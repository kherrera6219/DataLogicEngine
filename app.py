"""
Universal Knowledge Graph (UKG) System - Main Flask Application

This module serves as the main controller for the UKG system.
It provides RESTful API endpoints for interacting with the UKG components,
implements secure authentication, and serves the frontend.
"""

import os
import logging
import json
import uuid
import datetime
import jwt
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, Response, g
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

# Import configuration
from config import get_config

# Configure logging
logger = logging.getLogger(__name__)

# Create Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize Flask app
app = Flask(__name__, static_folder='static')
app.config.from_object(get_config())
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Enable CORS
CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})

# Initialize database
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Import models after initializing db to avoid circular imports
with app.app_context():
    from models import User, APIKey, Node, Edge, KnowledgeAlgorithm, SimulationSession
    db.create_all()

# API token authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if token is in headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        # Check if token is in request arguments
        if not token and 'token' in request.args:
            token = request.args.get('token')
        
        # Check if token is in JSON body
        if not token and request.is_json:
            data = request.get_json()
            if 'token' in data:
                token = data['token']
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            # Decode the token
            payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            g.user_id = payload['sub']
            g.is_admin = payload.get('admin', False)
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

# API key authentication decorator
def api_key_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = None
        
        # Check if API key is in headers
        if 'X-API-Key' in request.headers:
            api_key = request.headers['X-API-Key']
        
        # Check if API key is in request arguments
        if not api_key and 'api_key' in request.args:
            api_key = request.args.get('api_key')
        
        if not api_key:
            return jsonify({'message': 'API key is missing'}), 401
        
        try:
            # Check if API key exists and is valid
            with app.app_context():
                key = APIKey.query.filter_by(key=api_key, is_active=True).first()
                
                if not key:
                    return jsonify({'message': 'Invalid API key'}), 401
                
                if key.expires_at and key.expires_at < datetime.datetime.utcnow():
                    return jsonify({'message': 'API key has expired'}), 401
                
                # Store API key info in g for later use
                g.api_key = key
                g.user_id = key.user_id
        except Exception as e:
            logger.error(f"API key validation error: {str(e)}")
            return jsonify({'message': 'API key validation failed'}), 500
        
        return f(*args, **kwargs)
    
    return decorated

