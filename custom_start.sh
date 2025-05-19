#!/bin/bash
# Custom start script for the Universal Knowledge Graph (UKG) System

# Kill any existing processes using port 8080
echo "Checking for processes on port 8080..."
lsof -i :8080 | grep LISTEN | awk '{print $2}' | xargs -r kill -9

# Set environment variables
export PORT=8080
export FLASK_APP=wsgi.py
export FLASK_ENV=development

# Start the server using gunicorn
echo "Starting Universal Knowledge Graph system on port 8080 with gunicorn..."
gunicorn --bind 0.0.0.0:8080 --reuse-port --reload main:app