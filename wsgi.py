"""
Universal Knowledge Graph (UKG) System - WSGI Entry Point

This file serves as the WSGI entry point for the UKG system,
used for production deployments with Gunicorn.
"""

import os
from main import app

port = int(os.environ.get("PORT", 5000))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)