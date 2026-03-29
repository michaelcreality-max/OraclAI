#!/usr/bin/env python3
"""
Backup Server - Failover for Production AI Debate System
Runs on alternate port with same functionality
"""

import sys
import os

# Backup server configuration
BACKUP_PORT = int(os.environ.get('BACKUP_PORT', 5001))
PRIMARY_PORT = int(os.environ.get('PRIMARY_PORT', 5000))

# Import and run production server with backup settings
os.environ['PORT'] = str(BACKUP_PORT)
os.environ['HOST'] = '0.0.0.0'

print(f"🔧 Starting BACKUP Server on port {BACKUP_PORT}")
print(f"📡 Primary server expected on port {PRIMARY_PORT}")
print(f"🔄 This server activates if primary fails")

# Import the production server
from production_server import app, log

if __name__ == "__main__":
    log.info(f"🚀 Backup Server starting on port {BACKUP_PORT}")
    log.info(f"🔄 Will take over if primary server ({PRIMARY_PORT}) fails")
    
    app.run(
        host='0.0.0.0',
        port=BACKUP_PORT,
        debug=False,
        threaded=True,
        use_reloader=False
    )
