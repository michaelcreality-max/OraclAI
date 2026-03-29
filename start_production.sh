#!/bin/zsh
# Production WSGI Server Deployment Script
# Starts both primary and backup Gunicorn servers with Nginx load balancer

echo "🚀 Quant Trading System - Production WSGI Deployment"
echo "======================================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if gunicorn is installed
if ! command -v gunicorn &> /dev/null; then
    echo "${YELLOW}⚠️  Gunicorn not found. Installing...${NC}"
    pip3 install gunicorn
fi

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to kill process on port
kill_port() {
    local port=$1
    local pid=$(lsof -ti:$port)
    if [ -n "$pid" ]; then
        echo "${YELLOW}Killing process on port $port (PID: $pid)...${NC}"
        kill -9 $pid 2>/dev/null
        sleep 2
    fi
}

# Check and free ports
echo ""
echo "🔍 Checking ports..."
if check_port 5000; then
    echo "${YELLOW}Port 5000 is in use${NC}"
    kill_port 5000
fi

if check_port 5001; then
    echo "${YELLOW}Port 5001 is in use${NC}"
    kill_port 5001
fi

# Start Primary Server
echo ""
echo "🔵 Starting PRIMARY Server on port 5000..."
cd "/Users/joanna/Downloads/VSCode Folder (python)"
PORT=5000 gunicorn --config gunicorn.conf.py wsgi:application --daemon --pid /tmp/gunicorn_primary.pid

if [ $? -eq 0 ]; then
    echo "${GREEN}✅ Primary server started${NC}"
else
    echo "${RED}❌ Failed to start primary server${NC}"
    exit 1
fi

# Wait a moment
sleep 3

# Start Backup Server
echo ""
echo "🟡 Starting BACKUP Server on port 5001..."
PORT=5001 gunicorn --config gunicorn.conf.py wsgi:application --daemon --pid /tmp/gunicorn_backup.pid

if [ $? -eq 0 ]; then
    echo "${GREEN}✅ Backup server started${NC}"
else
    echo "${RED}❌ Failed to start backup server${NC}"
    # Kill primary if backup failed
    kill_port 5000
    exit 1
fi

# Wait for servers to initialize
sleep 3

# Health checks
echo ""
echo "🏥 Running health checks..."

primary_health=$(curl -s http://localhost:5000/api/health 2>&1)
if echo "$primary_health" | grep -q "healthy\|ok"; then
    echo "${GREEN}✅ Primary server healthy${NC}"
else
    echo "${RED}⚠️  Primary server health check failed${NC}"
    echo "$primary_health"
fi

backup_health=$(curl -s http://localhost:5001/api/health 2>&1)
if echo "$backup_health" | grep -q "healthy\|ok"; then
    echo "${GREEN}✅ Backup server healthy${NC}"
else
    echo "${RED}⚠️  Backup server health check failed${NC}"
    echo "$backup_health"
fi

# Summary
echo ""
echo "======================================================"
echo "📊 SERVER STATUS"
echo "======================================================"
echo "Primary: http://localhost:5000"
echo "Backup:  http://localhost:5001"
echo ""
echo "🔄 Management Commands:"
echo "  Restart Primary:  kill -HUP \$(cat /tmp/gunicorn_primary.pid)"
echo "  Restart Backup:   kill -HUP \$(cat /tmp/gunicorn_backup.pid)"
echo "  Stop All:         ./stop_production.sh"
echo "  View Logs:        tail -f /tmp/gunicorn*.log"
echo ""
echo "🌐 Nginx (Load Balancer):"
echo "  Install config:   sudo cp nginx_quant.conf /opt/homebrew/etc/nginx/servers/"
echo "  Start Nginx:      sudo nginx"
echo "  Test:             curl http://localhost/api/health"
echo ""
echo "${GREEN}🎉 Production WSGI servers are running!${NC}"
echo "======================================================"
