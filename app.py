"""
Universal Knowledge Graph (UKG) System - Main Flask Application

This module serves as the main controller for the UKG system.
It provides RESTful API endpoints for interacting with the UKG components,
implements secure authentication, and serves the frontend.
"""

import os
import sys
import json
import datetime
import logging
import uuid
import jwt
from functools import wraps
from typing import Dict, Any, Optional, List, Union, Tuple
from flask import Flask, request, jsonify, g, render_template, redirect, url_for, abort, Response, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.exceptions import NotFound, InternalServerError
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.environ.get('LOG_FILE', 'ukg_system.log'))
    ]
)
logger = logging.getLogger(__name__)

# Define the base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "ukg-dev-key-replace-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///ukg_system.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension, flask-sqlalchemy >= 3.0.x
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Import models after db initialization to avoid circular imports
with app.app_context():
    import models
    db.create_all()
    logger.info("Database tables created")

# Authentication decorator for JWT tokens
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = payload['sub']
            user = models.User.query.get(user_id)
            
            if not user:
                return jsonify({'message': 'User not found'}), 401
            
            g.current_user = user
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

# Authentication decorator for API keys
def api_key_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'message': 'API key is missing'}), 401
        
        key = models.APIKey.query.filter_by(key=api_key).first()
        
        if not key or not key.is_valid():
            return jsonify({'message': 'Invalid API key'}), 401
        
        user = models.User.query.get(key.user_id)
        if not user or not user.is_active:
            return jsonify({'message': 'User is inactive'}), 401
        
        # Check IP address if restrictions are in place
        if key.allowed_ips:
            client_ip = request.remote_addr
            allowed_ips = key.get_allowed_ips()
            
            if client_ip not in allowed_ips:
                return jsonify({'message': 'IP address not allowed'}), 403
        
        # Check origin if restrictions are in place
        if key.allowed_origins:
            origin = request.headers.get('Origin')
            allowed_origins = key.get_allowed_origins()
            
            if origin and origin not in allowed_origins:
                return jsonify({'message': 'Origin not allowed'}), 403
        
        # Update last used timestamp
        key.last_used_at = datetime.datetime.utcnow()
        db.session.commit()
        
        g.current_user = user
        return f(*args, **kwargs)
    
    return decorated

# Combined authentication decorator (token or API key)
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check for API key first
        api_key = request.headers.get('X-API-Key')
        if api_key:
            key = models.APIKey.query.filter_by(key=api_key).first()
            
            if key and key.is_valid():
                user = models.User.query.get(key.user_id)
                if user and user.is_active:
                    g.current_user = user
                    
                    # Update last used timestamp
                    key.last_used_at = datetime.datetime.utcnow()
                    db.session.commit()
                    
                    return f(*args, **kwargs)
        
        # If no valid API key, check for token
        auth_header = request.headers.get('Authorization')
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
                
                try:
                    payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
                    user_id = payload['sub']
                    user = models.User.query.get(user_id)
                    
                    if user and user.is_active:
                        g.current_user = user
                        return f(*args, **kwargs)
                except jwt.ExpiredSignatureError:
                    return jsonify({'message': 'Token has expired'}), 401
                except jwt.InvalidTokenError:
                    return jsonify({'message': 'Invalid token'}), 401
        
        return jsonify({'message': 'Authentication required'}), 401
    
    return decorated

# API Endpoints

@app.route('/api/health')
def health_check():
    """
    Health check endpoint for monitoring systems
    """
    try:
        # Check database connection
        result = db.session.execute(db.text('SELECT 1'))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"
    
    return jsonify({
        "status": "ok" if db_status == "healthy" else "degraded",
        "version": "1.0.0",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "components": {
            "api": "healthy",
            "database": db_status
        }
    })

@app.route('/api/system/status')
@auth_required
def system_status():
    """
    Get the overall system status, active components, and layer statuses
    """
    # Get counts of various entities
    node_count = models.Node.query.count()
    edge_count = models.Edge.query.count()
    algorithm_count = models.KnowledgeAlgorithm.query.count()
    user_count = models.User.query.count()
    simulation_count = models.SimulationSession.query.count()
    
    # Get node distribution by axis
    node_distribution = []
    for i in range(1, 14):
        count = models.Node.query.filter_by(axis_number=i).count()
        node_distribution.append({
            "axis": i,
            "count": count
        })
    
    # Get active simulations
    active_simulations = models.SimulationSession.query.filter(
        models.SimulationSession.status.in_(["running", "pending"])
    ).count()
    
    return jsonify({
        "status": "operational",
        "components": {
            "database": "operational",
            "knowledge_graph": "operational",
            "simulation_engine": "operational",
            "quad_persona_engine": "operational"
        },
        "statistics": {
            "node_count": node_count,
            "edge_count": edge_count,
            "algorithm_count": algorithm_count,
            "user_count": user_count,
            "simulation_count": simulation_count,
            "active_simulations": active_simulations,
            "node_distribution": node_distribution
        },
        "layer_status": {
            "1_entry": "active",
            "2_knowledge_graph": "active",
            "3_research_simulation": "active",
            "4_pov_engine": "active",
            "5_integration": "active",
            "7_agi_system": "active",
            "8_quantum_computer": "active",
            "9_recursive_agi": "active",
            "10_self_awareness": "active"
        }
    })

