"""
Universal Knowledge Graph (UKG) System - Flask Application

This is the main Flask application that serves the UKG API.
"""

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import os
import logging
import json
from dotenv import load_dotenv
from backend.rest_api import register_api as register_rest_api
from backend.chat_api import register_chat_api
import sys
from datetime import datetime


# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/ukg_core_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger("UKG-Core")

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    CORS(app)

    # Configure from environment variables
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///ukg.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize database
    from backend.ukg_db import init_db
    db = init_db(app)
    app.config['DB'] = db

    # Initialize UKG components
    from core.system.system_initializer import initialize_ukg_system
    initialize_ukg_system(app)

    # Register API blueprints
    register_rest_api(app)
    register_chat_api(app)

    # Homepage route
    @app.route('/health')
    def health():
        """Health check endpoint for the UKG Core Service"""
        return jsonify({
            "status": "healthy",
            "service": "UKG Core Service",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        })


    @app.route('/')
    def home():
        """Render the home page."""
        return render_template('home.html')

    # Catch-all API health check
    @app.route('/api/health')
    def api_health():
        """Simple health check endpoint."""
        return jsonify({
            "status": "healthy",
            "service": "UKG API",
            "timestamp": datetime.datetime.now().isoformat()
        })

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({
            "success": False,
            "message": "Resource not found",
            "error_code": "NOT_FOUND",
            "timestamp": datetime.datetime.now().isoformat()
        }), 404

    @app.errorhandler(500)
    def server_error(error):
        """Handle 500 errors."""
        return jsonify({
            "success": False,
            "message": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "timestamp": datetime.datetime.now().isoformat()
        }), 500

    logger.info("UKG application configured and initialized")
    return app

# Create the Flask application
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)