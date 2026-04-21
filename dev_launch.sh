#!/bin/bash

echo "🧪 Starting FastAPI (development mode)..."

# Activate virtual environment
source "$(pwd)/.venv/bin/activate"

# Config
IP=127.0.0.1
PORT=8000

# Kill anything running on port 8000 (optional but helpful)
echo "Checking port $PORT..."
lsof -ti:$PORT | xargs kill -9 2>/dev/null

# Start FastAPI with auto-reload
uvicorn app.main:app \
    --host "$IP" \
    --port "$PORT" \
    --reload

echo "✅ Development server running at http://$IP:$PORT"