#!/bin/bash
# Script to start the Universal Knowledge Graph server

# Set environment variables
export PORT=8080
export FLASK_APP=wsgi.py
export FLASK_ENV=development

# Kill any existing processes running on port 8080
echo "Checking for processes on port 8080..."
lsof -i :8080 | grep LISTEN | awk '{print $2}' | xargs -r kill -9

# Start the server
echo "Starting Universal Knowledge Graph system on port 8080..."
python wsgi.py