@app.route('/api/simulation/run', methods=['POST'])
@auth_required
def run_simulation():
    """
    Run a UKG simulation with the provided parameters
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    try:
        # Required parameters
        query = data.get('query')
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        # Optional parameters
        name = data.get('name', f"Simulation {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M')}")
        description = data.get('description')
        confidence_threshold = data.get('confidenceThreshold', 0.85)
        max_layer = data.get('maxLayer', 5)
        refinement_steps = data.get('refinementSteps', 8)
        entropy_sampling = data.get('entropySampling', True)
        
        # Create simulation session
        session_id = str(uuid.uuid4())
        
        simulation = models.SimulationSession(
            session_id=session_id,
            user_id=g.current_user.id,
            name=name,
            description=description,
            parameters={
                "query": query,
                "confidenceThreshold": confidence_threshold,
                "maxLayer": max_layer,
                "refinementSteps": refinement_steps,
                "entropySampling": entropy_sampling
            },
            status="running",
            current_step=0,
            total_steps=refinement_steps,
            started_at=datetime.datetime.utcnow()
        )
        
        db.session.add(simulation)
        db.session.commit()
        
        # In a real implementation, this would start an asynchronous task
        # For now, we'll just return the simulation ID
        
        return jsonify({
            "simulationId": session_id,
            "status": "running",
            "message": "Simulation started successfully",
            "url": f"/api/simulation/{session_id}"
        })
    
    except Exception as e:
        logger.error(f"Error starting simulation: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/simulation/<session_id>')
@auth_required
def get_simulation(session_id):
    """
    Get the status and results of a simulation
    """
    simulation = models.SimulationSession.query.filter_by(session_id=session_id).first()
    
    if not simulation:
        return jsonify({"error": "Simulation not found"}), 404
    
    # Check if the user has access to this simulation
    if simulation.user_id != g.current_user.id and not g.current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403
    
    # Simple simulation logic for demo purposes
    # In a real implementation, this would check the status of the async task
    
    if simulation.status == "running":
        # Update the simulation status based on time elapsed (for demo)
        elapsed = (datetime.datetime.utcnow() - simulation.started_at).total_seconds()
        step_time = elapsed / simulation.total_steps
        
        current_step = min(int(elapsed / step_time), simulation.total_steps)
        
        if current_step >= simulation.total_steps:
            simulation.status = "completed"
            simulation.current_step = simulation.total_steps
            simulation.completed_at = datetime.datetime.utcnow()
            simulation.last_step_at = datetime.datetime.utcnow()
            
            # Generate results based on the query
            query = simulation.parameters.get("query", "")
            
            if "knowledge" in query.lower():
                response = "The Universal Knowledge Graph organizes information across 13 axes, including knowledge domains, sectors, methods, and more. This allows for multi-perspective analysis of complex topics."
                confidence = 0.92
                active_layer = 2
            elif "simulation" in query.lower():
                response = "Simulations in the UKG system use a 10-layer architecture with recursive processing to generate insights based on integrated knowledge across multiple domains."
                confidence = 0.89
                active_layer = 3
            elif "persona" in query.lower() or "expert" in query.lower():
                response = "The Quad Persona Engine creates synthetic experts through 7 component structures (job role, education, certifications, skills, training, career path, related jobs). This allows the system to provide multi-perspective expertise on complex topics."
                confidence = 0.94
                active_layer = 4
            else:
                response = f"I understand your query about '{query}'. The Universal Knowledge Graph integrates multiple perspectives on this topic across knowledge domains, sectors, regulatory frameworks, and compliance requirements."
                confidence = 0.85
                active_layer = 1
            
            simulation.results = {
                "response": response,
                "confidenceScore": confidence,
                "activeLayer": active_layer
            }
        else:
            simulation.current_step = current_step
            simulation.last_step_at = datetime.datetime.utcnow()
        
        db.session.commit()
    
    result = {
        "simulationId": simulation.session_id,
        "name": simulation.name,
        "description": simulation.description,
        "status": simulation.status,
        "progress": {
            "currentStep": simulation.current_step,
            "totalSteps": simulation.total_steps,
            "percentage": round((simulation.current_step / simulation.total_steps) * 100) if simulation.total_steps > 0 else 0
        },
        "timing": {
            "started": simulation.started_at.isoformat() if simulation.started_at else None,
            "completed": simulation.completed_at.isoformat() if simulation.completed_at else None,
            "lastUpdate": simulation.last_step_at.isoformat() if simulation.last_step_at else None
        },
        "parameters": simulation.parameters
    }
    
    if simulation.status == "completed" and simulation.results:
        result["results"] = simulation.results
    
    return jsonify(result)

@app.route('/api/graph')
@auth_required
def get_graph_data():
    """
    Get graph data for visualization
    """
    try:
        # Get filter parameters
        axis = request.args.get('axis', type=int)
        node_type = request.args.get('nodeType')
        limit = request.args.get('limit', 100, type=int)
        
        # Build query for nodes
        node_query = models.Node.query
        
        if axis:
            node_query = node_query.filter_by(axis_number=axis)
        
        if node_type:
            node_query = node_query.filter_by(node_type=node_type)
        
        # Get nodes with limit
        nodes = node_query.limit(limit).all()
        
        # Prepare node data
        node_data = []
        node_ids = []
        
        for node in nodes:
            node_ids.append(node.id)
            node_data.append({
                "id": node.id,
                "label": node.label,
                "axis": node.axis_number,
                "type": node.node_type,
                "size": 5,  # Default size
                "color": get_color_for_axis(node.axis_number)
            })
        
        # Get edges between these nodes
        edges = models.Edge.query.filter(
            models.Edge.source_node_id.in_(node_ids),
            models.Edge.target_node_id.in_(node_ids)
        ).all()
        
        # Prepare edge data
        edge_data = []
        
        for edge in edges:
            edge_data.append({
                "source": edge.source_node_id,
                "target": edge.target_node_id,
                "label": edge.label,
                "value": edge.weight
            })
        
        # Return the graph data
        return jsonify({
            "nodes": node_data,
            "links": edge_data
        })
    
    except Exception as e:
        logger.error(f"Error getting graph data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/logs')
@auth_required
def get_logs():
    """
    Get system logs with filtering
    """
    # Check if user is admin
    if not g.current_user.is_admin:
        return jsonify({"error": "Admin privileges required"}), 403
    
    try:
        # Get filter parameters
        level = request.args.get('level', 'INFO')
        component = request.args.get('component')
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        limit = request.args.get('limit', 100, type=int)
        
        # In a real implementation, this would query the logs from a log store
        # For now, we'll return mock data
        
        log_file = os.environ.get('LOG_FILE', 'ukg_system.log')
        
        if not os.path.exists(log_file):
            return jsonify({"logs": [], "message": "Log file not found"}), 404
        
        # Read the log file and apply filters
        logs = []
        with open(log_file, 'r') as f:
            for line in f:
                logs.append(line.strip())
        
        # Return the logs
        return jsonify({
            "logs": logs[-limit:],
            "count": len(logs),
            "filters": {
                "level": level,
                "component": component,
                "startDate": start_date,
                "endDate": end_date
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting logs: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/settings', methods=['GET', 'POST'])
@auth_required
def manage_settings():
    """
    Get or update system settings
    """
    # Check if user is admin
    if not g.current_user.is_admin:
        return jsonify({"error": "Admin privileges required"}), 403
    
    if request.method == 'GET':
        # Return current settings
        settings = {
            "confidence_threshold": 0.85,
            "max_simulation_layers": 7,
            "refinement_steps": 12,
            "entropy_sampling_enabled": True,
            "quantum_simulation_enabled": False,
            "recursive_processing_enabled": True,
            "max_recursion_depth": 8
        }
        
        return jsonify(settings)
    
    elif request.method == 'POST':
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        try:
            # Update settings
            # In a real implementation, this would update settings in a database
            
            return jsonify({
                "message": "Settings updated successfully",
                "settings": data
            })
        
        except Exception as e:
            logger.error(f"Error updating settings: {str(e)}")
            return jsonify({"error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """
    Authenticate a user and provide a JWT token
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    
    user = models.User.query.filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid username or password"}), 401
    
    # Update last login time
    user.last_login = datetime.datetime.utcnow()
    db.session.commit()
    
    # Generate JWT token
    payload = {
        'sub': user.id,
        'username': user.username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    
    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin
        }
    })

