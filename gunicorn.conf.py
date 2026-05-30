# -----------------------------------------------------------------------------
# GUNICORN PRODUCTION CONFIGURATION FILE
# -----------------------------------------------------------------------------
# For more info see: https://docs.gunicorn.org/en/stable/configure.html
# -----------------------------------------------------------------------------

import multiprocessing
import os

# Server Socket Settings
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")
backlog = int(os.getenv("GUNICORN_BACKLOG", "2048"))

# Worker Process Configurations
# In production, worker count is typically set to (2 * CPU Cores) + 1
default_worker_count = (multiprocessing.cpu_count() * 2) + 1
workers = int(os.getenv("GUNICORN_WORKERS", str(default_worker_count)))
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "gthread")

# Threads per worker process (efficient for handling I/O bound DB operations)
threads = int(os.getenv("GUNICORN_THREADS", "2"))
worker_connections = int(os.getenv("GUNICORN_WORKER_CONNECTIONS", "1000"))

# Life Cycle Parameters
timeout = int(os.getenv("GUNICORN_TIMEOUT", "60"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "2"))
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "2000"))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "200"))

# Debugging and Core
reload = os.getenv("GUNICORN_RELOAD", "False").lower() in ("true", "1", "yes")

# Logging Configuration
# Send access logs and error logs directly to stdout/stderr for Docker aggregation
accesslog = os.getenv("GUNICORN_ACCESS_LOG", "-")
errorlog = os.getenv("GUNICORN_ERROR_LOG", "-")
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")

# Process Naming
proc_name = "baltim_backend_gunicorn"
