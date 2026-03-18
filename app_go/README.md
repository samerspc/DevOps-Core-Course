# DevOps Info Service (Go)

A web application providing detailed information about itself and its runtime environment, implemented in Go.

## Overview

This is the Go implementation of the DevOps Info Service - a RESTful API service that reports comprehensive system information, runtime statistics, and health status. This compiled language version demonstrates the benefits of static compilation and prepares for multi-stage Docker builds in Lab 2.

## Prerequisites

- Go 1.21 or higher
- Go modules enabled (default in Go 1.16+)

## Installation

1. Clone or navigate to the project directory:
```bash
cd app_go
```

2. Install dependencies (if any):
```bash
go mod download
```

## Building the Application

### Development Build
```bash
go build -o devops-info-service main.go
```

### Production Build (Optimized)
```bash
go build -ldflags="-s -w" -o devops-info-service main.go
```

The `-ldflags="-s -w"` flags strip debug information and reduce binary size:
- `-s`: Omit symbol table and debug information
- `-w`: Omit DWARF symbol table

### Cross-Platform Build
```bash
# Build for Linux
GOOS=linux GOARCH=amd64 go build -o devops-info-service-linux main.go

# Build for Windows
GOOS=windows GOARCH=amd64 go build -o devops-info-service.exe main.go

# Build for macOS (ARM64)
GOOS=darwin GOARCH=arm64 go build -o devops-info-service-macos-arm64 main.go
```

## Running the Application

### Run from Source (Development)
```bash
go run main.go
```

### Run Compiled Binary
```bash
./devops-info-service
```

The service will start on `http://0.0.0.0:8080` by default.

### Custom Configuration
You can configure the application using environment variables:

```bash
# Custom port
PORT=5000 go run main.go

# Custom host and port
HOST=127.0.0.1 PORT=3000 go run main.go

# Using compiled binary
HOST=0.0.0.0 PORT=8080 ./devops-info-service
```

## API Endpoints

### `GET /`
Returns comprehensive service and system information.

**Response:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Go"
  },
  "system": {
    "hostname": "my-laptop",
    "platform": "linux",
    "platform_version": "linux amd64",
    "architecture": "amd64",
    "cpu_count": 8,
    "go_version": "go1.21.0"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hour, 0 minutes",
    "current_time": "2026-01-28T19:30:00.000000000Z",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1:54321",
    "user_agent": "curl/7.81.0",
    "method": "GET",
    "path": "/"
  },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

### `GET /health`
Returns health status for monitoring purposes.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T19:30:00.000000000Z",
  "uptime_seconds": 3600
}
```

**Example Usage:**
```bash
# Using curl
curl http://localhost:8080/
curl http://localhost:8080/health

# Using HTTPie
http GET http://localhost:8080/
http GET http://localhost:8080/health
```

## Configuration

The application can be configured using the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host address to bind the server |
| `PORT` | `8080` | Port number to listen on |

## Binary Size Comparison

### Go Binary
```bash
# Check binary size
ls -lh devops-info-service

# Typical sizes:
# - Development build: ~8-10 MB
# - Optimized build (-ldflags="-s -w"): ~6-8 MB
# - Static binary: ~8-10 MB
```

### Python Comparison
- Python application requires:
  - Python interpreter: ~30-50 MB
  - Flask library: ~2-3 MB
  - Total runtime dependencies: ~50-100 MB

**Advantages of Go:**
- Single statically-linked binary
- No runtime dependencies
- Smaller container images
- Faster startup time
- Better for multi-stage Docker builds

## Development

### Project Structure
```
app_go/
├── main.go                 # Main application
├── go.mod                  # Go module definition
├── go.sum                  # Dependency checksums (auto-generated)
├── README.md               # This file
└── docs/                   # Documentation
    ├── LAB01.md           # Lab submission
    ├── GO.md              # Language justification
    └── screenshots/       # Proof of work
```

### Running Tests
```bash
go test ./...
```

### Code Formatting
```bash
go fmt ./...
```

### Linting
```bash
# Install golangci-lint
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

# Run linter
golangci-lint run
```

## License

This project is part of the DevOps Core Course.
