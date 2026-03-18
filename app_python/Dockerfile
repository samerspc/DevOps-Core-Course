# Multi-stage build is not required for Python, but we use best practices
# Base image with specific version for reproducibility
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Create non-root user for security (MANDATORY requirement)
# This prevents running as root, reducing security risks
RUN groupadd -r appuser && \
    useradd -r -g appuser appuser

# Install system dependencies if needed (optimize layer caching)
# Copy requirements first to leverage Docker layer caching
# This way, if dependencies don't change, Docker reuses this layer
COPY requirements.txt .

# Install Python dependencies
# Use --no-cache-dir to reduce image size
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code (after dependencies for better caching)
# Only copy necessary files (use .dockerignore to exclude others)
COPY app.py .

# Create directory for app data if needed and set ownership
RUN mkdir -p /app/data && \
    chown -R appuser:appuser /app

# Switch to non-root user (MANDATORY)
USER appuser

# Expose the port the app runs on
# Document which port is used (default 5000 for Flask)
EXPOSE 5000

# Set environment variables with defaults
ENV HOST=0.0.0.0 \
    PORT=5000 \
    PYTHONUNBUFFERED=1

# Health check for container orchestration
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Run the application
# Use exec form for better signal handling
CMD ["python", "app.py"]
