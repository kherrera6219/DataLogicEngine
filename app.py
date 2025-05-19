import os
import logging
from flask import Flask, jsonify, request, session, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Define base model class for SQLAlchemy
class Base(DeclarativeBase):
    pass

# Initialize Flask application and SQLAlchemy
db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

# Configure application
app.secret_key = os.environ.get("SESSION_SECRET", "ukg_development_secret_key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions
db.init_app(app)

# Import models and create tables
with app.app_context():
    import models
    db.create_all()
    logging.info(f"[{datetime.now()}] Database tables created")

# Import API blueprint
from backend.ukg_api import ukg_api

# Register API blueprint
app.register_blueprint(ukg_api)

# Define global orchestrator for API access
orchestrator = None

# Application routes

@app.route('/')
def index():
    """Serve the main application page"""
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    system_health = {
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    }
    
    # Add orchestrator health if available
    if orchestrator:
        system_health.update(orchestrator.get_system_health())
        
    return jsonify(system_health)

@app.route('/api/simulate', methods=['POST'])
def simulate():
    """Run a UKG simulation with the given query"""
    if not request.json or 'query' not in request.json:
        return jsonify({
            'status': 'error',
            'message': 'Missing required parameter: query',
            'timestamp': datetime.now().isoformat()
        }), 400
    
    query = request.json.get('query')
    location_uids = request.json.get('location_uids')
    target_confidence = request.json.get('target_confidence', 0.85)
    
    # Create a session ID if not exists
    if 'session_id' not in session:
        session['session_id'] = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}_{os.urandom(4).hex()}"
    
    if not orchestrator:
        return jsonify({
            'status': 'error',
            'message': 'UKG system not initialized',
            'timestamp': datetime.now().isoformat()
        }), 503
    
    # Run simulation
    result = orchestrator.run_simulation(
        query_text=query,
        location_uids=location_uids,
        target_confidence=target_confidence,
        context_data={'web_session_id': session['session_id']}
    )
    
    return jsonify(result)

@app.route('/api/memory/<session_id>', methods=['GET'])
def get_session_memory(session_id):
    """Get memory entries for a session"""
    if not orchestrator:
        return jsonify({
            'status': 'error',
            'message': 'UKG system not initialized',
            'timestamp': datetime.now().isoformat()
        }), 503
    
    result = orchestrator.get_session_info(session_id)
    return jsonify(result)

@app.route('/api/memory/<session_id>/clear', methods=['POST'])
def clear_session(session_id):
    """Clear all memory for a session"""
    if not orchestrator or not orchestrator.memory_manager:
        return jsonify({
            'status': 'error',
            'message': 'Memory manager not available',
            'timestamp': datetime.now().isoformat()
        }), 503
    
    try:
        orchestrator.memory_manager.clear_session_memory(session_id)
        return jsonify({
            'status': 'success',
            'message': f'Session memory cleared for {session_id}',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error clearing session memory: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500