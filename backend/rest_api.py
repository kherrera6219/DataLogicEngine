
"""
Universal Knowledge Graph (UKG) System - REST API

This module provides standardized REST API endpoints for the UKG system.
All endpoints follow RESTful conventions and return consistent JSON responses.
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import uuid
import logging
from backend.middleware import api_response

# Set up logging
logger = logging.getLogger(__name__)

# Create Blueprint for REST API
rest_api = Blueprint('rest_api', __name__, url_prefix='/api/v1')

# Standard response formatters
def success_response(data, message="Operation successful", status_code=200):
    """Format a standard success response."""
    response = {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    return jsonify(response), status_code

def error_response(message, error_code=None, status_code=400):
    """Format a standard error response."""
    response = {
        "success": False,
        "message": message,
        "error_code": error_code,
        "timestamp": datetime.utcnow().isoformat()
    }
    return jsonify(response), status_code

# API Health endpoint
@rest_api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for the API."""
    return success_response({
        "status": "healthy",
        "service": "UKG REST API",
        "version": "1.0.0"
    })

# Knowledge Graph endpoints
@rest_api.route('/graph/stats', methods=['GET'])
def get_graph_stats():
    """Get statistics about the knowledge graph."""
    try:
        graph_manager = current_app.config.get('GRAPH_MANAGER')
        if not graph_manager:
            return error_response("Graph manager not initialized", "GRAPH_NOT_INIT", 500)
        
        stats = graph_manager.get_statistics()
        return success_response(stats)
    except Exception as e:
        logger.error(f"Error getting graph stats: {str(e)}")
        return error_response(f"Error getting graph stats: {str(e)}", "INTERNAL_ERROR", 500)

# Pillar Level endpoints
@rest_api.route('/pillars', methods=['GET'])
def get_pillars():
    """Get all pillar levels."""
    try:
        from models import PillarLevel
        pillars = PillarLevel.query.all()
        return success_response([pillar.to_dict() for pillar in pillars])
    except Exception as e:
        logger.error(f"Error getting pillar levels: {str(e)}")
        return error_response(f"Error getting pillar levels: {str(e)}", "DB_ERROR", 500)

@rest_api.route('/pillars/<pillar_id>', methods=['GET'])
def get_pillar(pillar_id):
    """Get a specific pillar level."""
    try:
        from models import PillarLevel
        pillar = PillarLevel.query.filter_by(pillar_id=pillar_id).first()
        if not pillar:
            return error_response(f"Pillar level with ID {pillar_id} not found", "NOT_FOUND", 404)
        return success_response(pillar.to_dict())
    except Exception as e:
        logger.error(f"Error getting pillar level: {str(e)}")
        return error_response(f"Error getting pillar level: {str(e)}", "DB_ERROR", 500)

@rest_api.route('/pillars', methods=['POST'])
def create_pillar():
    """Create a new pillar level."""
    try:
        data = request.json
        if not data:
            return error_response("No data provided", "INVALID_REQUEST", 400)
        
        # Validate required fields
        required_fields = ['pillar_id', 'name']
        for field in required_fields:
            if field not in data:
                return error_response(f"Missing required field: {field}", "MISSING_FIELD", 400)
        
        from models import PillarLevel
        from app import db
        
        # Check if pillar level already exists
        existing = PillarLevel.query.filter_by(pillar_id=data['pillar_id']).first()
        if existing:
            return error_response(f"Pillar level with ID {data['pillar_id']} already exists", "ALREADY_EXISTS", 409)
        
        # Create new pillar level
        new_pillar = PillarLevel(
            uid=str(uuid.uuid4()),
            pillar_id=data['pillar_id'],
            name=data['name'],
            description=data.get('description'),
            sublevels=data.get('sublevels')
        )
        
        db.session.add(new_pillar)
        
        try:
            db.session.commit()
            return success_response(new_pillar.to_dict(), "Pillar level created successfully", 201)
        except Exception as e:
            db.session.rollback()
            return error_response(f"Database error: {str(e)}", "DB_COMMIT_ERROR", 500)
    except Exception as e:
        logger.error(f"Error creating pillar level: {str(e)}")
        return error_response(f"Error creating pillar level: {str(e)}", "INTERNAL_ERROR", 500)

