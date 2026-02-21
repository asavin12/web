#!/bin/bash
# Script để chạy React SPA trong development mode
# Chạy cả Django backend và Vite dev server

echo "🚀 Starting UnstressVN Development Servers..."
echo ""

# Kill any existing processes on ports 8000 and 5173
echo "🔄 Checking for existing processes..."
lsof -ti:8000 | xargs -r kill -9 2>/dev/null
lsof -ti:5173 | xargs -r kill -9 2>/dev/null

# Start Django backend
echo "📦 Starting Django backend on http://localhost:8000..."
cd /home/unstress/UnstressVN/UnstressVN
python manage.py runserver 0.0.0.0:8000 &
DJANGO_PID=$!

# Wait for Django to start
sleep 2

# Start Vite dev server
echo "⚛️ Starting React frontend on http://localhost:5173..."
cd /home/unstress/UnstressVN/UnstressVN/frontend
npm run dev &
VITE_PID=$!

echo ""
echo "✅ Development servers started!"
echo ""
echo "🌐 Django backend:   http://localhost:8000"
echo "⚛️ React frontend:   http://localhost:5173"
echo "📡 API endpoints:    http://localhost:8000/api/v1/"
echo ""
echo "Press Ctrl+C to stop all servers..."

# Wait for Ctrl+C
trap "kill $DJANGO_PID $VITE_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
