"""
DevOps Info Service
Main application module
"""
import os
import socket
import platform
import logging
from datetime import datetime, timezone
from time import monotonic

from flask import Flask, jsonify, request, g, Response
from pythonjsonlogger import jsonlogger
from prometheus_client import Counter, Gauge, Histogram, generate_latest

# Configure JSON logging
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    '%(timestamp)s %(level)s %(name)s %(message)s',
    timestamp=True
)
logHandler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Prevent duplicate logs
logger.propagate = False

# Initialize Flask app
app = Flask(__name__)

# Configuration from environment variables
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# ─── Prometheus metrics (Lab 8) ──────────────────────────────────────────────
# Keep label cardinality low: endpoint is the route path (this app has only a
# few static endpoints).
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code'],
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
)

# Number of HTTP requests currently being processed.
http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests currently being processed',
)


@app.route('/metrics')
def metrics():
    # Expose Prometheus metrics in the default text format.
    return Response(
        generate_latest(),
        mimetype='text/plain; version=0.0.4; charset=utf-8',
    )

# Request logging middleware
@app.before_request
def log_request():
    """Log incoming HTTP requests."""
    g.start_time = datetime.now(timezone.utc)
    g.start_time_monotonic = monotonic()
    # Ensure the gauge is decremented even if the request handler errors.
    g.inprogress_cm = http_requests_in_progress.track_inprogress()
    g.inprogress_cm.__enter__()
    logger.info('Incoming request', extra={
        'event': 'http_request',
        'method': request.method,
        'path': request.path,
        'client_ip': request.remote_addr or 'unknown',
        'user_agent': request.headers.get('User-Agent', 'unknown')
    })

@app.after_request
def log_response(response):
    """Log HTTP responses."""
    if hasattr(g, 'start_time'):
        duration_ms = (datetime.now(timezone.utc) - g.start_time).total_seconds() * 1000
    else:
        duration_ms = 0

    # Record Prometheus metrics for every response (success or error).
    endpoint = request.path or 'unknown'
    method = request.method or 'unknown'
    status_code = str(getattr(response, 'status_code', 0))

    http_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status_code=status_code,
    ).inc()

    if hasattr(g, 'start_time_monotonic'):
        duration_seconds = monotonic() - g.start_time_monotonic
    else:
        duration_seconds = duration_ms / 1000.0

    http_request_duration_seconds.labels(
        method=method,
        endpoint=endpoint,
    ).observe(duration_seconds)

    # Stop tracking in-progress requests.
    if hasattr(g, 'inprogress_cm'):
        g.inprogress_cm.__exit__(None, None, None)

    logger.info('HTTP response', extra={
        'event': 'http_response',
        'method': request.method,
        'path': request.path,
        'status_code': response.status_code,
        'duration_ms': round(duration_ms, 2),
        'client_ip': request.remote_addr or 'unknown'
    })
    
    return response

# Application start time (for uptime calculation)
START_TIME = datetime.now(timezone.utc)

# Log application startup
logger.info('Application starting', extra={
    'event': 'app_startup',
    'host': os.getenv('HOST', '0.0.0.0'),
    'port': int(os.getenv('PORT', 5000)),
    'debug': os.getenv('DEBUG', 'False').lower() == 'true'
})


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


def get_request_info():
    """Extract request information."""
    return {
        'client_ip': request.remote_addr or 'unknown',
        'user_agent': request.headers.get('User-Agent', 'unknown'),
        'method': request.method,
        'path': request.path
    }


@app.route('/')
def index():
    """Main endpoint - service and system information."""
    uptime = get_uptime()
    
    response = {
        'service': {
            'name': 'devops-info-service',
            'version': '1.0.0',
            'description': 'DevOps course info service',
            'framework': 'Flask'
        },
        'system': get_system_info(),
        'runtime': {
            'uptime_seconds': uptime['seconds'],
            'uptime_human': uptime['human'],
            'current_time': datetime.now(timezone.utc).isoformat(),
            'timezone': 'UTC'
        },
        'request': get_request_info(),
        'endpoints': [
            {'path': '/', 'method': 'GET', 'description': 'Service information'},
            {'path': '/health', 'method': 'GET', 'description': 'Health check'}
        ]
    }
    
    return jsonify(response)


@app.route('/health')
def health():
    """Health check endpoint for monitoring."""
    uptime = get_uptime()
    
    logger.debug('Health check requested', extra={
        'event': 'health_check',
        'uptime_seconds': uptime['seconds']
    })
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': uptime['seconds']
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    logger.warning('Endpoint not found', extra={
        'event': 'http_error',
        'error_code': 404,
        'path': request.path,
        'method': request.method
    })
    return jsonify({
        'error': 'Not Found',
        'message': 'Endpoint does not exist'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error('Internal server error', extra={
        'event': 'http_error',
        'error_code': 500,
        'error_type': type(error).__name__,
        'error_message': str(error),
        'path': request.path,
        'method': request.method
    })
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500


if __name__ == '__main__':
    logger.info('DevOps Info Service started', extra={
        'event': 'app_ready',
        'host': HOST,
        'port': PORT,
        'debug': DEBUG
    })
    app.run(host=HOST, port=PORT, debug=DEBUG)
