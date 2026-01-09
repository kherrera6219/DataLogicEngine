#!/bin/bash

# Azure App Service Custom Startup Script

# 1. Apply Database Migrations
echo "Applying database migrations..."
flask db upgrade

# 2. Seed Data (Idempotent)
echo "Seeding initial data..."
python backend/seed_data.py

# 3. Start Gunicorn
echo "Starting Gunicorn..."
# Azure places the app code in /home/site/wwwroot by default
# We assume the container structure where app is in /app
gunicorn --bind=0.0.0.0:8000 --workers=4 --timeout=600 app:app
