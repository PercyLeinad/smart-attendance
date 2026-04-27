#!/bin/bash

echo "🧪 Starting FastAPI (development mode)..."

# Activate virtual environment
source "$(pwd)/.venv/bin/activate"

# Get LAN IP (first non-loopback IPv4)
IP=$(hostname -I | awk '{print $1}')

# Fallback in case detection fails
if [ -z "$IP" ]; then
    echo "⚠️ Could not detect LAN IP, falling back to 127.0.0.1"
    IP="127.0.0.1"
fi

PORT=8000

# Kill anything running on port 8000 (optional but helpful)
echo "Checking port $PORT..."
lsof -ti:$PORT | xargs kill -9 2>/dev/null


echo "✅ Development server running at http://$IP:$PORT"

# Run from the root, but watch the 'app' directory specifically
uvicorn app.main:app \
    --host "$IP" \
    --port "$PORT" \
    --reload \
    --reload-dir app \
    --reload-include "*.py" \
    --reload-include "*.html" \
    --reload-include "*.css" \
    --reload-include "*.js" \
    --log-level debug

