"""
Gunicorn Configuration for Production
Supports both primary (port 5000) and backup (port 5001) servers
"""
import os
import multiprocessing

# Server socket binding
port = os.environ.get('PORT', '5000')
bind = f"0.0.0.0:{port}"

# Worker processes - auto-detect CPU cores
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000

# Worker lifecycle
max_requests = 1000
max_requests_jitter = 50
timeout = 120
keepalive = 5

# Logging
accesslog = "-"  # stdout
errorlog = "-"   # stdout
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = f"quant_trading_{port}"

# Server mechanics
daemon = False
pidfile = f"/tmp/gunicorn_quant_{port}.pid"

# SSL (handled by Nginx in production)
forwarded_allow_ips = '*'
secure_scheme_headers = {
    'X-FORWARDED-PROTOCOL': 'ssl',
    'X-FORWARDED-PROTO': 'https',
    'X-FORWARDED-SSL': 'on'
}

# Preload app for memory efficiency
preload_app = True

# User/Group (run as current user for now)
# user = "www-data"
# group = "www-data"

# Environment
raw_env = [
    "FLASK_ENV=production",
    f"PORT={port}"
]

# Server hooks
def on_starting(server):
    print(f"🚀 Starting Quant Trading Server on port {port}")

def on_reload(server):
    print(f"🔄 Reloading server on port {port}")

def when_ready(server):
    print(f"✅ Server ready on port {port} with {workers} workers")

def worker_int(worker):
    print(f"⚠️ Worker {worker.pid} received SIGINT")

def worker_abort(worker):
    print(f"🛑 Worker {worker.pid} aborted")
