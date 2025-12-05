"""
Universal Knowledge Graph (UKG) System - Persona API

This module implements the API endpoints for interacting with the
Quad Persona Simulation Engine.
"""

import logging
from typing import Optional
from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user

from simulation.simulation_engine import create_simulation_engine
from quad_persona.quad_engine import create_quad_persona_engine

logger = logging.getLogger(__name__)

# Create blueprint
persona_api = Blueprint('persona_api', __name__, url_prefix='/api/persona')

# Initialize simulation engine
simulation_engine = create_simulation_engine()

@persona_api.route('/query', methods=['POST'])
@login_required
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
        context['conversation_id'] = f"conv_{datetime.utcnow().timestamp()}"
    
    try:
        # Process the query with the simulation engine
        result = simulation_engine.process_query(query, context)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return jsonify({
            'error': 'Failed to process query',
            'details': str(e)
        }), 500

@persona_api.route('/direct-query', methods=['POST'])
@login_required
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
        # Create a new quad persona engine for this request
        engine = create_quad_persona_engine()
        
        # Process the query directly
        result = engine.process_query(query, context)
        
        return jsonify({
            'query': query,
            'response': result,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error processing direct query: {str(e)}")
        return jsonify({
            'error': 'Failed to process query',
            'details': str(e)
        }), 500

@persona_api.route('/personas', methods=['GET'])
@login_required
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
            'details': str(e)
        }), 500

@persona_api.route('/axis-map', methods=['GET'])
@login_required
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
            'details': str(e)
        }), 500