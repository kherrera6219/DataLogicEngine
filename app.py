"""
Universal Knowledge Graph (UKG) System - Main Application

This is the main application file for the UKG system,
handling database setup and application initialization.
"""

# This file is the central entry point for the UKG application and should initialize
# the core Flask app, database connection, and all necessary components.

import os
import logging
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create a base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Create the Flask app and database
db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "ukg-dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize app with database
db.init_app(app)

# Setup error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    logger.error(f"Server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

# Initialize database tables
def create_tables():
    """Create database tables."""
    with app.app_context():
        # Import models to ensure they're registered with SQLAlchemy
        from models import PillarLevel, Sector, Domain, Location, KnowledgeNode, SimulationSession
        
        # Create tables
        db.create_all()
        logger.info("Database tables created successfully.")

# Create tables when the app starts
with app.app_context():
    try:
        create_tables()
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")