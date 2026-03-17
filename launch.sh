#!/bin/bash

echo "Starting FastAPI..."

# Activating env
source $(pwd)/.venv/bin/activate

cd app

IP=127.0.0.1

uvicorn main:app --reload --port 8000 --host "$IP"
