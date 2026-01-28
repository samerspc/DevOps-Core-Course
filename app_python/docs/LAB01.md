# Lab 01 Submission - DevOps Info Service

## Framework Selection

### Choice: Flask 3.1.0

I selected **Flask** as the web framework for this project. Below is a detailed comparison and justification.

### Comparison Table

| Framework | Pros | Cons | Use Case |
|-----------|------|------|----------|
| **Flask** | • Lightweight and minimal<br>• Easy to learn<br>• Flexible and extensible<br>• Large ecosystem<br>• Simple for small APIs | • More manual setup needed<br>• No built-in async support | Small to medium APIs, microservices |
| **FastAPI** | • Modern async support<br>• Auto-generated docs<br>• Type hints validation<br>• High performance | • Steeper learning curve<br>• More dependencies | High-performance APIs, modern async apps |
| **Django** | • Full-featured framework<br>• Built-in ORM<br>• Admin panel<br>• Security features | • Heavy for simple APIs<br>• Opinionated structure<br>• More complex | Full web applications, complex projects |

### Justification

I chose **Flask** for the following reasons:

1. **Simplicity**: For a straightforward REST API with only two endpoints, Flask provides the perfect balance of functionality without unnecessary complexity.

2. **Learning Curve**: As a beginner-friendly framework, Flask allows focusing on core DevOps concepts rather than framework-specific features.

3. **Flexibility**: Flask's minimal core with extensible architecture means we can add features (like async support via Flask 2.0+ or extensions) as needed in future labs.

4. **Industry Standard**: Flask is widely used in production environments and is well-documented, making it a practical choice for real-world DevOps scenarios.

5. **Resource Efficiency**: Lightweight nature makes it ideal for containerized deployments (Lab 2) and Kubernetes (Lab 9).

6. **Ecosystem**: Rich ecosystem of extensions (Flask-RESTful, Flask-CORS, etc.) provides flexibility for future enhancements.

While FastAPI offers modern features like async and auto-documentation, Flask's simplicity and maturity make it the better choice for this foundational service that will evolve throughout the course.

---

## Best Practices Applied

### 1. Clean Code Organization

**Implementation:**
- Clear function names following Python naming conventions
- Proper imports grouping (standard library, third-party, local)
- Docstrings for all functions
- Logical code structure with separation of concerns

**Code Example:**
```python
def get_system_info():
    """Collect system information."""
    return {
        'hostname': socket.gethostname(),
        'platform': platform.system(),
        'platform_version': platform.platform(),
        'architecture': platform.machine(),
        'cpu_count': os.cpu_count() or 1,
        'python_version': platform.python_version()
    }
```

**Importance:** Clean organization improves maintainability, readability, and makes it easier for team members to understand and contribute to the codebase.

### 2. Error Handling

**Implementation:**
- Custom error handlers for 404 (Not Found) and 500 (Internal Server Error)
- JSON-formatted error responses for API consistency
- Proper HTTP status codes

**Code Example:**
```python
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'error': 'Not Found',
        'message': 'Endpoint does not exist'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f'Internal server error: {error}')
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500
```

**Importance:** Proper error handling provides better user experience, helps with debugging, and ensures the API returns consistent error formats that can be consumed by monitoring tools and clients.

### 3. Logging

**Implementation:**
- Configured logging with appropriate format
- INFO level for general application events
- ERROR level for exceptions
- Request logging for debugging

**Code Example:**
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info('Starting DevOps Info Service...')
logger.info(f'Request: {request.method} {request.path} from {request.remote_addr}')
```

**Importance:** Logging is crucial for production applications. It helps with debugging, monitoring application health, tracking user requests, and diagnosing issues in deployed environments. This will be especially important when deploying to Kubernetes in Lab 9.

### 4. Configuration via Environment Variables

**Implementation:**
- All configuration externalized to environment variables
- Sensible defaults provided
- Easy to configure for different environments

**Code Example:**
```python
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
```

**Importance:** Environment-based configuration is essential for DevOps practices. It allows the same code to run in different environments (development, staging, production) without code changes. This aligns with 12-factor app principles and is crucial for containerization (Lab 2) and Kubernetes deployments (Lab 9).

### 5. PEP 8 Compliance

**Implementation:**
- Function and variable names follow snake_case convention
- Proper spacing and indentation
- Line length considerations
- Import organization

**Importance:** PEP 8 compliance ensures code consistency, improves readability, and makes collaboration easier. It's the standard for Python development and is expected in professional environments.

### 6. Dependency Management

**Implementation:**
- Pinned exact versions in `requirements.txt`
- Minimal dependencies (only Flask)

**Code Example:**
```txt
Flask==3.1.0
```

**Importance:** Pinning exact versions ensures reproducible builds across different environments and team members. This prevents "works on my machine" issues and is critical for CI/CD pipelines (Lab 3) and containerization (Lab 2).

### 7. Git Ignore

**Implementation:**
- Comprehensive `.gitignore` covering Python artifacts, virtual environments, IDE files, and OS-specific files

**Importance:** Prevents committing unnecessary files to version control, keeps the repository clean, and avoids exposing sensitive information or build artifacts.

---

## API Documentation

### Endpoint: `GET /`

**Description:** Returns comprehensive service and system information.

**Request:**
```bash
curl http://localhost:5000/
```

**Response (200 OK):**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Flask"
  },
  "system": {
    "hostname": "MacBook-Air-samer",
    "platform": "Darwin",
    "platform_version": "Darwin-23.6.0-x86_64-i386-64bit",
    "architecture": "x86_64",
    "cpu_count": 8,
    "python_version": "3.13.1"
  },
  "runtime": {
    "uptime_seconds": 120,
    "uptime_human": "2 minutes",
    "current_time": "2026-01-28T19:15:00.000000+00:00",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
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

### Endpoint: `GET /health`

**Description:** Returns health status for monitoring and Kubernetes probes.

**Request:**
```bash
curl http://localhost:5000/health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-28T19:15:00.000000+00:00",
  "uptime_seconds": 120
}
```

### Testing Commands

**Using curl:**
```bash
# Main endpoint
curl http://localhost:5000/

