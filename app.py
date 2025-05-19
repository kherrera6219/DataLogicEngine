"""
Universal Knowledge Graph (UKG) System - Flask Application

This is the main Flask application that serves the UKG API and coordinates
with the Enterprise Architecture backend services.
"""

from flask import Flask, jsonify, request, render_template, abort
from flask_cors import CORS
import os
import logging
import json
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv
from backend.rest_api import register_api as register_rest_api
from backend.chat_api import register_chat_api

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

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

# Import configuration manager
try:
    from backend.config_manager import get_config
    config = get_config()
except ImportError:
    logger.warning("Config manager not found, using default settings")
    config = None

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    CORS(app)

    # Configure from environment variables or config manager
    if config:
        app.config['SECRET_KEY'] = config.get("auth.jwt_secret", os.urandom(24))
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///ukg.db')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['DEBUG'] = config.get("system.debug", False)
        app.config['ENVIRONMENT'] = config.get("system.environment", "development")
        app.config['ENTERPRISE_MODE'] = True
    else:
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///ukg.db')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['DEBUG'] = os.environ.get('DEBUG', 'False').lower() == 'true'
        app.config['ENVIRONMENT'] = os.environ.get('ENVIRONMENT', 'development')
        app.config['ENTERPRISE_MODE'] = os.environ.get('ENTERPRISE_MODE', 'False').lower() == 'true'

    # Initialize database
    from backend.ukg_db import init_db
    db = init_db(app)
    app.config['DB'] = db

    # Initialize UKG components
    from core.system.system_initializer import initialize_ukg_system
    initialize_ukg_system(app)

    # Initialize enterprise architecture if in enterprise mode
    if app.config['ENTERPRISE_MODE']:
        try:
            from backend.enterprise_architecture import get_enterprise_architecture
            app.config['ENTERPRISE_ARCH'] = get_enterprise_architecture()
            logger.info("Enterprise architecture initialized")
        except ImportError:
            logger.warning("Enterprise architecture module not found")

    # Register API blueprints
    register_rest_api(app)
    register_chat_api(app)

    # System routes
    @app.route('/health')
    def health():
        """Health check endpoint for the UKG Core Service"""
        status = {
            "status": "healthy",
            "service": "UKG API Gateway",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "environment": app.config['ENVIRONMENT']
        }
        
        # Add enterprise service status if available
        if app.config.get('ENTERPRISE_ARCH'):
            try:
                enterprise_status = app.config['ENTERPRISE_ARCH'].get_architecture_status()
                status["enterprise"] = {
                    "services": len(enterprise_status["services"]),
                    "status": "healthy" if all(svc["status"] == "healthy" for name, svc in 
                              enterprise_status["services"].items()) else "degraded"
                }
            except Exception as e:
                logger.error(f"Failed to get enterprise status: {e}")
                status["enterprise"] = {"status": "error"}
                
        return jsonify(status)

    @app.route('/system/status')
    def system_status():
        """Full system status endpoint"""
        if not app.config.get('ENTERPRISE_ARCH'):
            return jsonify({
                "mode": "standalone",
                "status": "healthy",
                "timestamp": datetime.now().isoformat()
            })
            
        try:
            enterprise_status = app.config['ENTERPRISE_ARCH'].get_architecture_status()
            return jsonify({
                "mode": "enterprise",
                "status": "healthy" if all(svc["status"] == "healthy" for name, svc in 
                          enterprise_status["services"].items()) else "degraded",
                "services": enterprise_status["services"],
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to get enterprise status: {e}")
            return jsonify({
                "mode": "enterprise",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

    @app.route('/')
    def home():
        """Render the home page."""
        return render_template('home.html')

    # API gateway proxy routes for enterprise services
    @app.route('/api/webhooks/<path:path>', methods=['POST', 'GET', 'PUT', 'DELETE'])
    def webhook_proxy(path):
        """Proxy requests to webhook server"""
        if not app.config.get('ENTERPRISE_ARCH'):
            abort(404)
            
        try:
            webhook_service = app.config['ENTERPRISE_ARCH'].get_service("webhook_server")
            if not webhook_service:
                abort(503)  # Service unavailable
                
            webhook_url = f"{webhook_service.endpoint}/webhooks/{path}"
            response = requests.request(
                method=request.method,
                url=webhook_url,
                headers={key: value for key, value in request.headers if key != 'Host'},
                data=request.get_data(),
                cookies=request.cookies,
                allow_redirects=False,
            )
            
            return (response.content, response.status_code, response.headers.items())
        except Exception as e:
            logger.error(f"Webhook proxy error: {e}")
            abort(500)

    @app.route('/api/model/<path:path>', methods=['POST', 'GET', 'PUT', 'DELETE'])
    def model_context_proxy(path):
        """Proxy requests to model context server"""
        if not app.config.get('ENTERPRISE_ARCH'):
            abort(404)
            
        try:
            model_service = app.config['ENTERPRISE_ARCH'].get_service("model_context_server")
            if not model_service:
                abort(503)  # Service unavailable
                
            model_url = f"{model_service.endpoint}/{path}"
            response = requests.request(
                method=request.method,
                url=model_url,
                headers={key: value for key, value in request.headers if key != 'Host'},
                data=request.get_data(),
                cookies=request.cookies,
                allow_redirects=False,
            )
            
            return (response.content, response.status_code, response.headers.items())
        except Exception as e:
            logger.error(f"Model context proxy error: {e}")
            abort(500)

    # Catch-all API health check
    @app.route('/api/health')
    def api_health():
        """Simple health check endpoint."""
        return jsonify({
            "status": "healthy",
            "service": "UKG API",
            "timestamp": datetime.now().isoformat()
        })

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({
            "success": False,
            "message": "Resource not found",
            "error_code": "NOT_FOUND",
            "timestamp": datetime.now().isoformat()
        }), 404

    @app.errorhandler(500)
    def server_error(error):
        """Handle 500 errors."""
        return jsonify({
            "success": False,
            "message": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "timestamp": datetime.now().isoformat()
        }), 500

    @app.errorhandler(503)
    def service_unavailable(error):
        """Handle 503 errors."""
        return jsonify({
            "success": False,
            "message": "Service unavailable",
            "error_code": "SERVICE_UNAVAILABLE",
            "timestamp": datetime.now().isoformat()
        }), 503

    logger.info("UKG application configured and initialized")
    return app

# Create the Flask application
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = app.config.get('DEBUG', False)
    logger.info(f"Starting UKG API on port {port} (debug={debug})")
    app.run(host="0.0.0.0", port=port, debug=debug)