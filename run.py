"""
Universal Knowledge Graph (UKG) System - Run Script

This script provides a standalone entry point to run the UKG application
on a configurable port (8080) to avoid conflicts with other services.
"""

import os
import logging
from app import app

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Get port configuration with fallback to 8080
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting UKG application on port {port}")
    
    # Run the application with debug mode
    app.run(host="0.0.0.0", port=port, debug=True)