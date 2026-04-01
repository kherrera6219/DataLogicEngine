# ruff: noqa: E402
"""
Universal Knowledge Graph (UKG) System - WSGI Entry Point

This file serves as the WSGI entry point for the UKG system,
used for production deployments with Gunicorn.
"""

import os
import sys

from backend.bootstrap_compat import apply_runtime_compatibility_patches

# Ensure root directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
apply_runtime_compatibility_patches()

from app import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
