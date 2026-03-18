# Lab 01 Bonus Task - Go Implementation

## Overview

This document describes the Go implementation of the DevOps Info Service, completed as the bonus task for Lab 01. This compiled language version demonstrates the advantages of static compilation and prepares for multi-stage Docker builds in Lab 2.

## Implementation Details

### Project Structure

```
app_go/
├── main.go                 # Main application (single file)
├── go.mod                  # Go module definition
├── go.sum                  # Dependency checksums (auto-generated)
├── README.md               # User documentation
└── docs/
    ├── LAB01.md           # This file
    ├── GO.md              # Language justification
    └── screenshots/       # Proof of work
```

### Key Implementation Features

#### 1. Zero External Dependencies

The Go implementation uses only the standard library:
- `net/http` - HTTP server and routing
- `encoding/json` - JSON encoding/decoding
- `runtime` - System information (OS, architecture, CPU count, Go version)
- `os` - Hostname and environment variables
- `time` - Timestamps and uptime calculation
- `log` - Logging

**go.mod:**
```go
module devops-info-service

go 1.21
// No dependencies!
```

This is a significant advantage over Python, which requires Flask and other dependencies.

#### 2. Struct-Based JSON Response

Go's struct tags provide type-safe JSON encoding:

```go
type ServiceInfo struct {
    Service  ServiceInfoDetail `json:"service"`
    System   SystemInfo        `json:"system"`
    Runtime  RuntimeInfo       `json:"runtime"`
    Request  RequestInfo       `json:"request"`
    Endpoints []EndpointInfo   `json:"endpoints"`
}
```

Benefits:
- Compile-time type checking
- Automatic JSON marshaling
- Clear data structure

#### 3. Uptime Calculation

Similar to Python version, but using Go's `time` package:

```go
func getUptime() (int, string) {
    delta := time.Since(startTime)
    seconds := int(delta.Seconds())
    
    hours := seconds / 3600
    minutes := (seconds % 3600) / 60
    
    // Format human-readable string with proper pluralization
    // ...
    return seconds, uptimeHuman
}
```

#### 4. Error Handling

Go's explicit error handling:

```go
if err := json.NewEncoder(w).Encode(info); err != nil {
    log.Printf("Error encoding JSON: %v", err)
    http.Error(w, "Internal Server Error", http.StatusInternalServerError)
}
```

#### 5. Environment Configuration

```go
port := os.Getenv("PORT")
if port == "" {
    port = "8080"  // Default
}

host := os.Getenv("HOST")
if host == "" {
    host = "0.0.0.0"  // Default
}
```

## Build Process

### Development Build

```bash
# Simple build
go build -o devops-info-service main.go

# Build with verbose output
go build -v -o devops-info-service main.go
```

### Optimized Build (Production)

```bash
# Strip debug info and reduce size
go build -ldflags="-s -w" -o devops-info-service main.go

# Flags explanation:
# -s: Omit symbol table and debug information
# -w: Omit DWARF symbol table
```

### Cross-Platform Build

```bash
# Build for Linux (for Docker)
GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -o devops-info-service-linux main.go

# Build for Windows
GOOS=windows GOARCH=amd64 go build -ldflags="-s -w" -o devops-info-service.exe main.go

# Build for macOS ARM64 (Apple Silicon)
GOOS=darwin GOARCH=arm64 go build -ldflags="-s -w" -o devops-info-service-macos-arm64 main.go
```

### Static Binary (for minimal Docker images)

```bash
# Build fully static binary (Linux)
CGO_ENABLED=0 GOOS=linux go build -a -ldflags="-s -w -extldflags '-static'" -o devops-info-service-static main.go
```

## Binary Size Comparison

### Go Binary Sizes

```bash
# Check sizes
ls -lh devops-info-service*

# Typical results:
# Development build:        ~8-10 MB
# Optimized build (-s -w):  ~6-8 MB
# Static binary:            ~8-10 MB
```

**Example output:**
```
-rwxr-xr-x  1 user  staff   7.2M  devops-info-service
-rwxr-xr-x  1 user  staff   6.8M  devops-info-service-optimized
-rwxr-xr-x  1 user  staff   8.1M  devops-info-service-static
```

### Python Comparison

Python application requires:

1. **Python Interpreter:**
   - Python 3.13: ~30-50 MB
   - Standard library: ~20-30 MB

2. **Dependencies:**
   - Flask 3.1.0: ~2-3 MB
   - Werkzeug, Jinja2, etc.: ~5-10 MB

3. **Total Runtime:**
   - Minimum: ~50-80 MB
   - With full Python installation: ~100-150 MB

### Size Comparison Table

