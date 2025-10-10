"""
Gunicorn configuration file
"""

# Server socket
bind = "0.0.0.0:3000"
workers = 1  # Single worker for SimpleCache to work correctly

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Worker process
worker_class = "sync"
timeout = 120

# Application
def on_starting(server):
    """Called just before the master process is initialized."""
    print("Gunicorn is starting...")

def when_ready(server):
    """Called just after the server is started."""
    print("Gunicorn server is ready. Warming up cache...")
    # Import app and run warmup
    from app import app, init_app
    init_app()
    print("Cache warmup complete. Server ready to accept connections.")
