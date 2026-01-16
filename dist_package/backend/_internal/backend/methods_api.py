
"""
Methods API

This module provides API endpoints for accessing and managing the Methods axis (Axis 4)
of the Universal Knowledge Graph (UKG) system.
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime

methods_api = Blueprint('methods_api', __name__)

@methods_api.route('/api/methods', methods=['GET'])
def get_methods():
    """Get all method nodes or filtered by node type."""
    node_type = request.args.get('node_type')
    
    try:
        axis_system = current_app.config.get('AXIS_SYSTEM')
        methods_manager = axis_system.axis_managers.get(4)
        
        if not methods_manager:
            return jsonify({
                'status': 'error',
                'message': 'Methods manager not initialized',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        # Query nodes from the database based on filters
        filters = {}
        if node_type:
            filters['node_type'] = node_type
            
        filters['axis_number'] = 4  # Ensure we only get Method nodes
        
        # Use the database manager to get nodes
        db_manager = methods_manager.db_manager
        nodes = db_manager.get_nodes_by_properties(filters)
        
        return jsonify({
            'status': 'success',
            'count': len(nodes),
            'methods': nodes,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting methods: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error getting methods: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

@methods_api.route('/api/methods/<node_id>', methods=['GET'])
def get_method(node_id):
    """Get a specific method node by ID."""
    try:
        axis_system = current_app.config.get('AXIS_SYSTEM')
        methods_manager = axis_system.axis_managers.get(4)
        
        if not methods_manager:
            return jsonify({
                'status': 'error',
                'message': 'Methods manager not initialized',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        # Get the node
        db_manager = methods_manager.db_manager
        node = db_manager.get_node_by_id(node_id)
        
        if not node:
            return jsonify({
                'status': 'error',
                'message': f'Method node not found: {node_id}',
                'timestamp': datetime.now().isoformat()
            }), 404
        
        # Get the hierarchy
        hierarchy = methods_manager.get_method_hierarchy(node_id)
        
        return jsonify({
            'status': 'success',
            'method': node,
            'hierarchy': hierarchy,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting method: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error getting method: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

@methods_api.route('/api/methods/cross-sector', methods=['POST'])
def find_cross_sector_methods():
    """Find methods that apply across multiple sectors."""
    try:
        data = request.json
        if not data or 'sector_ids' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameter: sector_ids',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        sector_ids = data['sector_ids']
        if not isinstance(sector_ids, list) or not sector_ids:
            return jsonify({
                'status': 'error',
                'message': 'sector_ids must be a non-empty list',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        axis_system = current_app.config.get('AXIS_SYSTEM')
        methods_manager = axis_system.axis_managers.get(4)
        
        if not methods_manager:
            return jsonify({
                'status': 'error',
                'message': 'Methods manager not initialized',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        result = methods_manager.find_cross_sector_methods(sector_ids)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error finding cross-sector methods: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error finding cross-sector methods: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

@methods_api.route('/api/methods/cross-pillar', methods=['POST'])
def find_cross_pillar_methods():
    """Find methods that apply across multiple pillar levels."""
    try:
        data = request.json
        if not data or 'pillar_ids' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameter: pillar_ids',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        pillar_ids = data['pillar_ids']
        if not isinstance(pillar_ids, list) or not pillar_ids:
            return jsonify({
                'status': 'error',
                'message': 'pillar_ids must be a non-empty list',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        axis_system = current_app.config.get('AXIS_SYSTEM')
        methods_manager = axis_system.axis_managers.get(4)
        
        if not methods_manager:
            return jsonify({
                'status': 'error',
                'message': 'Methods manager not initialized',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        result = methods_manager.find_cross_pillar_methods(pillar_ids)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error finding cross-pillar methods: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error finding cross-pillar methods: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

@methods_api.route('/api/methods', methods=['POST'])
def create_method():
    """Create a new method node."""
    try:
        data = request.json
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Validate required fields
        required_fields = ['label', 'node_type', 'node_id']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}',
                    'timestamp': datetime.now().isoformat()
                }), 400
        
        axis_system = current_app.config.get('AXIS_SYSTEM')
        methods_manager = axis_system.axis_managers.get(4)
        
        if not methods_manager:
            return jsonify({
                'status': 'error',
                'message': 'Methods manager not initialized',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        result = methods_manager.register_method_node(data)
        
        if result.get('status') == 'exists':
            return jsonify(result), 409
        elif result.get('status') == 'error':
            return jsonify(result), 400
        else:
            return jsonify(result), 201
        
    except Exception as e:
        current_app.logger.error(f"Error creating method: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error creating method: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

@methods_api.route('/api/methods/hierarchy', methods=['POST'])
def create_hierarchy():
    """Create a hierarchical relationship between method nodes."""
    try:
        data = request.json
        if not data or 'parent_id' not in data or 'child_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameters: parent_id, child_id',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        parent_id = data['parent_id']
        child_id = data['child_id']
        
        axis_system = current_app.config.get('AXIS_SYSTEM')
        methods_manager = axis_system.axis_managers.get(4)
        
        if not methods_manager:
            return jsonify({
                'status': 'error',
                'message': 'Methods manager not initialized',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        result = methods_manager.establish_node_hierarchy(parent_id, child_id)
        
        if result.get('status') == 'exists':
            return jsonify(result), 409
        elif result.get('status') == 'error':
            return jsonify(result), 400
        else:
            return jsonify(result), 201
        
    except Exception as e:
        current_app.logger.error(f"Error creating hierarchy: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error creating hierarchy: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500
