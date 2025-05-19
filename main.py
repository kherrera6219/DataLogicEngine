"""
Universal Knowledge Graph (UKG) System - Main Entry Point

This file serves as the main entry point for the UKG system.
It registers all components, blueprints, and initializes the application.
"""

# Import application
from app import app

# Make the app available for gunicorn
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)