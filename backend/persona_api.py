"""
Universal Knowledge Graph (UKG) System - Persona API

This module provides REST API endpoints for interacting with the Quad Persona Engine.
"""

import json
import logging
from flask import Blueprint, request, jsonify

from core.persona.persona_manager import get_persona_manager

logger = logging.getLogger(__name__)

# Create a Blueprint for the persona API
persona_api = Blueprint('persona_api', __name__)

@persona_api.route('/api/persona/query', methods=['POST'])
def process_query():
    """
    Process a query through the Quad Persona Engine.
    
    POST body:
    {
        "query": "The query to process",
        "context": {
            "conversation_id": "optional_conversation_id",
            "additional_context": "any additional context"
        }
    }
    """
    try:
        # Parse request data
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        # Extract query and context
        query = data.get('query')
        context = data.get('context', {})
        
        if not query:
            return jsonify({
                'status': 'error',
                'message': 'No query provided'
            }), 400
        
        # Get the persona manager
        persona_manager = get_persona_manager()
        
        # Process the query
        response_data = persona_manager.generate_response(query, context)
        
        # Return the response
        return jsonify({
            'status': 'success',
            'response': response_data['content'],
            'metadata': {
                'generated_by': response_data.get('generated_by', 'unknown'),
                'active_personas': response_data.get('active_personas', []),
                'confidence': response_data.get('confidence', 0),
                'used_memories': response_data.get('used_memories', False),
                'memory_contexts': response_data.get('memory_contexts', [])
            }
        })
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error processing query: {str(e)}'
        }), 500

@persona_api.route('/api/persona/add-memory', methods=['POST'])
def add_memory():
    """
    Add a memory to the system.
    
    POST body:
    {
        "content": "The memory content",
        "memory_type": "fact|insight|rule|feedback",
        "source": "user|system|knowledge_expert|sector_expert|regulatory_expert|compliance_expert",
        "context_name": "optional context name (default: general)",
        "metadata": {}
    }
    """
    try:
        # Parse request data
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        # Extract memory data
        content = data.get('content')
        memory_type = data.get('memory_type', 'fact')
        source = data.get('source', 'user')
        context_name = data.get('context_name', 'general')
        metadata = data.get('metadata', {})
        
        if not content:
            return jsonify({
                'status': 'error',
                'message': 'No content provided'
            }), 400
        
        # Get the persona manager
        persona_manager = get_persona_manager()
        
        # Add the memory
        success = persona_manager.add_memory(content, memory_type, source, context_name, metadata)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Memory added successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Error adding memory: context "{context_name}" not found'
            }), 400
    except Exception as e:
        logger.error(f"Error adding memory: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error adding memory: {str(e)}'
        }), 500

@persona_api.route('/api/persona/status', methods=['GET'])
def get_status():
    """Get the status of the Quad Persona Engine."""
    try:
        # Get the persona manager
        persona_manager = get_persona_manager()
        
        # Get the status
        status = persona_manager.get_status()
        
        # Return the status
        return jsonify({
            'status': 'success',
            'persona_engine': status
        })
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error getting status: {str(e)}'
        }), 500

@persona_api.route('/api/persona/clear-working-memory', methods=['POST'])
def clear_working_memory():
    """Clear the working memory of the Quad Persona Engine."""
    try:
        # Get the persona manager
        persona_manager = get_persona_manager()
        
        # Clear the working memory
        persona_manager.clear_working_memory()
        
        # Return success
        return jsonify({
            'status': 'success',
            'message': 'Working memory cleared successfully'
        })
    except Exception as e:
        logger.error(f"Error clearing working memory: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error clearing working memory: {str(e)}'
        }), 500

@persona_api.route('/api/persona/toggle-memory', methods=['POST'])
def toggle_memory():
    """Enable or disable memory usage in the Quad Persona Engine."""
    try:
        # Parse request data
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        # Extract enable flag
        enable = data.get('enable')
        if enable is None:
            return jsonify({
                'status': 'error',
                'message': 'No enable flag provided'
            }), 400
        
        # Get the persona manager
        persona_manager = get_persona_manager()
        
        # Enable or disable memory
        if enable:
            persona_manager.enable_memory()
            message = 'Memory enabled'
        else:
            persona_manager.disable_memory()
            message = 'Memory disabled'
        
        # Return success
        return jsonify({
            'status': 'success',
            'message': message
        })
    except Exception as e:
        logger.error(f"Error toggling memory: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error toggling memory: {str(e)}'
        }), 500

@persona_api.route('/api/persona/get-personas', methods=['GET'])
def get_personas():
    """Get the list of available personas and their details."""
    try:
        # Get the persona manager
        persona_manager = get_persona_manager()
        
        # Get the persona types
        persona_types = persona_manager.get_persona_types()
        
        # Get details for each persona
        personas = {}
        for persona_type in persona_types:
            persona_details = persona_manager.get_persona_details(persona_type)
            if persona_details:
                personas[persona_type] = persona_details
        
        # Return the personas
        return jsonify({
            'status': 'success',
            'personas': personas
        })
    except Exception as e:
        logger.error(f"Error getting personas: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error getting personas: {str(e)}'
        }), 500