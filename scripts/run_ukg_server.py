"""
Universal Knowledge Graph (UKG) System - Standalone Server

This script runs the UKG system on port 8080 to avoid 
port conflicts with other services.
"""

import os
import sys
import logging
import json
from flask import Flask, request, jsonify, render_template
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Print startup message
print("Starting Universal Knowledge Graph (UKG) System on port 8080")

# Import the Flask app
from app import app

# Set port to 8080
port = int(os.environ.get("PORT", 8080))

# Run the application
if __name__ == "__main__":
    print(f"UKG System starting on http://0.0.0.0:{port}")
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host="0.0.0.0", port=port, debug=debug_mode)