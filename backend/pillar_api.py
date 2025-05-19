
"""
Universal Knowledge Graph (UKG) System - Pillar Level API

This module provides API endpoints for managing the Pillar Levels (Axis 1)
and the dynamic mapping between pillar sublevels.
"""

import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from backend.middleware import api_response

# Set up logging
logger = logging.getLogger(__name__)

# Create Blueprint for Pillar API
pillar_api = Blueprint('pillar_api', __name__, url_prefix='/api/pillars')

@pillar_api.route('/', methods=['GET'])
@api_response
def get_all_pillars():
    """Get all pillar levels."""
    knowledge_manager = current_app.config.get('KNOWLEDGE_MANAGER')
    
    if not knowledge_manager:
        return {"error": "Knowledge Manager not available"}, 500
        
    result = knowledge_manager.get_all_pillar_levels()
    
    if result['status'] == 'success':
        return result['pillars']
    else:
        return {"error": result['message']}, 400

@pillar_api.route('/<pillar_id>', methods=['GET'])
@api_response
def get_pillar(pillar_id):
    """Get a specific pillar level."""
    knowledge_manager = current_app.config.get('KNOWLEDGE_MANAGER')
    
    if not knowledge_manager:
        return {"error": "Knowledge Manager not available"}, 500
        
    result = knowledge_manager.get_pillar_level(pillar_id)
    
    if result['status'] == 'success':
        return result['pillar']
    else:
        return {"error": result['message']}, 404

@pillar_api.route('/', methods=['POST'])
@api_response
def create_pillar():
    """Create a new pillar level."""
    knowledge_manager = current_app.config.get('KNOWLEDGE_MANAGER')
    
    if not knowledge_manager:
        return {"error": "Knowledge Manager not available"}, 500
        
    data = request.json
    result = knowledge_manager.create_pillar_level(data)
    
    if result['status'] == 'success':
        return result['pillar'], 201
    else:
        return {"error": result['message']}, 400

@pillar_api.route('/<pillar_id>/sublevels', methods=['GET'])
@api_response
def get_sublevels(pillar_id):
    """Get all sublevels for a pillar."""
    knowledge_manager = current_app.config.get('KNOWLEDGE_MANAGER')
    
    if not knowledge_manager:
        return {"error": "Knowledge Manager not available"}, 500
        
    pillar_result = knowledge_manager.get_pillar_level(pillar_id)
    
    if pillar_result['status'] == 'success':
        pillar = pillar_result['pillar']
        return pillar.get('sublevels', [])
    else:
        return {"error": pillar_result['message']}, 404

@pillar_api.route('/<pillar_id>/sublevels', methods=['POST'])
@api_response
def add_sublevel(pillar_id):
    """Add a sublevel to a pillar."""
    knowledge_manager = current_app.config.get('KNOWLEDGE_MANAGER')
    
    if not knowledge_manager:
        return {"error": "Knowledge Manager not available"}, 500
        
    data = request.json
    sublevel_id = data.get('sublevel_id')
    sublevel_name = data.get('name')
    sublevel_description = data.get('description', '')
    parent_sublevel_id = data.get('parent_sublevel_id')
    
    if not sublevel_id or not sublevel_name:
        return {"error": "sublevel_id and name are required"}, 400
        
    result = knowledge_manager.add_sublevel(
        pillar_id, 
        sublevel_id, 
        sublevel_name, 
        sublevel_description, 
        parent_sublevel_id
    )
    
    if result['status'] == 'success':
        return result['sublevel'], 201
    else:
        return {"error": result['message']}, 400

@pillar_api.route('/<pillar_id>/sublevels/<sublevel_id>', methods=['GET'])
@api_response
def get_sublevel(pillar_id, sublevel_id):
    """Get a specific sublevel."""
    knowledge_manager = current_app.config.get('KNOWLEDGE_MANAGER')
    
    if not knowledge_manager:
        return {"error": "Knowledge Manager not available"}, 500
        
    result = knowledge_manager.get_sublevel(pillar_id, sublevel_id)
    
    if result['status'] == 'success':
        return result['sublevel']
    else:
        return {"error": result['message']}, 404