# Health check
curl http://localhost:5000/health

# Pretty-printed JSON (requires jq)
curl -s http://localhost:5000/ | jq
```

**Using HTTPie:**
```bash
# Main endpoint
http GET http://localhost:5000/

# Health check
http GET http://localhost:5000/health
```

**Using Python requests:**
```python
import requests

# Main endpoint
response = requests.get('http://localhost:5000/')
print(response.json())

# Health check
response = requests.get('http://localhost:5000/health')
print(response.json())
```

---

## Testing Evidence

### Screenshots

Screenshots demonstrating the working endpoints are located in `docs/screenshots/`:

1. **01-main-endpoint.png** - Shows the complete JSON response from `GET /`
2. **02-health-check.png** - Shows the health check endpoint response
3. **03-formatted-output.png** - Shows pretty-printed JSON output using `jq`

### Terminal Output

**Starting the application:**
```
2026-01-28 19:14:44,835 - __main__ - INFO - Starting DevOps Info Service...
2026-01-28 19:14:44,835 - __main__ - INFO - Listening on 0.0.0.0:5000
 * Serving Flask app 'app'
 * Debug mode: off
 * Running on http://0.0.0.0:5000
```

**Testing main endpoint:**
```bash
$ curl http://localhost:5000/
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    ...
  }
}
```

**Testing health endpoint:**
```bash
$ curl http://localhost:5000/health
{
  "status": "healthy",
  "timestamp": "2026-01-28T19:15:00.000000+00:00",
  "uptime_seconds": 120
}
```

---

## Challenges & Solutions

### Challenge 1: Port 5000 Already in Use

**Problem:** On macOS, port 5000 is often occupied by AirPlay Receiver service, causing the application to fail to start.

**Solution:** 
- Used environment variable to run on a different port: `PORT=8080 python app.py`
- Documented this in the README as a common macOS issue
- Alternative solution: Disable AirPlay Receiver in System Settings

**Learning:** Environment-based configuration proved essential for handling platform-specific issues.

### Challenge 2: Uptime Human-Readable Format

**Problem:** Converting seconds to a human-readable format (e.g., "1 hour, 30 minutes") required careful handling of edge cases (singular/plural, zero values, etc.).

**Solution:** 
- Implemented a function that handles hours, minutes, and seconds separately
- Added proper pluralization logic
- Handled edge case when uptime is less than 60 seconds

**Code:**
```python
def get_uptime():
    """Calculate application uptime."""
    delta = datetime.now(timezone.utc) - START_TIME
    seconds = int(delta.total_seconds())
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    uptime_human = ""
    if hours > 0:
        uptime_human += f"{hours} hour{'s' if hours != 1 else ''}"
    if minutes > 0:
        if uptime_human:
            uptime_human += ", "
        uptime_human += f"{minutes} minute{'s' if minutes != 1 else ''}"
    if seconds < 60:
        uptime_human = f"{secs} second{'s' if secs != 1 else ''}"
    
    return {
        'seconds': seconds,
        'human': uptime_human if uptime_human else "0 seconds"
    }
```

**Learning:** Paying attention to edge cases and user experience details (like proper pluralization) improves API quality.

### Challenge 3: Platform Version Information

**Problem:** The lab specification requested `platform_version` like "Ubuntu 24.04", but `platform.platform()` returns detailed system information that may not match the expected format.

**Solution:** 
- Used `platform.platform()` which provides comprehensive platform information
- This gives more detailed information than just the OS version
- For production, could be enhanced with platform-specific detection

**Learning:** Sometimes the standard library provides more information than needed, but it's better to be comprehensive than to miss important details.

---

## GitHub Community

### Why Starring Repositories Matters

Starring repositories in open source serves multiple important purposes. First, it acts as a bookmarking mechanism, allowing developers to save interesting projects for future reference. More importantly, stars signal community appreciation and project quality, which encourages maintainers and attracts new contributors. High star counts also improve project visibility in GitHub's search and recommendation algorithms, helping valuable projects gain traction. From a professional perspective, the repositories you star reflect your interests and awareness of industry tools, which can be valuable for networking and career growth.

### How Following Developers Helps

Following developers on GitHub is essential for both team collaboration and professional development. In team projects, following teammates keeps you updated on their work, making collaboration smoother and helping you discover new approaches to problem-solving. For professional growth, following experienced developers and thought leaders exposes you to best practices, trending technologies, and real-world solutions. This continuous learning helps you stay current with industry trends and build a network of connections that can lead to future opportunities. Additionally, your GitHub activity profile, including who you follow, demonstrates your engagement with the developer community to potential employers.

---

## Conclusion

This lab successfully implemented a production-ready DevOps Info Service using Flask. The service provides comprehensive system information and health monitoring capabilities, following Python best practices and DevOps principles. The foundation established here will support future enhancements including containerization, CI/CD pipelines, and Kubernetes deployment.

**Key Achievements:**
- ✅ Clean, maintainable code following PEP 8
- ✅ Comprehensive error handling and logging
- ✅ Environment-based configuration
- ✅ Complete API documentation
- ✅ Production-ready structure

**Next Steps (Future Labs):**
- Lab 2: Containerize with Docker
- Lab 3: Add unit tests and CI/CD
- Lab 8: Add Prometheus metrics endpoint
- Lab 9: Deploy to Kubernetes
