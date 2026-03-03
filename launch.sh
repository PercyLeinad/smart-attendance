#!/bin/bash
echo "Starting FastAPI..."

# Activating env
source $(pwd)/.venv/bin/activate

cd app

IP=$(ip -4 -o addr show wlp2s0 | awk '{print $4}' | cut -d/ -f1)

uvicorn main:app --reload --port 8000 --host "$IP"