@pillar_api.route('/mappings', methods=['GET'])
@api_response
def get_mappings():
    """Get all dynamic mappings."""
    knowledge_manager = current_app.config.get('KNOWLEDGE_MANAGER')
    
    if not knowledge_manager:
        return {"error": "Knowledge Manager not available"}, 500
        
    pillar_id = request.args.get('pillar_id')
    sublevel_id = request.args.get('sublevel_id')
    
    result = knowledge_manager.get_dynamic_mappings(pillar_id, sublevel_id)
    
    if result['status'] == 'success':
        return result['mappings']
    else:
        return {"error": result['message']}, 400

@pillar_api.route('/mappings', methods=['POST'])
@api_response
def create_mapping():
    """Create a new dynamic mapping."""
    knowledge_manager = current_app.config.get('KNOWLEDGE_MANAGER')
    
    if not knowledge_manager:
        return {"error": "Knowledge Manager not available"}, 500
        
    data = request.json
    
    source_pillar_id = data.get('source_pillar_id')
    source_sublevel_id = data.get('source_sublevel_id')
    target_pillar_id = data.get('target_pillar_id')
    target_sublevel_id = data.get('target_sublevel_id')
    mapping_type = data.get('mapping_type', 'related_to')
    strength = float(data.get('strength', 0.5))
    bidirectional = bool(data.get('bidirectional', False))
    
    if not all([source_pillar_id, source_sublevel_id, target_pillar_id, target_sublevel_id]):
        return {"error": "Source and target pillar and sublevel IDs are required"}, 400
        
    result = knowledge_manager.create_dynamic_mapping(
        source_pillar_id,
        source_sublevel_id,
        target_pillar_id,
        target_sublevel_id,
        mapping_type,
        strength,
        bidirectional
    )
    
    if result['status'] == 'success':
        return result['mapping'], 201
    else:
        return {"error": result['message']}, 400

@pillar_api.route('/<pillar_id>/expand', methods=['POST'])
@api_response
def expand_pillar(pillar_id):
    """Dynamically expand a pillar's sublevels."""
    knowledge_manager = current_app.config.get('KNOWLEDGE_MANAGER')
    
    if not knowledge_manager:
        return {"error": "Knowledge Manager not available"}, 500
        
    data = request.json
    context_text = data.get('context_text')
    
    result = knowledge_manager.dynamic_sublevel_expansion(pillar_id, context_text)
    
    if result['status'] == 'success':
        return result['expansion']
    else:
        return {"error": result['message']}, 400

@pillar_api.route('/analyze-text', methods=['POST'])
@api_response
def analyze_text():
    """Analyze text to identify relevant pillar levels and sublevels."""
    knowledge_manager = current_app.config.get('KNOWLEDGE_MANAGER')
    
    if not knowledge_manager:
        return {"error": "Knowledge Manager not available"}, 500
        
    data = request.json
    text = data.get('text')
    
    if not text:
        return {"error": "Text is required for analysis"}, 400
        
    result = knowledge_manager.analyze_text_for_pillar_context(text)
    
    if result['status'] == 'success':
        return result['context']
    else:
        return {"error": result['message']}, 400

@pillar_api.route('/export', methods=['POST'])
@api_response
def export_pillars():
    """Export all pillar levels to YAML."""
    knowledge_manager = current_app.config.get('KNOWLEDGE_MANAGER')
    
    if not knowledge_manager:
        return {"error": "Knowledge Manager not available"}, 500
        
    data = request.json
    file_path = data.get('file_path')
    
    result = knowledge_manager.export_pillar_levels_to_yaml(file_path)
    
    if result['status'] == 'success':
        return {"message": result['message'], "file_path": result['file_path']}
    else:
        return {"error": result['message']}, 400

def register_api(app):
    """Register the API blueprint with the Flask application."""
    app.register_blueprint(pillar_api)
    return app
