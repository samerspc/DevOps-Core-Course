# Stage 1: Builder - Compile the application
FROM golang:1.21-alpine AS builder

# Set working directory
WORKDIR /build

# Install git (needed for some Go dependencies)
RUN apk add --no-cache git

# Copy go mod files
COPY go.mod go.sum* ./

# Download dependencies
RUN go mod download

# Copy source code
COPY main.go .

# Build static binary
# CGO_ENABLED=0: Disable CGO for static binary
# -ldflags '-w -s': Strip debug info to reduce size
# -a: Force rebuilding of packages
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags='-w -s' -a -installsuffix cgo -o app main.go

# Stage 2: Runtime - Minimal image with only the binary
FROM alpine:latest

# Create non-root user
RUN addgroup -g 1000 appuser && \
    adduser -D -u 1000 -G appuser appuser

# Set working directory
WORKDIR /app

# Copy binary from builder stage
COPY --from=builder /build/app .

# Change ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Set environment variables
ENV PORT=8080

# Health check (install wget for health check)
RUN apk add --no-cache wget
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/health || exit 1

# Run the application
CMD ["./app"]
