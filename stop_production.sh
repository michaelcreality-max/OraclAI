#!/bin/zsh
# Stop Production WSGI Servers

echo "🛑 Stopping Quant Trading Production Servers..."
echo "======================================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Stop by PID files
if [ -f /tmp/gunicorn_primary.pid ]; then
    primary_pid=$(cat /tmp/gunicorn_primary.pid)
    echo "Stopping Primary Server (PID: $primary_pid)..."
    kill -TERM $primary_pid 2>/dev/null
    rm -f /tmp/gunicorn_primary.pid
    echo "${GREEN}✅ Primary server stopped${NC}"
fi

if [ -f /tmp/gunicorn_backup.pid ]; then
    backup_pid=$(cat /tmp/gunicorn_backup.pid)
    echo "Stopping Backup Server (PID: $backup_pid)..."
    kill -TERM $backup_pid 2>/dev/null
    rm -f /tmp/gunicorn_backup.pid
    echo "${GREEN}✅ Backup server stopped${NC}"
fi

# Kill any remaining processes on ports 5000 and 5001
for port in 5000 5001; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ -n "$pid" ]; then
        echo "${YELLOW}Force killing process on port $port (PID: $pid)...${NC}"
        kill -9 $pid 2>/dev/null
    fi
done

echo ""
echo "${GREEN}🎉 All production servers stopped${NC}"
echo "======================================================"
