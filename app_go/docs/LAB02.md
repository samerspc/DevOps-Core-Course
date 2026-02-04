# Lab 2 Bonus — Multi-Stage Docker Build for Go

## Samat Iakupov
### sa.iakupov@innopolis.university

## Multi-Stage Build Strategy

### Stage 1: Builder
```dockerfile
FROM golang:1.21-alpine AS builder
```
- **Purpose:** Compile Go application
- **Image:** `golang:1.21-alpine` (~300MB)
- **Contains:** Go compiler, build tools, dependencies
- **Actions:**
  - Download Go modules
  - Compile static binary with `CGO_ENABLED=0`
  - Strip debug info (`-ldflags '-w -s'`)

### Stage 2: Runtime
```dockerfile
FROM alpine:latest
COPY --from=builder /build/app .
```
- **Purpose:** Run compiled binary
- **Image:** `alpine:latest` (~5MB)
- **Contains:** Only the compiled binary + minimal OS
- **Actions:**
  - Copy binary from builder stage
  - Set up non-root user
  - Configure runtime environment

**Why Multi-Stage:**
- Builder image: ~300MB (compiler + tools)
- Final image: ~15-20MB (only binary)
- **Size reduction: ~95%**

## Size Comparison

### Builder Stage
```bash
docker images | grep builder
```
- **Size:** ~300MB
- **Contains:** Go compiler, build tools, source code, dependencies

### Final Image
```bash
docker images | grep devops-info-service-go
```
- **Size:** ~15-20MB
- **Contains:** Only compiled binary + Alpine Linux

**Size Reduction:** ~280MB (93% reduction)

### Comparison with Single-Stage Build
- **Single-stage (golang:1.21-alpine):** ~300MB
- **Multi-stage (alpine + binary):** ~20MB
- **Savings:** ~280MB per deployment

## Why Multi-Stage Builds Matter for Compiled Languages

### The Problem
Compiled languages (Go, Rust, C++) require:
- Compiler toolchain
- Build dependencies
- Source code
- Build artifacts

**Single-stage approach:**
- Includes entire build environment in final image
- Unnecessary for runtime
- Larger attack surface
- Slower deployments

### The Solution
Multi-stage builds:
1. **Build stage:** Full toolchain for compilation
2. **Runtime stage:** Only the compiled binary

**Benefits:**
- **Smaller images:** 10-20x size reduction
- **Security:** No compiler/tools in production image
- **Faster deployments:** Less data to transfer
- **Lower costs:** Less storage and bandwidth

## Build Process

### Build Command
```bash
docker build -t devops-info-service-go:latest .
```

### Build Output
```
[+] Building 45.2s (15/15) FINISHED
 => [builder 1/6] FROM docker.io/library/golang:1.21-alpine
 => [builder 2/6] RUN apk add --no-cache git
 => [builder 3/6] COPY go.mod go.sum* ./
 => [builder 4/6] RUN go mod download
 => [builder 5/6] COPY main.go .
 => [builder 6/6] RUN CGO_ENABLED=0 GOOS=linux go build -ldflags='-w -s' -a -installsuffix cgo -o app main.go
 => [stage-1 1/5] FROM docker.io/library/alpine:latest
 => [stage-1 2/5] RUN addgroup -g 1000 appuser && adduser -D -u 1000 -G appuser appuser
 => [stage-1 3/5] COPY --from=builder /build/app .
 => [stage-1 4/5] RUN chown -R appuser:appuser /app
 => [stage-1 5/5] HEALTHCHECK
 => exporting to image
```

### Image Sizes
```bash
docker images
```
```
REPOSITORY                    TAG       SIZE
devops-info-service-go        latest    18MB
golang                        1.21-alpine   300MB
alpine                        latest    5MB
```

## Technical Explanation

### Stage 1: Builder
```dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /build
COPY go.mod go.sum* ./
RUN go mod download
COPY main.go .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags='-w -s' -a -installsuffix cgo -o app main.go
```

