#!/bin/bash

echo "Starting FastAPI with Gunicorn..."

source "$(pwd)/.venv/bin/activate"

IP=127.0.0.1
PORT=8000
WORKERS=8

gunicorn app.main:app \
    -k uvicorn.workers.UvicornWorker \
    -w "$WORKERS" \
    -b "$IP:$PORT" \
    --timeout 30