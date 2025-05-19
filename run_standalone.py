"""
Universal Knowledge Graph (UKG) System - Standalone Runner

This script provides a standalone way to run the UKG system
without relying on workflow configurations.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set environment variables for proper operation
os.environ["PORT"] = "8080"
os.environ["FLASK_APP"] = "wsgi.py"
os.environ["FLASK_ENV"] = "development"

# Import the application
from wsgi import app

if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT", 8080))
        logger.info(f"Starting UKG application on port {port}")
        app.run(host="0.0.0.0", port=port, debug=True)
    except Exception as e:
        logger.error(f"Error starting UKG application: {str(e)}")
        sys.exit(1)