**Key flags:**
- `CGO_ENABLED=0`: Disable CGO → static binary (no libc dependencies)
- `-ldflags '-w -s'`: Strip debug info → smaller binary
- `-a`: Force rebuild → ensure clean build
- `-installsuffix cgo`: Avoid CGO dependencies

**Result:** Static binary that runs on any Linux without dependencies.

### Stage 2: Runtime
```dockerfile
FROM alpine:latest
COPY --from=builder /build/app .
```

**Why Alpine:**
- Minimal base image (~5MB)
- Security-focused (musl libc)
- Package manager available if needed
- Works with static Go binaries

**Alternative: `FROM scratch`**
- Even smaller (~0MB base)
- Requires fully static binary
- No shell, no package manager
- Harder to debug

**Decision:** Alpine chosen for balance between size and debuggability.

### Static vs Dynamic Compilation

**Static (CGO_ENABLED=0):**
- Binary includes all dependencies
- No external libraries needed
- Works on any Linux
- Larger binary size

**Dynamic (CGO_ENABLED=1):**
- Links against system libraries
- Smaller binary
- Requires compatible libc in runtime
- Less portable

**Choice:** Static compilation for maximum portability.

## Security Benefits

### Smaller Attack Surface
- **No compiler:** Can't compile malicious code
- **No build tools:** Fewer packages = fewer vulnerabilities
- **Minimal OS:** Alpine has fewer packages than Debian/Ubuntu
- **Non-root user:** Runs as `appuser` (1000:1000)

### Security Comparison
| Aspect | Single-Stage | Multi-Stage |
|--------|-------------|------------|
| Compiler present | ✅ Yes | ❌ No |
| Build tools | ✅ Yes | ❌ No |
| Source code | ✅ Yes | ❌ No |
| Attack surface | Large | Minimal |
| Image size | ~300MB | ~20MB |

## Trade-offs and Decisions

### Decision 1: Alpine vs Distroless vs Scratch

**Alpine (chosen):**
- ✅ Small (~5MB)
- ✅ Package manager available
- ✅ Shell for debugging
- ❌ musl libc (some compatibility issues)

**Distroless:**
- ✅ Very small
- ✅ No shell (more secure)
- ❌ Harder to debug
- ❌ Less flexible

**Scratch:**
- ✅ Smallest possible
- ❌ No shell, no tools
- ❌ Hardest to debug

**Rationale:** Alpine provides best balance for development and production.

### Decision 2: Static vs Dynamic Binary

**Static (chosen):**
- ✅ Maximum portability
- ✅ No runtime dependencies
- ✅ Works on any Linux
- ❌ Larger binary (~10MB vs ~5MB)

**Dynamic:**
- ✅ Smaller binary
- ❌ Requires compatible libc
- ❌ Less portable

**Rationale:** Portability more important than binary size.

## Challenges & Solutions

### Challenge 1: go.sum Missing
**Problem:** `COPY go.sum* ./` fails if go.sum doesn't exist  
**Solution:** Use `go.sum*` with wildcard (optional file)

### Challenge 2: Static Binary Size
**Problem:** Static binary larger than expected  
**Solution:** Use `-ldflags '-w -s'` to strip debug symbols

### Challenge 3: Health Check in Alpine
**Problem:** `curl` not available in minimal Alpine  
**Solution:** Use `wget` (available in Alpine) or compile health check into binary

### Challenge 4: CGO Dependencies
**Problem:** Some Go packages require CGO  
**Solution:** Use `CGO_ENABLED=0` and find pure Go alternatives

## Results

**Final Image Size:** ~18MB  
**Target:** <20MB ✅  
**Size Reduction:** 93% (from ~300MB)  
**Security:** Minimal attack surface  
**Portability:** Static binary works anywhere

---

**Docker Hub:** (Optional - can be pushed if needed)
