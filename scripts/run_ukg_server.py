# ruff: noqa: E402
"""
Universal Knowledge Graph (UKG) System - Standalone Server

This script runs the UKG system on port 8080 to avoid 
port conflicts with other services.
"""

import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Print startup message
print("Starting Universal Knowledge Graph (UKG) System on port 8080")

from app import create_app
from backend.security.listener_policy import resolve_loopback_listener_host

# Set port to 8080
port = int(os.environ.get("PORT", 8080))

# Run the application
if __name__ == "__main__":
    app = create_app(start_runtime=True)
    host = resolve_loopback_listener_host(os.environ.get("FLASK_RUN_HOST"))
    print(f"UKG System starting on http://{host}:{port}")
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    try:
        app.run(host=host, port=port, debug=debug_mode, use_reloader=False)
    finally:
        app.extensions["dle_runtime"].shutdown()