# Sector endpoints
@rest_api.route('/sectors', methods=['GET'])
def get_sectors():
    """Get all sectors."""
    try:
        from models import Sector
        sectors = Sector.query.all()
        return success_response([sector.to_dict() for sector in sectors])
    except Exception as e:
        logger.error(f"Error getting sectors: {str(e)}")
        return error_response(f"Error getting sectors: {str(e)}", "DB_ERROR", 500)

# Query endpoints
@rest_api.route('/query', methods=['POST'])
def process_query():
    """Process a query through the UKG system."""
    try:
        data = request.json
        if not data:
            return error_response("No data provided", "INVALID_REQUEST", 400)
        
        query = data.get('query')
        if not query:
            return error_response("Query is required", "MISSING_FIELD", 400)
        
        # Get the app orchestrator
        app_orchestrator = current_app.config.get('APP_ORCHESTRATOR')
        if not app_orchestrator:
            return error_response("App orchestrator not initialized", "SYSTEM_NOT_INIT", 500)
        
        # Process the query
        result = app_orchestrator.process_request(
            query=query,
            max_confidence=data.get('confidence', 0.95),
            max_passes=data.get('max_passes', 3),
            target_max_layer=data.get('max_layer', 3)
        )
        
        return success_response(result)
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return error_response(f"Error processing query: {str(e)}", "QUERY_ERROR", 500)

# Simulation endpoints
@rest_api.route('/simulations', methods=['GET'])
def get_simulations():
    """Get all simulation sessions."""
    try:
        from models import SimulationSession
        simulations = SimulationSession.query.all()
        return success_response([sim.to_dict() for sim in simulations])
    except Exception as e:
        logger.error(f"Error getting simulations: {str(e)}")
        return error_response(f"Error getting simulations: {str(e)}", "DB_ERROR", 500)

@rest_api.route('/simulations', methods=['POST'])
def create_simulation():
    """Create a new simulation session."""
    try:
        data = request.json
        if not data:
            return error_response("No data provided", "INVALID_REQUEST", 400)
        
        # Validate required fields
        if 'parameters' not in data:
            return error_response("Missing required field: parameters", "MISSING_FIELD", 400)
        
        from models import SimulationSession
        from app import db
        
        # Create new simulation
        new_simulation = SimulationSession(
            uid=str(uuid.uuid4()),
            name=data.get('name', f"Simulation-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"),
            parameters=data['parameters'],
            status="pending",
            current_step=0,
            results={}
        )
        
        db.session.add(new_simulation)
        
        try:
            db.session.commit()
            
            # Run the simulation asynchronously if requested
            if data.get('auto_start', False):
                # This would typically be done with a task queue like Celery
                # For simplicity, we'll just update the status here
                new_simulation.status = "active"
                db.session.commit()
            
            return success_response(new_simulation.to_dict(), "Simulation created successfully", 201)
        except Exception as e:
            db.session.rollback()
            return error_response(f"Database error: {str(e)}", "DB_COMMIT_ERROR", 500)
    except Exception as e:
        logger.error(f"Error creating simulation: {str(e)}")
        return error_response(f"Error creating simulation: {str(e)}", "INTERNAL_ERROR", 500)

@rest_api.route('/simulations/<simulation_id>', methods=['GET'])
def get_simulation(simulation_id):
    """Get details of a specific simulation."""
    try:
        from models import SimulationSession
        simulation = SimulationSession.query.filter_by(uid=simulation_id).first()
        
        if not simulation:
            return error_response(f"Simulation with ID {simulation_id} not found", "NOT_FOUND", 404)
        
        return success_response(simulation.to_dict())
    except Exception as e:
        logger.error(f"Error getting simulation: {str(e)}")
        return error_response(f"Error getting simulation: {str(e)}", "DB_ERROR", 500)

# Register the blueprint
def register_api(app):
    """Register the REST API blueprint with the Flask application."""
    app.register_blueprint(rest_api)
    logger.info("REST API endpoints registered")
