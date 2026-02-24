#!/bin/bash
echo "Starting FastAPI..."

# Activating env
source $(pwd)/.venv/bin/activate

cd app

uvicorn main:app --reload --port 8000 --host 0.0.0.0
