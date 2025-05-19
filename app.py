
from flask import Flask, render_template, request, jsonify
from backend import create_app
import os
import logging
from config import AppConfig

# Initialize the Flask app with our backend
app = create_app()

# Load configuration
config = AppConfig()

# Import orchestrator (will be initialized in main.py)
from core.app_orchestrator import AppOrchestrator

# Reference to the orchestrator instance - will be set in main.py
orchestrator = None

@app.route('/')
def index():
    """Serve the main application page"""
    logging.info("Rendering index page")
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

@app.route('/api/ukg/simulate', methods=['POST'])
def simulate():
    """Run a UKG simulation with the given query"""
    data = request.json
    
    if not data or 'query' not in data:
        return jsonify({"error": "Missing query parameter"}), 400
    
    # Check if orchestrator is initialized
    if not orchestrator:
        return jsonify({"error": "UKG System not fully initialized"}), 503
    
    query = data['query']
    user_id = data.get('user_id')
    session_id = data.get('session_id')
    simulation_params = data.get('parameters', {})
    
    # Process the request with the orchestrator
    result = orchestrator.process_request(
        user_query=query,
        user_id=user_id,
        session_id=session_id,
        simulation_params=simulation_params
    )
    
    return jsonify(result)

@app.route('/api/ukg/memory/<session_id>', methods=['GET'])
def get_session_memory(session_id):
    """Get memory entries for a session"""
    # Check if orchestrator is initialized
    if not orchestrator:
        return jsonify({"error": "UKG System not fully initialized"}), 503
    
    memory_entries = orchestrator.get_session_memory(session_id)
    return jsonify({"session_id": session_id, "memory_entries": memory_entries})

@app.route('/api/ukg/memory/<session_id>', methods=['DELETE'])
def clear_session(session_id):
    """Clear all memory for a session"""
    # Check if orchestrator is initialized
    if not orchestrator:
        return jsonify({"error": "UKG System not fully initialized"}), 503
    
    result = orchestrator.clear_session(session_id)
    return jsonify(result)

# API routes are now handled by the backend blueprints

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
