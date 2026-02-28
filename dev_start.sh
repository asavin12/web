#!/bin/bash
# Script khởi động development servers cho UnstressVN

set -e

# Màu sắc output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_DIR="/home/unstress/unstressvn"
VENV_PATH="$PROJECT_DIR/.venv"
PYTHON="$VENV_PATH/bin/python"
BACKEND_DIR="$PROJECT_DIR"
FRONTEND_DIR="$PROJECT_DIR/frontend"
PID_DIR="$PROJECT_DIR/.pids"

# Tạo thư mục PID nếu chưa có
mkdir -p "$PID_DIR"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   UnstressVN Development Environment  ${NC}"
echo -e "${GREEN}========================================${NC}"

# Kiểm tra PostgreSQL
echo -e "${YELLOW}[1/4] Checking PostgreSQL...${NC}"
if pg_isready -h 127.0.0.1 -p 5433 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL is running on port 5433${NC}"
else
    echo -e "${RED}✗ PostgreSQL is not running. Starting...${NC}"
    sudo systemctl start postgresql@16-main
    sleep 2
    if pg_isready -h 127.0.0.1 -p 5433 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PostgreSQL started${NC}"
    else
        echo -e "${RED}✗ Failed to start PostgreSQL${NC}"
        exit 1
    fi
fi

# Check virtual environment
echo -e "${YELLOW}[2/4] Checking virtual environment...${NC}"
if [ ! -f "$PYTHON" ]; then
    echo -e "${RED}✗ Virtual environment not found: $PYTHON${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Virtual environment OK${NC}"

# Start Django backend
echo -e "${YELLOW}[3/4] Starting Django backend (port 8000)...${NC}"
cd "$BACKEND_DIR"
"$PYTHON" manage.py runserver 0.0.0.0:8000 > "$PID_DIR/django.log" 2>&1 &
echo $! > "$PID_DIR/django.pid"
sleep 2

if kill -0 $(cat "$PID_DIR/django.pid") 2>/dev/null; then
    echo -e "${GREEN}✓ Django server started (PID: $(cat $PID_DIR/django.pid))${NC}"
else
    echo -e "${RED}✗ Failed to start Django server. Check logs:${NC}"
    tail -20 "$PID_DIR/django.log"
    exit 1
fi

# Start Vite frontend
echo -e "${YELLOW}[4/4] Starting Vite frontend (port 5173)...${NC}"
cd "$FRONTEND_DIR"
if [ -d "node_modules" ]; then
    npm run dev > "$PID_DIR/vite.log" 2>&1 &
    echo $! > "$PID_DIR/vite.pid"
    sleep 3
    
    if kill -0 $(cat "$PID_DIR/vite.pid") 2>/dev/null; then
        echo -e "${GREEN}✓ Vite server started (PID: $(cat $PID_DIR/vite.pid))${NC}"
    else
        echo -e "${RED}✗ Failed to start Vite server. Check logs:${NC}"
        tail -20 "$PID_DIR/vite.log"
    fi
else
    echo -e "${YELLOW}! node_modules not found. Running npm install first...${NC}"
    npm install
    npm run dev > "$PID_DIR/vite.log" 2>&1 &
    echo $! > "$PID_DIR/vite.pid"
    sleep 3
    echo -e "${GREEN}✓ Vite server started${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Development Servers Started!        ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "  Backend:  ${GREEN}http://localhost:8000${NC}"
echo -e "  Frontend: ${GREEN}http://localhost:5173${NC}"
echo -e "  Admin:    ${GREEN}http://localhost:8000/admin/${NC}"
echo ""
echo -e "  To stop servers: ${YELLOW}./dev_stop.sh${NC}"
echo ""