| Component | Go | Python |
|-----------|-----|--------|
| **Application Code** | 7.2 MB (binary) | ~50 KB (source) |
| **Runtime** | 0 MB (static) | ~50-80 MB (interpreter) |
| **Dependencies** | 0 MB (included) | ~10-20 MB (packages) |
| **Total** | **~7.2 MB** | **~60-100 MB** |
| **Container Image** | ~10-15 MB (scratch) | ~100-150 MB (python:3.13) |

### Advantages of Go Binary Size

1. **Faster Container Pulls:** Smaller images download faster
2. **Lower Storage Costs:** Less disk space required
3. **Faster Startup:** No interpreter initialization
4. **Better for Multi-Stage Builds:** Can use `FROM scratch` in Docker
5. **Lower Memory Footprint:** Single process, no interpreter overhead

## Running the Application

### From Source (Development)

```bash
go run main.go
```

### From Compiled Binary

```bash
./devops-info-service
```

### With Custom Configuration

```bash
# Custom port
PORT=5000 ./devops-info-service

# Custom host and port
HOST=127.0.0.1 PORT=3000 ./devops-info-service
```

## API Endpoints

### `GET /`

**Request:**
```bash
curl http://localhost:8080/
```

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
    "hostname": "MacBook-Air-samer",
    "platform": "darwin",
    "platform_version": "darwin amd64",
    "architecture": "amd64",
    "cpu_count": 8,
    "go_version": "go1.21.5"
  },
  "runtime": {
    "uptime_seconds": 120,
    "uptime_human": "2 minutes",
    "current_time": "2026-01-28T20:00:00.000000000Z",
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

**Request:**
```bash
curl http://localhost:8080/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T20:00:00.000000000Z",
  "uptime_seconds": 120
}
```

## Testing

### Manual Testing

```bash
# Start server
go run main.go

# Test main endpoint
curl http://localhost:8080/ | python3 -m json.tool

# Test health endpoint
curl http://localhost:8080/health | python3 -m json.tool

# Test 404
curl http://localhost:8080/nonexistent
```

### Automated Testing (Future)

```bash
# Run tests
go test ./...

# With coverage
go test -cover ./...
```

## Performance Characteristics

### Startup Time
- **Go:** < 10ms (instant)
- **Python:** 50-200ms (interpreter startup)

### Memory Usage
- **Go:** ~5-10 MB baseline
- **Python:** ~20-30 MB baseline

### Request Latency
- **Go:** < 1ms per request
- **Python:** 2-5ms per request (Flask)

## Challenges & Solutions

### Challenge 1: JSON Timestamp Format

**Problem:** Go's `time.RFC3339Nano` format differs slightly from Python's ISO format.

**Solution:** Used `time.RFC3339Nano` which is ISO 8601 compliant and provides nanosecond precision. Both formats are valid and parseable.

### Challenge 2: Client IP Extraction

**Problem:** Go's `http.Request.RemoteAddr` includes port number (e.g., "127.0.0.1:54321"), unlike Python's `request.remote_addr`.

**Solution:** Kept the port in the response for accuracy. In production, could parse and extract just the IP if needed.

### Challenge 3: Platform Version Format

**Problem:** Go's `runtime.GOOS` and `runtime.GOARCH` provide different format than Python's `platform.platform()`.

**Solution:** Combined `GOOS` and `GOARCH` to create a descriptive platform version string. This is actually more accurate for containerized deployments.

## Differences from Python Version

| Feature | Python | Go |
|---------|--------|-----|
| **Dependencies** | Flask 3.1.0 | None (stdlib only) |
| **Binary Size** | N/A (interpreted) | ~7 MB |
| **Startup Time** | 50-200ms | < 10ms |
| **Memory** | ~30 MB | ~8 MB |
| **Deployment** | Needs Python | Single binary |
| **Type Safety** | Runtime | Compile-time |

## Future Enhancements (For Later Labs)

1. **Lab 2 - Docker:** Multi-stage build with `FROM scratch` for minimal image
2. **Lab 3 - CI/CD:** Fast compilation speeds up pipeline
3. **Lab 8 - Metrics:** Add Prometheus metrics endpoint
4. **Lab 9 - Kubernetes:** Smaller images = faster pod startup

## Conclusion

The Go implementation successfully demonstrates:

✅ **Same functionality** as Python version  
✅ **Smaller footprint** (~7 MB vs ~60-100 MB)  
✅ **Faster startup** (< 10ms vs 50-200ms)  
✅ **No dependencies** (stdlib only)  
✅ **Single binary** deployment  
✅ **Cross-platform** compilation  

This implementation provides an excellent foundation for containerization and Kubernetes deployment in future labs, showcasing the advantages of compiled languages for DevOps tooling.
