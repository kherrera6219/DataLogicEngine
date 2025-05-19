#!/bin/bash
# Start script for the Universal Knowledge Graph application
# This script runs the application on port 8080 to avoid conflicts

echo "Starting Universal Knowledge Graph system on port 8080..."
export FLASK_APP=wsgi.py
export FLASK_ENV=development
export PORT=8080

# Create database tables if they don't exist
python -c "from app import app, db; from models import *; app.app_context().push(); db.create_all()"

# Start the application with gunicorn
gunicorn --bind 0.0.0.0:8080 --reuse-port --reload wsgi:app