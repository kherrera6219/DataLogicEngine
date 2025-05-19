"""
Universal Knowledge Graph (UKG) System - Main Entry Point

This file serves as the main entry point for the UKG system.
It registers all components, blueprints, and initializes the application.
"""

import os
import logging
import uuid
import json
from datetime import datetime
from flask import request, jsonify, render_template, redirect, url_for, session, send_from_directory

# Import app and db from app.py
from app import app, db, logger

# Import models
import db_models

# Import API and middleware components
from backend.middleware import setup_middleware
from backend.ukg_api import register_api

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Set up middleware
setup_middleware(app)

# Register API blueprints
register_api(app)

# Configure port for the application
port = int(os.environ.get("PORT", 8080))

# Basic routes for the web interface
@app.route('/')
def home():
    """Render the home page."""
    return render_template('index.html', title="Universal Knowledge Graph System")

@app.route('/simulation')
def simulation_page():
    """Render the simulation page."""
    return render_template('simulation.html', title="UKG Simulation")

@app.route('/api/docs')
def api_docs():
    """Render the API documentation page."""
    return render_template('api_docs.html', title="UKG API Documentation")

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files."""
    return send_from_directory('static', path)

# Initialize seed data if needed
@app.before_first_request
def initialize_seed_data():
    """Initialize seed data if tables are empty."""
    try:
        # Import models here to make sure they're loaded
        from db_models import PillarLevel, Sector, Domain
        
        # Check if we need to seed pillar levels
        if PillarLevel.query.count() == 0:
            logger.info("Seeding initial pillar level data...")
            from backend.ukg_api import seed_pillar_levels
            seed_pillar_levels()
        
        # Check if we need to seed sectors
        if Sector.query.count() == 0:
            logger.info("Seeding initial sector data...")
            from backend.ukg_api import seed_sectors
            seed_sectors()
        
        # Check if we need to seed domains
        if Domain.query.count() == 0:
            logger.info("Seeding initial domain data...")
            from backend.ukg_api import seed_domains
            seed_domains()
    except Exception as e:
        logger.error(f"Error initializing seed data: {str(e)}")

# Run the application
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port, debug=True)