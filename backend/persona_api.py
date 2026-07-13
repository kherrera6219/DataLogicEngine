"""
Universal Knowledge Graph (UKG) System - Persona API

This module implements the API endpoints for interacting with the
Quad Persona Simulation Engine.
"""

import logging
from datetime import datetime, UTC

from flask import Blueprint, request, jsonify
from flask_login import current_user
from backend.auth.api_decorators import api_session_login_required
from backend.utils.error_normalization import normalize_public_error_message

logger = logging.getLogger(__name__)

# Create blueprint
persona_api = Blueprint('persona_api', __name__)

# Lazy-loaded simulation engine (initialized on first use)
_simulation_engine = None


def _get_simulation_engine():
    """Get or create the simulation engine (lazy initialization)."""
    global _simulation_engine
    if _simulation_engine is None:
        from core.simulation.legacy_simulation_engine import create_simulation_engine
        _simulation_engine = create_simulation_engine()
        logger.info("Simulation engine initialized (lazy)")
    return _simulation_engine

@persona_api.route('/query', methods=['POST'])
@api_session_login_required
def process_query():
    """
    Process a query through the Quad Persona Simulation Engine.
    
    Expected JSON payload:
    {
        "query": "The query text to process",
        "context": {
            "conversation_id": "optional_conversation_id",
            "domain": "optional_domain",
            ...
        }
    }
    """
    data = request.json
    if not data or 'query' not in data:
        return jsonify({
            'error': 'Invalid request format, query is required'
        }), 400
    
    query = data['query']
    context = data.get('context', {})
    
    # Add user to context
    if current_user and current_user.is_authenticated:
        context['user_id'] = current_user.id
    
    # Add conversation ID if not provided
    if 'conversation_id' not in context:
        context['conversation_id'] = f"conv_{datetime.now(UTC).timestamp()}"
    
    try:
        # Process the query with the simulation engine (lazy loaded)
        result = _get_simulation_engine().process_query(query, context)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return jsonify({
            'error': 'Failed to process query',
            'details': normalize_public_error_message(str(e), "Internal persona processing error")
        }), 500

@persona_api.route('/direct-query', methods=['POST'])
@api_session_login_required
def direct_query():
    """
    Process a query directly through the Quad Persona Engine without additional simulation components.
    
    This endpoint is useful for testing and debugging the core persona engine.
    
    Expected JSON payload:
    {
        "query": "The query text to process",
        "context": { ... }
    }
    """
    data = request.json
    if not data or 'query' not in data:
        return jsonify({
            'error': 'Invalid request format, query is required'
        }), 400
    
    query = data['query']
    context = data.get('context', {})
    
    try:
        # Construct the four axes-8–11 expert personas directly via the
        # canonical DSQP system (deterministic, offline-capable). This replaces
        # the legacy root quad_persona engine/factory, which was a duplicate,
        # shadowed implementation that raised TypeError on construction.
        from backend.dsqp import DSQPOrchestrator

        orchestrator = DSQPOrchestrator()
        result = orchestrator.construct_all_sync(query, context=context)

        return jsonify({
            'query': query,
            'response': result,
            'timestamp': datetime.now(UTC).isoformat()
        })
    except Exception as e:
        logger.error(f"Error processing direct query: {str(e)}")
        return jsonify({
            'error': 'Failed to process query',
            'details': normalize_public_error_message(str(e), "Internal direct-query error")
        }), 500

@persona_api.route('/personas', methods=['GET'])
@api_session_login_required
def get_personas():
    """
    Get information about available personas in the system.
    """
    try:
        # For now, return a static list of available personas
        # In a real implementation, this would query the persona loader
        personas = {
            'knowledge': [{
                'id': 'knowledge_default',
                'name': 'Knowledge Expert',
                'description': 'Expert in domain-specific knowledge and academic concepts',
                'axis_number': 8
            }],
            'sector': [{
                'id': 'sector_default',
                'name': 'Sector Expert',
                'description': 'Expert in industry-specific practices and standards',
                'axis_number': 9
            }],
            'regulatory': [{
                'id': 'regulatory_default',
                'name': 'Regulatory Expert',
                'description': 'Expert in legal frameworks, regulations, and policy',
                'axis_number': 10
            }],
            'compliance': [{
                'id': 'compliance_default',
                'name': 'Compliance Expert',
                'description': 'Expert in ensuring adherence to standards and requirements',
                'axis_number': 11
            }]
        }
        
        return jsonify(personas)
    except Exception as e:
        logger.error(f"Error getting personas: {str(e)}")
        return jsonify({
            'error': 'Failed to get personas',
            'details': normalize_public_error_message(str(e), "Internal persona lookup error")
        }), 500

@persona_api.route('/axis-map', methods=['GET'])
@api_session_login_required
def get_axis_map():
    """
    Get information about the 13-axis coordinate system.
    """
    try:
        axis_map = {
            'core_axes': {
                1: 'Knowledge Framework (Pillar Levels)',
                2: 'Sectors',
                3: 'Domains',
                4: 'Methods',
                5: 'Temporal Context',
                6: 'Regulatory',
                7: 'Compliance'
            },
            'persona_axes': {
                8: 'Knowledge Expert',
                9: 'Sector Expert',
                10: 'Regulatory Expert (Octopus Node)',
                11: 'Compliance Expert (Spiderweb Node)'
            },
            'integration_axes': {
                12: 'Integration Context',
                13: 'Application Context'
            }
        }
        
        return jsonify(axis_map)
    except Exception as e:
        logger.error(f"Error getting axis map: {str(e)}")
        return jsonify({
            'error': 'Failed to get axis map',
            'details': normalize_public_error_message(str(e), "Internal axis-map error")
        }), 500
