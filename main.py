"""
Universal Knowledge Graph (UKG) System - Main Entry Point

This module serves as the entry point for the UKG system.
It initializes the Flask application with enterprise-grade security and standards.
"""

import os
import logging
from app import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("ukg_system.log")
    ]
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        # Get port from environment or default to 3000
        port = int(os.environ.get("PORT", 3000))
        
        # Log startup
        logger.info(f"UKG System starting on port {port}")
        logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'production')}")
        
        # Run the application
        app.run(host='0.0.0.0', port=port, debug=False)
    
    except Exception as e:
        logger.error(f"Error starting UKG System: {str(e)}")
        raise