# Either token or API key required
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        api_key = None
        
        # Check for token
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        # Check for API key
        if 'X-API-Key' in request.headers:
            api_key = request.headers['X-API-Key']
        
        if not token and not api_key:
            return jsonify({'message': 'Authentication required'}), 401
        
        if token:
            try:
                # Decode the token
                payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
                g.user_id = payload['sub']
                g.is_admin = payload.get('admin', False)
                g.auth_method = 'token'
            except jwt.ExpiredSignatureError:
                return jsonify({'message': 'Token has expired'}), 401
            except jwt.InvalidTokenError:
                # If token is invalid, try API key if present
                if not api_key:
                    return jsonify({'message': 'Invalid token'}), 401
                # Else continue to API key validation
        
        if not token or (token and not hasattr(g, 'user_id')):
            if not api_key:
                return jsonify({'message': 'Authentication required'}), 401
            
            try:
                # Check if API key exists and is valid
                with app.app_context():
                    key = APIKey.query.filter_by(key=api_key, is_active=True).first()
                    
                    if not key:
                        return jsonify({'message': 'Invalid API key'}), 401
                    
                    if key.expires_at and key.expires_at < datetime.datetime.utcnow():
                        return jsonify({'message': 'API key has expired'}), 401
                    
                    # Store API key info in g for later use
                    g.api_key = key
                    g.user_id = key.user_id
                    g.is_admin = key.is_admin
                    g.auth_method = 'api_key'
            except Exception as e:
                logger.error(f"API key validation error: {str(e)}")
                return jsonify({'message': 'Authentication failed'}), 500
        
        return f(*args, **kwargs)
    
    return decorated

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring systems
    """
    # Check database connection
    try:
        db.session.execute('SELECT 1')
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"
    
    response = {
        "status": "ok" if db_status == "healthy" else "degraded",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "version": app.config['APP_VERSION'],
        "components": {
            "database": db_status,
            "api": "healthy",
            "ukg_system": "healthy"
        }
    }
    
    status_code = 200 if response["status"] == "ok" else 500
    return jsonify(response), status_code

# System status endpoint
@app.route('/api/status', methods=['GET'])
@auth_required
def system_status():
    """
    Get the overall system status, active components, and layer statuses
    """
    try:
        # This would be integrated with UKG components in a real implementation
        # For now, we'll return a simulated response
        status = {
            "system": {
                "status": "operational",
                "uptime": "14d 3h 27m",
                "version": app.config['APP_VERSION'],
                "environment": os.environ.get("FLASK_ENV", "development"),
                "activeUsers": 12,
                "totalNodes": 15782,
                "totalEdges": 47291
            },
            "layers": {
                "layer1": {"status": "active", "confidence": 0.98},
                "layer2": {"status": "active", "confidence": 0.95},
                "layer3": {"status": "active", "confidence": 0.92},
                "layer4": {"status": "active", "confidence": 0.89},
                "layer5": {"status": "active", "confidence": 0.87},
                "layer7": {"status": "active", "confidence": 0.85},
                "layer8": {"status": "standby", "confidence": 0.0},
                "layer9": {"status": "standby", "confidence": 0.0},
                "layer10": {"status": "monitoring", "confidence": 0.95}
            },
            "components": {
                "quadPersona": {"status": "active", "lastActivity": "2 minutes ago"},
                "knowledgeAlgorithms": {"status": "active", "availableCount": 38, "runningCount": 2},
                "simulationEngine": {"status": "ready", "activeSimulations": 0},
                "gatekeeperAgent": {"status": "monitoring", "threshold": app.config['DEFAULT_CONFIDENCE_THRESHOLD']},
                "mediaGeneration": {"status": "ready", "availableModels": ["dall-e-3", "midjourney-turbo"]}
            },
            "resources": {
                "cpu": {"usage": "42%", "temperature": "normal"},
                "memory": {"usage": "3.2GB / 8GB", "percentage": 40},
                "storage": {"usage": "28GB / 100GB", "percentage": 28}
            }
        }
        
        # Add additional information for admin users
        if hasattr(g, 'is_admin') and g.is_admin:
            status["admin"] = {
                "databaseSize": "487MB",
                "lastBackup": "2023-05-18T14:30:00Z",
                "activeApiKeys": 8,
                "logSize": "24MB"
            }
        
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return jsonify({"error": "Failed to get system status"}), 500

# Run simulation endpoint
@app.route('/api/simulation/run', methods=['POST'])
@auth_required
def run_simulation():
    """
    Run a UKG simulation with the provided parameters
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required parameters
        required_params = ['query', 'confidenceThreshold', 'maxLayer']
        for param in required_params:
            if param not in data:
                return jsonify({"error": f"Missing required parameter: {param}"}), 400
        
        # Extract parameters
        query = data['query']
        confidence_threshold = float(data['confidenceThreshold'])
        max_layer = int(data['maxLayer'])
        refinement_steps = int(data.get('refinementSteps', app.config['DEFAULT_REFINEMENT_STEPS']))
        
        # Validate parameter values
        if confidence_threshold < 0.5 or confidence_threshold > 0.99:
            return jsonify({"error": "confidenceThreshold must be between 0.5 and 0.99"}), 400
        
        if max_layer < 0 or max_layer > app.config['MAX_SIMULATION_LAYERS']:
            return jsonify({"error": f"maxLayer must be between 0 and {app.config['MAX_SIMULATION_LAYERS']}"}), 400
        
        if refinement_steps < 1 or refinement_steps > 24:
            return jsonify({"error": "refinementSteps must be between 1 and 24"}), 400
        
        # Create a simulation session
        session_id = str(uuid.uuid4())
        simulation_session = SimulationSession(
            uid=session_id,
            session_id=session_id,
            name=data.get('name', f"Simulation {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"),
            parameters={
                "query": query,
                "confidenceThreshold": confidence_threshold,
                "maxLayer": max_layer,
                "refinementSteps": refinement_steps,
                "additionalParams": data.get('additionalParams', {})
            },
            status="running",
            current_step=0,
            started_at=datetime.datetime.utcnow()
        )
        
        db.session.add(simulation_session)
        db.session.commit()
        
        # This would call the actual UKG simulation components in a real implementation
        # For now, we'll return a simulated response
        
        # Simulate processing time based on complexity
        processing_time = 120 + (max_layer * 50) + (refinement_steps * 10)  # milliseconds
        
        # Simulate result data
        result = {
            "simulationId": session_id,
            "query": query,
            "response": f"This is a simulated response to the query: {query}",
            "confidenceScore": 0.92,
            "activeLayer": min(max_layer, 4),  # Simulate that layer 4 was sufficient
            "refinementSteps": refinement_steps,
            "refinementPasses": refinement_steps,
            "elapsedTime": processing_time,
            "insights": [
                {"type": "knowledge", "text": "Knowledge insight 1", "confidence": 0.95},
                {"type": "sector", "text": "Sector insight 1", "confidence": 0.88},
                {"type": "regulatory", "text": "Regulatory insight 1", "confidence": 0.91},
                {"type": "compliance", "text": "Compliance insight 1", "confidence": 0.89}
            ],
            "graphData": {
                "nodes": [
                    {"id": "n1", "label": "Query", "axis_number": 1, "size": 10},
                    {"id": "n2", "label": "Knowledge Node 1", "axis_number": 1, "size": 8},
                    {"id": "n3", "label": "Sector Node 1", "axis_number": 2, "size": 8},
                    {"id": "n4", "label": "Domain Node 1", "axis_number": 3, "size": 8},
                    {"id": "n5", "label": "Regulatory Node 1", "axis_number": 10, "size": 8}
                ],
                "links": [
                    {"source": "n1", "target": "n2", "label": "relates to", "value": 1},
                    {"source": "n1", "target": "n3", "label": "relates to", "value": 1},
                    {"source": "n2", "target": "n4", "label": "belongs to", "value": 1},
                    {"source": "n3", "target": "n5", "label": "governed by", "value": 1}
                ]
            }
        }
        
        # Update simulation session with results
        simulation_session.status = "completed"
        simulation_session.current_step = refinement_steps
        simulation_session.completed_at = datetime.datetime.utcnow()
        simulation_session.last_step_at = datetime.datetime.utcnow()
        simulation_session.results = result
        db.session.commit()
        
        return jsonify(result), 200
    
    except ValueError as ve:
        logger.error(f"Validation error in simulation: {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    
    except Exception as e:
        logger.error(f"Error running simulation: {str(e)}")
        return jsonify({"error": "Failed to run simulation"}), 500

# Get graph data endpoint
@app.route('/api/graph', methods=['GET'])
@auth_required
def get_graph_data():
    """
    Get graph data for visualization
    """
    try:
        # Get query parameters
        axis = request.args.get('axis')
        node_type = request.args.get('nodeType')
        limit = request.args.get('limit', 100)
        
        # Validate parameters
        if axis and not axis.isdigit():
            return jsonify({"error": "axis must be a number"}), 400
        
        if limit and not str(limit).isdigit():
            return jsonify({"error": "limit must be a number"}), 400
        
        limit = int(limit)
        if limit < 1 or limit > 1000:
            return jsonify({"error": "limit must be between 1 and 1000"}), 400
        
        # This would query the actual UKG graph database in a real implementation
        # For now, we'll return a simulated response
        
        # Simulate graph data with 13 axes
        nodes = []
        links = []
        
        # Create nodes for each axis
        for i in range(1, 14):
            # Skip if filtering by axis
            if axis and int(axis) != i:
                continue
                
            # Node type name based on axis number
            axis_type = ["Knowledge", "Sector", "Domain", "Method", "Context", 
                         "Problem", "Solution", "Role", "Expert", "Regulation", 
                         "Compliance", "Location", "Time"][i-1]
            
            # Skip if filtering by node type
            if node_type and node_type.lower() != axis_type.lower():
                continue
                
            # Create nodes for this axis
            for j in range(1, min(limit // 13 + 1, 20)):  # Up to ~20 nodes per axis
                node_id = f"n{i}_{j}"
                node = {
                    "id": node_id,
                    "label": f"{axis_type} {j}",
                    "description": f"This is a {axis_type.lower()} node example.",
                    "axis_number": i,
                    "size": 8,
                    "value": 1,
                    "attributes": {
                        "created": datetime.datetime.utcnow().isoformat(),
                        "confidence": 0.85 + (j / 100)
                    }
                }
                nodes.append(node)
                
                # Create links between nodes in same axis
                if j > 1:
                    links.append({
                        "source": f"n{i}_{j-1}",
                        "target": node_id,
                        "label": "related",
                        "value": 1,
                        "directed": True,
                        "attributes": {
                            "confidence": 0.8 + (j / 100)
                        }
                    })
        
        # Create cross-axis links
        for i in range(1, 13):
            for j in range(1, min(limit // 13 + 1, 10)):
                # Skip if either source or target axis is filtered out
                if axis and (int(axis) != i and int(axis) != i+1):
                    continue
                    
                source_id = f"n{i}_{j}"
                target_id = f"n{i+1}_{j}"
                
                # Check if both nodes exist (they might have been filtered out)
                source_exists = any(n["id"] == source_id for n in nodes)
                target_exists = any(n["id"] == target_id for n in nodes)
                
                if source_exists and target_exists:
                    links.append({
                        "source": source_id,
                        "target": target_id,
                        "label": "influences",
                        "value": 1,
                        "directed": True,
                        "attributes": {
                            "confidence": 0.75 + (j / 100)
                        }
                    })
        
        graph_data = {
            "nodes": nodes,
            "links": links
        }
        
        return jsonify(graph_data), 200
    
    except ValueError as ve:
        logger.error(f"Validation error in graph data: {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    
    except Exception as e:
        logger.error(f"Error getting graph data: {str(e)}")
        return jsonify({"error": "Failed to get graph data"}), 500

# Get logs endpoint
@app.route('/api/logs', methods=['GET'])
@auth_required
def get_logs():
    """
    Get system logs with filtering
    """
    try:
        # Check admin permission for logs
        if not hasattr(g, 'is_admin') or not g.is_admin:
            return jsonify({"error": "Unauthorized access to logs"}), 403
        
        # Get query parameters
        level = request.args.get('level', 'INFO').upper()
        limit = request.args.get('limit', 100)
        component = request.args.get('component')
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        
        # Validate parameters
        if level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            return jsonify({"error": "Invalid log level"}), 400
        
        if limit and not str(limit).isdigit():
            return jsonify({"error": "limit must be a number"}), 400
        
        limit = int(limit)
        if limit < 1 or limit > 1000:
            return jsonify({"error": "limit must be between 1 and 1000"}), 400
        
        # This would query the actual log storage in a real implementation
        # For now, we'll return simulated logs
        
        # Simulate log entries
        logs = []
        log_components = ["system", "api", "database", "quad_persona", "simulation", "gatekeeper"]
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        log_level_indices = {level: i for i, level in enumerate(log_levels)}
        
        # Filter by minimum log level
        min_level_index = log_level_indices[level]
        
        # Generate simulated logs
        for i in range(limit):
            log_level = log_levels[max(min_level_index, min(4, i % 5))]
            log_component = component if component in log_components else log_components[i % len(log_components)]
            
            # Skip if filtering by component
            if component and log_component != component:
                continue
                
            # Create log entry
            timestamp = datetime.datetime.utcnow() - datetime.timedelta(minutes=i*5)
            
            # Skip if outside date range
            if start_date:
                try:
                    start_datetime = datetime.datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    if timestamp < start_datetime:
                        continue
                except ValueError:
                    pass
                    
            if end_date:
                try:
                    end_datetime = datetime.datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    if timestamp > end_datetime:
                        continue
                except ValueError:
                    pass
            
            log_entry = {
                "timestamp": timestamp.isoformat(),
                "level": log_level,
                "component": log_component,
                "message": f"Simulated {log_level.lower()} log message from {log_component}",
                "details": {
                    "requestId": str(uuid.uuid4()),
                    "userId": f"user_{i % 10 + 1}",
                    "action": "query" if i % 3 == 0 else "simulation" if i % 3 == 1 else "system"
                }
            }
            
            logs.append(log_entry)
        
        return jsonify(logs), 200
    
    except ValueError as ve:
        logger.error(f"Validation error in logs: {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    
    except Exception as e:
        logger.error(f"Error getting logs: {str(e)}")
        return jsonify({"error": "Failed to get logs"}), 500

# Manage settings endpoint
@app.route('/api/settings', methods=['GET', 'PUT'])
@auth_required
def manage_settings():
    """
    Get or update system settings
    """
    try:
        # Check admin permission for updating settings
        if request.method == 'PUT' and (not hasattr(g, 'is_admin') or not g.is_admin):
            return jsonify({"error": "Unauthorized access to update settings"}), 403
        
        if request.method == 'GET':
            # Return current settings
            settings = {
                "ukg": {
                    "confidenceThreshold": app.config['DEFAULT_CONFIDENCE_THRESHOLD'],
                    "maxSimulationLayers": app.config['MAX_SIMULATION_LAYERS'],
                    "defaultRefinementSteps": app.config['DEFAULT_REFINEMENT_STEPS'],
                    "entropySamplingEnabled": app.config['ENTROPY_SAMPLING_ENABLED'],
                    "quantumSimulationEnabled": app.config['QUANTUM_SIMULATION_ENABLED'],
                    "recursiveProcessingEnabled": app.config['RECURSIVE_PROCESSING_ENABLED'],
                    "maxRecursionDepth": app.config['MAX_RECURSION_DEPTH'],
                    "memoryCacheSize": app.config['MEMORY_CACHE_SIZE']
                },
                "system": {
                    "logLevel": app.config['LOG_LEVEL'],
                    "corsOrigins": app.config['CORS_ORIGINS'],
                    "sessionExpiryMinutes": app.config['JWT_ACCESS_TOKEN_EXPIRES'] // 60
                }
            }
            
            return jsonify(settings), 200
        
        elif request.method == 'PUT':
            # Update settings
            data = request.get_json()
            
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            # Update config based on provided settings
            if 'ukg' in data:
                ukg_settings = data['ukg']
                
                if 'confidenceThreshold' in ukg_settings:
                    threshold = float(ukg_settings['confidenceThreshold'])
                    if threshold < 0.5 or threshold > 0.99:
                        return jsonify({"error": "confidenceThreshold must be between 0.5 and 0.99"}), 400
                    app.config['DEFAULT_CONFIDENCE_THRESHOLD'] = threshold
                
                if 'maxSimulationLayers' in ukg_settings:
                    layers = int(ukg_settings['maxSimulationLayers'])
                    if layers < 1 or layers > 10:
                        return jsonify({"error": "maxSimulationLayers must be between 1 and 10"}), 400
                    app.config['MAX_SIMULATION_LAYERS'] = layers
                
                if 'defaultRefinementSteps' in ukg_settings:
                    steps = int(ukg_settings['defaultRefinementSteps'])
                    if steps < 1 or steps > 24:
                        return jsonify({"error": "defaultRefinementSteps must be between 1 and 24"}), 400
                    app.config['DEFAULT_REFINEMENT_STEPS'] = steps
                
                if 'entropySamplingEnabled' in ukg_settings:
                    app.config['ENTROPY_SAMPLING_ENABLED'] = bool(ukg_settings['entropySamplingEnabled'])
                
                if 'quantumSimulationEnabled' in ukg_settings:
                    app.config['QUANTUM_SIMULATION_ENABLED'] = bool(ukg_settings['quantumSimulationEnabled'])
                
                if 'recursiveProcessingEnabled' in ukg_settings:
                    app.config['RECURSIVE_PROCESSING_ENABLED'] = bool(ukg_settings['recursiveProcessingEnabled'])
                
                if 'maxRecursionDepth' in ukg_settings:
                    depth = int(ukg_settings['maxRecursionDepth'])
                    if depth < 1 or depth > 12:
                        return jsonify({"error": "maxRecursionDepth must be between 1 and 12"}), 400
                    app.config['MAX_RECURSION_DEPTH'] = depth
                
                if 'memoryCacheSize' in ukg_settings:
                    cache_size = int(ukg_settings['memoryCacheSize'])
                    if cache_size < 512 or cache_size > 16384:
                        return jsonify({"error": "memoryCacheSize must be between 512 and 16384"}), 400
                    app.config['MEMORY_CACHE_SIZE'] = cache_size
            
            if 'system' in data:
                system_settings = data['system']
                
                if 'logLevel' in system_settings:
                    log_level = system_settings['logLevel'].upper()
                    if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                        return jsonify({"error": "Invalid log level"}), 400
                    app.config['LOG_LEVEL'] = log_level
                    
                    # Update logger levels
                    root_logger = logging.getLogger()
                    root_logger.setLevel(getattr(logging, log_level))
                    for handler in root_logger.handlers:
                        handler.setLevel(getattr(logging, log_level))
                
                if 'sessionExpiryMinutes' in system_settings:
                    minutes = int(system_settings['sessionExpiryMinutes'])
                    if minutes < 5 or minutes > 1440:  # 5 min to 24 hours
                        return jsonify({"error": "sessionExpiryMinutes must be between 5 and 1440"}), 400
                    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = minutes * 60
            
            # Return updated settings
            settings = {
                "ukg": {
                    "confidenceThreshold": app.config['DEFAULT_CONFIDENCE_THRESHOLD'],
                    "maxSimulationLayers": app.config['MAX_SIMULATION_LAYERS'],
                    "defaultRefinementSteps": app.config['DEFAULT_REFINEMENT_STEPS'],
                    "entropySamplingEnabled": app.config['ENTROPY_SAMPLING_ENABLED'],
                    "quantumSimulationEnabled": app.config['QUANTUM_SIMULATION_ENABLED'],
                    "recursiveProcessingEnabled": app.config['RECURSIVE_PROCESSING_ENABLED'],
                    "maxRecursionDepth": app.config['MAX_RECURSION_DEPTH'],
                    "memoryCacheSize": app.config['MEMORY_CACHE_SIZE']
                },
                "system": {
                    "logLevel": app.config['LOG_LEVEL'],
                    "corsOrigins": app.config['CORS_ORIGINS'],
                    "sessionExpiryMinutes": app.config['JWT_ACCESS_TOKEN_EXPIRES'] // 60
                }
            }
            
            return jsonify(settings), 200
    
    except ValueError as ve:
        logger.error(f"Validation error in settings: {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    
    except Exception as e:
        logger.error(f"Error managing settings: {str(e)}")
        return jsonify({"error": "Failed to manage settings"}), 500

# Login endpoint
@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    Authenticate a user and provide a JWT token
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Missing username or password"}), 400
        
        # Check if user exists
        user = User.query.filter_by(username=username).first()
        
        if not user:
            # Use consistent error messages for security
            return jsonify({"error": "Invalid credentials"}), 401
        
        if not user.is_active:
            return jsonify({"error": "Account is disabled"}), 401
        
        # Check password
        if not user.check_password(password):
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Generate JWT token
        exp = datetime.datetime.utcnow() + datetime.timedelta(seconds=app.config['JWT_ACCESS_TOKEN_EXPIRES'])
        payload = {
            "sub": str(user.id),
            "name": user.username,
            "admin": user.is_admin,
            "exp": exp
        }
        
        token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')
        
        # Update last login timestamp
        user.last_login = datetime.datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "token": token,
            "expires": exp.isoformat(),
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "isAdmin": user.is_admin,
                "firstName": user.first_name,
                "lastName": user.last_name
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"error": "Authentication failed"}), 500

# Process query endpoint
@app.route('/api/query', methods=['POST'])
@auth_required
def process_query():
    """
    Process a knowledge query through the UKG system
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required parameters
        if 'query' not in data:
            return jsonify({"error": "Missing required parameter: query"}), 400
        
        # Extract parameters
        query = data['query']
        confidence_threshold = float(data.get('confidenceThreshold', app.config['DEFAULT_CONFIDENCE_THRESHOLD']))
        max_layer = int(data.get('maxLayer', app.config['MAX_SIMULATION_LAYERS']))
        refinement_steps = int(data.get('refinementSteps', app.config['DEFAULT_REFINEMENT_STEPS']))
        include_graph = bool(data.get('includeGraph', False))
        
        # Validate parameter values
        if confidence_threshold < 0.5 or confidence_threshold > 0.99:
            return jsonify({"error": "confidenceThreshold must be between 0.5 and 0.99"}), 400
        
        if max_layer < 0 or max_layer > app.config['MAX_SIMULATION_LAYERS']:
            return jsonify({"error": f"maxLayer must be between 0 and {app.config['MAX_SIMULATION_LAYERS']}"}), 400
        
        if refinement_steps < 1 or refinement_steps > 24:
            return jsonify({"error": "refinementSteps must be between 1 and 24"}), 400
        
        # This would call the actual UKG processing components in a real implementation
        # For now, we'll return a simulated response
        
        # Simulate processing time based on complexity
        processing_time = 80 + (max_layer * 30) + (refinement_steps * 5)  # milliseconds
        
        # Simulate response generation
        response = f"This is a simulated response to the query: {query}"
        
        # Simulate active layer based on query complexity
        active_layer = min(max_layer, max(1, len(query) % 5 + 1))
        
        # Create response object
        result = {
            "query": query,
            "response": response,
            "confidenceScore": min(0.99, max(0.75, 0.85 + (active_layer * 0.02))),
            "activeLayer": active_layer,
            "elapsedTime": processing_time
        }
        
        # Add graph data if requested
        if include_graph:
            # Simplified graph for the query
            result["graphData"] = {
                "nodes": [
                    {"id": "query", "label": "Query", "axis_number": 1, "size": 10},
                    {"id": "k1", "label": "Knowledge 1", "axis_number": 1, "size": 7},
                    {"id": "k2", "label": "Knowledge 2", "axis_number": 1, "size": 7},
                    {"id": "s1", "label": "Sector 1", "axis_number": 2, "size": 7}
                ],
                "links": [
                    {"source": "query", "target": "k1", "label": "references", "value": 1},
                    {"source": "query", "target": "k2", "label": "references", "value": 1},
                    {"source": "k1", "target": "s1", "label": "belongs to", "value": 1}
                ]
            }
        
        return jsonify(result), 200
    
    except ValueError as ve:
        logger.error(f"Validation error in query: {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return jsonify({"error": "Failed to process query"}), 500

# Generate media endpoint
@app.route('/api/media/generate', methods=['POST'])
@auth_required
def generate_media():
    """
    Generate media (images or videos) based on input prompt
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required parameters
        if 'prompt' not in data:
            return jsonify({"error": "Missing required parameter: prompt"}), 400
        
        # Extract parameters
        prompt = data['prompt']
        media_type = data.get('type', 'image')
        model = data.get('model', 'dall-e-3')
        
        # Validate parameters
        if media_type not in ['image', 'video']:
            return jsonify({"error": "type must be either 'image' or 'video'"}), 400
        
        if model not in ['dall-e-3', 'midjourney-turbo', 'stable-diffusion-xl']:
            return jsonify({"error": "Unsupported model"}), 400
        
        # This would call the actual media generation service in a real implementation
        # For now, we'll return a simulated response
        
        # Generate a unique ID for the media
        media_id = str(uuid.uuid4())
        
        # Simulate media generation
        if media_type == 'image':
            # Simulate image generation
            result = {
                "id": media_id,
                "type": "image",
                "model": model,
                "prompt": prompt,
                "url": f"https://example.com/media/images/{media_id}.png",
                "width": 1024,
                "height": 1024,
                "created": datetime.datetime.utcnow().isoformat()
            }
        else:
            # Simulate video generation
            result = {
                "id": media_id,
                "type": "video",
                "model": model,
                "prompt": prompt,
                "url": f"https://example.com/media/videos/{media_id}.mp4",
                "duration": 10.5,  # seconds
                "created": datetime.datetime.utcnow().isoformat()
            }
        
        return jsonify(result), 200
    
    except ValueError as ve:
        logger.error(f"Validation error in media generation: {str(ve)}")
        return jsonify({"error": str(ve)}), 400
    
    except Exception as e:
        logger.error(f"Error generating media: {str(e)}")
        return jsonify({"error": "Failed to generate media"}), 500

# Serve static frontend files
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """
    Serve the React frontend
    """
    # Serve index.html for all routes (for React router)
    if path and '.' in path:
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# Error handlers
@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({"error": "Endpoint not found"}), 404
    else:
        return send_from_directory(app.static_folder, 'index.html')

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors"""
    logger.error(f"Server error: {str(e)}")
    return jsonify({"error": "Internal server error"}), 500