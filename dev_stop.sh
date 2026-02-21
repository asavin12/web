#!/bin/bash
# Script dừng development servers cho UnstressVN

# Màu sắc output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_DIR="/home/unstress/unstressvn"
PID_DIR="$PROJECT_DIR/.pids"

echo -e "${YELLOW}Stopping development servers...${NC}"

# Stop Django
if [ -f "$PID_DIR/django.pid" ]; then
    PID=$(cat "$PID_DIR/django.pid")
    if kill -0 $PID 2>/dev/null; then
        kill $PID 2>/dev/null
        echo -e "${GREEN}✓ Django server stopped (PID: $PID)${NC}"
    fi
    rm -f "$PID_DIR/django.pid"
else
    # Fallback: kill any runserver process
    pkill -f "manage.py runserver" 2>/dev/null && echo -e "${GREEN}✓ Django server stopped${NC}"
fi

# Stop Vite
if [ -f "$PID_DIR/vite.pid" ]; then
    PID=$(cat "$PID_DIR/vite.pid")
    if kill -0 $PID 2>/dev/null; then
        kill $PID 2>/dev/null
        echo -e "${GREEN}✓ Vite server stopped (PID: $PID)${NC}"
    fi
    rm -f "$PID_DIR/vite.pid"
else
    # Fallback: kill any vite process
    pkill -f "vite" 2>/dev/null && echo -e "${GREEN}✓ Vite server stopped${NC}"
fi

# Also kill any node processes running on port 5173
lsof -ti:5173 2>/dev/null | xargs -r kill 2>/dev/null

echo -e "${GREEN}All development servers stopped.${NC}"
