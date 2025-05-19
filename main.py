import logging
import os
from datetime import datetime
from flask import Flask, jsonify, request

# Import API blueprint
from backend.ukg_api import ukg_api

# Create Flask app
app = Flask(__name__)

# Register blueprints
app.register_blueprint(ukg_api)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Root endpoint
@app.route('/')
def index():
    """
    Root endpoint - health check and welcome message.
    """
    return jsonify({
        'status': 'ok',
        'message': 'Universal Knowledge Graph (UKG) System API',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

# Health check endpoint
@app.route('/health')
def health():
    """
    Health check endpoint.
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == "__main__":
    logging.info(f"[{datetime.now()}] Starting Universal Knowledge Graph (UKG) System...")
    
    # Get port from environment or use default
    # Using port 5000 for Flask to avoid conflicts with gunicorn
    port = int(os.environ.get('PORT', 5000))
    
    # Run the application
    app.run(host="0.0.0.0", port=port, debug=True)