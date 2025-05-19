
#!/bin/bash

# Enterprise UKG System Startup Script

# Create log directory if it doesn't exist
mkdir -p logs

# Log file
LOG_FILE="logs/startup_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "Starting UKG Enterprise Architecture..."

# Kill any existing processes on relevant ports
echo "Cleaning up existing processes..."
pkill -f "port=5000" || true
pkill -f "port=5001" || true
pkill -f "port=5002" || true
pkill -f "port=5003" || true
pkill -f "port=3000" || true

# Set environment variables
export ENTERPRISE_MODE=true
export FLASK_ENV=production
export DEBUG=false

# Start the Python-based enterprise orchestrator
echo "Starting Enterprise UKG system using orchestrator..."

if [ "$1" == "--build" ]; then
    echo "Building frontend before startup..."
    python run_enterprise_ukg.py --build
else
    python run_enterprise_ukg.py
fi

# Script will terminate when run_enterprise_ukg.py terminates
echo "Enterprise shutdown complete."
