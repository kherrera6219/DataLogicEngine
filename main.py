
"""
Universal Knowledge Graph (UKG) System - Main Entry Point

This module serves as the entry point for the UKG system.
"""

import os
import logging
from app import create_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the application
app = create_app()

# Main execution
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting UKG system on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