@app.route('/api/query', methods=['POST'])
@auth_required
def process_query():
    """
    Process a knowledge query through the UKG system
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    query = data.get('query')
    
    if not query:
        return jsonify({"error": "Query is required"}), 400
    
    try:
        # Get optional parameters
        confidence_threshold = data.get('confidenceThreshold', 0.85)
        max_layer = data.get('maxLayer', 5)
        
        # Create simulation session
        session_id = str(uuid.uuid4())
        
        simulation = models.SimulationSession(
            session_id=session_id,
            user_id=g.current_user.id,
            name=f"Query {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            parameters={
                "query": query,
                "confidenceThreshold": confidence_threshold,
                "maxLayer": max_layer
            },
            status="pending",
            current_step=0,
            total_steps=8,
            started_at=datetime.datetime.utcnow()
        )
        
        db.session.add(simulation)
        db.session.commit()
        
        # Process the query (simplified for demo)
        simulation.status = "running"
        db.session.commit()
        
        # Generate response based on the query
        if "knowledge" in query.lower():
            response = "The Universal Knowledge Graph organizes information across 13 axes, including knowledge domains, sectors, methods, and more. This allows for multi-perspective analysis of complex topics."
            confidence = 0.92
            active_layer = 2
        elif "simulation" in query.lower():
            response = "Simulations in the UKG system use a 10-layer architecture with recursive processing to generate insights based on integrated knowledge across multiple domains."
            confidence = 0.89
            active_layer = 3
        elif "persona" in query.lower() or "expert" in query.lower():
            response = "The Quad Persona Engine creates synthetic experts through 7 component structures (job role, education, certifications, skills, training, career path, related jobs). This allows the system to provide multi-perspective expertise on complex topics."
            confidence = 0.94
            active_layer = 4
        else:
            response = f"I understand your query about '{query}'. The Universal Knowledge Graph integrates multiple perspectives on this topic across knowledge domains, sectors, regulatory frameworks, and compliance requirements."
            confidence = 0.85
            active_layer = 1
        
        # Update simulation with results
        simulation.status = "completed"
        simulation.current_step = 8
        simulation.total_steps = 8
        simulation.completed_at = datetime.datetime.utcnow()
        simulation.results = {
            "response": response,
            "confidenceScore": confidence,
            "activeLayer": active_layer
        }
        
        db.session.commit()
        
        # Return the response
        return jsonify({
            "query": query,
            "response": response,
            "confidenceScore": confidence,
            "activeLayer": active_layer,
            "simulationId": session_id
        })
    
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/media/generate', methods=['POST'])
@auth_required
def generate_media():
    """
    Generate media (images or videos) based on input prompt
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    prompt = data.get('prompt')
    
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    
    try:
        # In a real implementation, this would call a media generation service
        # For now, we'll return a mock response
        
        return jsonify({
            "message": "Media generation not implemented in demo",
            "prompt": prompt
        })
    
    except Exception as e:
        logger.error(f"Error generating media: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Serve frontend assets

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """
    Serve the React frontend
    """
    # Check if the path is an API route
    if path.startswith('api/'):
        return abort(404)
    
    # Check if the path is a file that exists in the static folder
    static_folder = app.static_folder
    
    # First, try to find the file in the static folder
    static_file_path = os.path.join(static_folder, path) if path else None
    
    if path and os.path.isfile(static_file_path):
        return send_from_directory(static_folder, path)
    
    # If it's not an existing file, check for an HTML template
    template_path = f"{path}.html" if path else "index.html"
    
    try:
        return render_template(template_path)
    except NotFound:
        # If the template doesn't exist, try serving from the templates folder directly
        templates_folder = os.path.join(app.root_path, 'templates')
        template_file_path = os.path.join(templates_folder, template_path)
        
        if os.path.isfile(template_file_path):
            return send_from_directory(templates_folder, template_path)
        
        # If all else fails, serve the index.html template
        return render_template("index.html")

# Error handlers

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({"error": "Not found"}), 404
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    if request.path.startswith('/api/'):
        return jsonify({"error": "Server error"}), 500
    return render_template('errors/500.html'), 500

# Helper functions

def get_color_for_axis(axis_number: int) -> str:
    """Return a color for the given axis number"""
    colors = [
        "#4299E1",  # Axis 1: Knowledge - Blue
        "#48BB78",  # Axis 2: Sectors - Green
        "#ECC94B",  # Axis 3: Domains - Yellow
        "#ED8936",  # Axis 4: Methods - Orange
        "#9F7AEA",  # Axis 5: Contexts - Purple
        "#F56565",  # Axis 6: Problems - Red
        "#38B2AC",  # Axis 7: Solutions - Teal
        "#667EEA",  # Axis 8: Roles - Indigo
        "#F687B3",  # Axis 9: Experts - Pink
        "#805AD5",  # Axis 10: Regulations - Violet
        "#DD6B20",  # Axis 11: Compliance - Dark Orange
        "#1A202C",  # Axis 12: Location - Dark Gray
        "#2C5282",  # Axis 13: Time - Dark Blue
    ]
    
    if axis_number < 1 or axis_number > len(colors):
        return "#A0AEC0"  # Default color
    
    return colors[axis_number - 1]

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)