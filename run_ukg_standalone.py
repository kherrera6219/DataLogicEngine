#!/usr/bin/env python3
"""
Universal Knowledge Graph (UKG) System - Standalone Runner

This script provides a way to run the UKG system without relying on 
Replit workflows that might have port conflicts.
"""

import os
import sys
import logging
import argparse
import time
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("UKG-Standalone")

def main():
    """Run the UKG system."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the UKG system")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the server on (default: 8080)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the server to (default: 0.0.0.0)")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    args = parser.parse_args()
    
    # Set environment variables
    os.environ["PORT"] = str(args.port)
    os.environ["HOST"] = args.host
    os.environ["DEBUG"] = "True" if args.debug else "False"
    
    # Print startup banner
    print_banner(args.port)
    
    # Import the Flask app
    try:
        from app import app
        logger.info("Successfully imported Flask app")
    except Exception as e:
        logger.error(f"Error importing Flask app: {str(e)}")
        sys.exit(1)
    
    # Run the app
    try:
        logger.info(f"Starting UKG system on http://{args.host}:{args.port}")
        app.run(host=args.host, port=args.port, debug=args.debug)
    except Exception as e:
        logger.error(f"Error running Flask app: {str(e)}")
        sys.exit(1)

def print_banner(port):
    """Print a startup banner."""
    banner = f"""
    ╔════════════════════════════════════════════════════════════════╗
    ║                                                                ║
    ║                Universal Knowledge Graph System                ║
    ║                                                                ║
    ║  Version: 1.0.0                                               ║
    ║  Server running at: http://localhost:{port}                    ║
    ║  Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                      ║
    ║                                                                ║
    ╚════════════════════════════════════════════════════════════════╝
    """
    print(banner)

if __name__ == "__main__":
    main()