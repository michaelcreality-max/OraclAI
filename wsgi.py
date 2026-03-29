"""
WSGI Entry Point for Production Servers
Supports both primary and backup server modes
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app from production_server
from production_server import app

# Gunicorn will look for 'application' variable
application = app

if __name__ == "__main__":
    # For testing WSGI directly
    port = int(os.environ.get('PORT', 5000))
    application.run(host='0.0.0.0', port=port, threaded=True)
