#!/bin/bash

echo "Starting FastAPI..."

# Activating env
source $(pwd)/.venv/bin/activate

cd app

# Get machine IP automatically
IP=$(ip route get 1.1.1.1 | awk '{print $7; exit}')

uvicorn main:app --reload --port 8000 --host "$IP"
