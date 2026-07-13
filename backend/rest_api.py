
"""
Universal Knowledge Graph (UKG) System - REST API

This module provides standardized REST API endpoints for the UKG system.
All endpoints follow RESTful conventions and return consistent JSON responses.
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, UTC
import logging
from backend.utils.error_normalization import normalize_public_error_message

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
        "timestamp": datetime.now(UTC).isoformat()
    }
    return jsonify(response), status_code

def error_response(message, error_code=None, status_code=400):
    """Format a standard error response."""
    response = {
        "success": False,
        "message": message,
        "error_code": error_code,
        "timestamp": datetime.now(UTC).isoformat()
    }
    return jsonify(response), status_code



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
        return error_response(
            normalize_public_error_message(str(e), "Error getting graph stats"),
            "INTERNAL_ERROR",
            500,
        )

# Pillar Level endpoints - DEPRECATED: Handled by pillar_api.py




# Sector endpoints - DEPRECATED: Handled by ukg_api.py


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
        return error_response(
            normalize_public_error_message(str(e), "Error processing query"),
            "QUERY_ERROR",
            500,
        )

# Simulation endpoints - DEPRECATED: Handled by routes/simulation_routes.py


# Register the blueprint
def register_api(app):
    """Register the REST API blueprint with the Flask application."""
    app.register_blueprint(rest_api)
    logger.info("REST API endpoints registered")
