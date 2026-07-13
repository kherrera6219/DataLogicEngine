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
from backend.security.listener_policy import resolve_loopback_listener_host

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    listener_host = resolve_loopback_listener_host(os.environ.get("FLASK_RUN_HOST"))
    app.run(host=listener_host, port=port)
