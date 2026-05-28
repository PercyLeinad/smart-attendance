#!/bin/bash

source "$(pwd)/.venv/bin/activate"

IP=127.0.0.1
PORT=8000
WORKERS=4
LOG_DIR="/var/log/gunicorn"

echo "Starting FastAPI with Gunicorn..."

gunicorn app.main:app \
    -k uvicorn.workers.UvicornWorker \
    -w "$WORKERS" \
    -b "$IP:$PORT" \
    --timeout 30 \
    --keep-alive 5 \
    --worker-tmp-dir /dev/shm \
    --forwarded-allow-ips="*" \
    --access-logfile "$LOG_DIR/access.log" \
    --error-logfile "$LOG_DIR/error.log" \
    --log-level infonproc