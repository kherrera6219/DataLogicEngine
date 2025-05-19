
#!/bin/bash

# Enterprise UKG System Startup Script

echo "Starting UKG Enterprise Architecture..."

# Kill any existing processes on relevant ports
echo "Cleaning up existing processes..."
pkill -f "port=5000" || true
pkill -f "port=5001" || true
pkill -f "port=5002" || true
pkill -f "port=5003" || true
pkill -f "port=3000" || true

# Start the core API server
echo "Starting Core API server on port 5000..."
FLASK_APP=app.py FLASK_ENV=production gunicorn --bind 0.0.0.0:5000 --workers=2 app:app &
sleep 2

# Start the webhook server
echo "Starting Webhook server on port 5001..."
WEBHOOK_PORT=5001 PYTHONUNBUFFERED=1 python backend/webhook_server/webhook_server.py &
sleep 2

# Start the model context server
echo "Starting Model Context Protocol server on port 5002..."
MODEL_CONTEXT_PORT=5002 PYTHONUNBUFFERED=1 python backend/model_context/model_context_server.py &
sleep 2

# Start the core UKG service
echo "Starting Core UKG service on port 5003..."
UKG_CORE_PORT=5003 PYTHONUNBUFFERED=1 python backend/enterprise_architecture.py &
sleep 2

# Start Next.js frontend in production mode
echo "Starting Next.js frontend on port 3000..."
npm run build && npm start
