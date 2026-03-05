#!/bin/bash
echo "Starting FastAPI..."

# Activating env
source $(pwd)/.venv/bin/activate

cd app

# Get the local IP address of the machine changed to wlp2s0 for wireless, change to eth0 for wired connection
IP=$(ip -4 -o addr show wlp2s0 | awk '{print $4}' | cut -d/ -f1)

uvicorn main:app --reload --port 8000 --host "$IP"
