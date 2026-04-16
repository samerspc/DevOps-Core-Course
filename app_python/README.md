# DevOps Info Service

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

# Lab 12: visit counter file (default /data/visits)
VISITS_FILE=/tmp/visits python app.py
```

## API Endpoints

### `GET /`
Returns comprehensive service and system information. **Each request increments a persisted visit counter** (Lab 12); the current total is included in `visits.total`.

**Response (illustrative):**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Flask",
    "environment": "dev"
  },
  "system": { "...": "..." },
  "runtime": { "...": "..." },
  "request": { "...": "..." },
  "visits": { "total": 42 },
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Service information"},
    {"path": "/visits", "method": "GET", "description": "Visit counter"},
    {"path": "/health", "method": "GET", "description": "Health check"}
  ]
}
```

### `GET /visits`
Returns the current visit count (read from `VISITS_FILE` without incrementing) and a small `config` summary (from `APP_CONFIG_PATH` JSON and env vars such as `APP_ENV` / `LOG_LEVEL` when set).

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
curl http://localhost:5000/visits
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

### Docker Compose (Lab 12 — persistent visits + optional config)

From `app_python/`, a volume keeps the counter across restarts; `sample-config/` is mounted read-only at `/config`:

```bash
docker compose up --build
# Map is host 5001 → container 5000 (avoids macOS AirPlay / conflict on 5000)
curl -s http://localhost:5001/visits
docker compose restart
curl -s http://localhost:5001/visits
```

### Running a Container

Run the containerized application with port mapping:

```bash
docker run -d -p 5000:5000 --name devops-app devops-info-service:latest
```

Persist visits on the host:

```bash
mkdir -p data
docker run -d -p 5000:5000 -v "$(pwd)/data:/data" -e VISITS_FILE=/data/visits --name devops-app devops-info-service:latest
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
| `VISITS_FILE` | `/data/visits` | Path to the visit counter file (Lab 12) |
| `APP_CONFIG_PATH` | `/config/config.json` | Optional JSON config (Kubernetes ConfigMap mount) |

## Development

### Project Structure
```
app_python/
├── app.py                    # Main application
├── docker-compose.yml        # Lab 12 local persistence demo
├── sample-config/config.json # Example mounted config for compose
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
