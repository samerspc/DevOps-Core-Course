# DevOps Info Service

[![Python CI](https://github.com/samerspc/DevOps-Core-Course/workflows/Python%20CI/badge.svg)](https://github.com/samerspc/DevOps-Core-Course/actions/workflows/python-ci.yml)

A web application providing detailed information about itself and its runtime environment.

## Overview

DevOps Info Service is a RESTful API service that reports comprehensive system information, runtime statistics, and health status. This service serves as the foundation for future DevOps tooling and monitoring capabilities.

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
```bash
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Default Configuration
```bash
python app.py
```
The service will start on `http://0.0.0.0:5000`

### Custom Configuration
You can configure the application using environment variables:

```bash
# Custom port
PORT=8080 python app.py

# Custom host and port
HOST=127.0.0.1 PORT=3000 python app.py

# Enable debug mode
DEBUG=true python app.py
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
    "framework": "Flask"
  },
  "system": {
    "hostname": "my-laptop",
    "platform": "Linux",
    "platform_version": "Ubuntu 24.04",
    "architecture": "x86_64",
    "cpu_count": 8,
    "python_version": "3.13.1"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hour, 0 minutes",
    "current_time": "2026-01-07T14:30:00.000Z",
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

### `GET /health`
Returns health status for monitoring purposes.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:30:00.000Z",
  "uptime_seconds": 3600
}
```

**Example Usage:**
```bash
# Using curl
curl http://localhost:5000/
curl http://localhost:5000/health

# Using HTTPie
http GET http://localhost:5000/
http GET http://localhost:5000/health
```

## Docker

The application is containerized using Docker and published to Docker Hub.

### Building the Image Locally

Build the Docker image from the Dockerfile:

```bash
docker build -t devops-info-service:latest .
```

### Running a Container

Run the containerized application with port mapping:

```bash
docker run -d -p 5000:5000 --name devops-app devops-info-service:latest
```

Access the application at `http://localhost:5000`

### Pulling from Docker Hub

Pull the pre-built image from Docker Hub:

```bash
docker pull samerdockerhup/devops-info-service:latest
docker run -d -p 5000:5000 --name devops-app samerdockerhup/devops-info-service:latest
```

**Docker Hub Repository:** https://hub.docker.com/r/samerdockerhup/devops-info-service

### Container Configuration

You can override environment variables when running the container:

```bash
# Custom port
docker run -d -p 8080:8080 -e PORT=8080 --name devops-app devops-info-service:latest

# Custom host and port
docker run -d -p 3000:3000 -e HOST=0.0.0.0 -e PORT=3000 --name devops-app devops-info-service:latest
```

## Configuration

The application can be configured using the following environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Host address to bind the server |
| `PORT` | `5000` | Port number to listen on |
| `DEBUG` | `False` | Enable debug mode (set to `true` to enable) |

## Testing

Run unit tests locally:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Run with coverage (optional)
pytest tests/ --cov=. --cov-report=term
```

## Development

### Project Structure
```
app_python/
├── app.py                    # Main application
├── requirements.txt          # Dependencies
├── .gitignore               # Git ignore rules
├── README.md                # This file
├── tests/                   # Unit tests
│   └── __init__.py
└── docs/                    # Documentation
    ├── LAB01.md            # Lab submission
    └── screenshots/        # Proof of work
```

## License

This project is part of the DevOps Core Course.
