#!/bin/bash

# This script installs the necessary dependencies for the Smart Attendance System.
curl -LsSf https://astral.sh/uv/install.sh | sh

# Initialize the project and install dependencies from requirements.txt
uv init

uv add -r requirements.txt