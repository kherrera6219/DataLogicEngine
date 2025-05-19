
"""
Unified Mapping System API

This module provides API endpoints for the Unified Mapping System,
allowing access to Nuremberg numbering, SAM.gov naming, and 13D coordinate system features.
"""

from flask import Blueprint, request, jsonify
import logging
import json
import numpy as np
from datetime import datetime

# Create blueprint
unified_mapping_api = Blueprint('unified_mapping_api', __name__)

# Logger
logger = logging.getLogger(__name__)

@unified_mapping_api.route('/api/unified/status', methods=['GET'])
def get_status():
    """Get the status of the unified mapping system."""
    from main import unified_mapping_system
    
    if not unified_mapping_system:
        return jsonify({
            'status': 'error',
            'message': 'Unified mapping system not initialized',
            'timestamp': datetime.now().isoformat()
        }), 500
    
    stats = unified_mapping_system.get_unified_system_stats()
    return jsonify(stats)

@unified_mapping_api.route('/api/unified/register_node', methods=['POST'])
def register_node():
    """Register a node in the unified system."""
    try:
        from main import unified_mapping_system
        
        if not unified_mapping_system:
            return jsonify({
                'status': 'error',
                'message': 'Unified mapping system not initialized',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        # Get request data
        data = request.json
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Register the node
        result = unified_mapping_system.register_node_in_unified_system(data)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"[{datetime.now()}] Error registering node: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error registering node: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

@unified_mapping_api.route('/api/unified/nuremberg/<code>', methods=['GET'])
def get_by_nuremberg(code):
    """Find nodes by Nuremberg code."""
    try:
        from main import unified_mapping_system
        
        if not unified_mapping_system:
            return jsonify({
                'status': 'error',
                'message': 'Unified mapping system not initialized',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        nodes = unified_mapping_system.find_nodes_by_nuremberg_code(code)
        
        return jsonify({
            'status': 'success',
            'nuremberg_code': code,
            'nodes': nodes,
            'node_count': len(nodes),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"[{datetime.now()}] Error finding nodes by Nuremberg code: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error finding nodes: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

@unified_mapping_api.route('/api/unified/samgov/<name>', methods=['GET'])
def get_by_samgov(name):
    """Find nodes by SAM.gov name."""
    try:
        from main import unified_mapping_system
        
        if not unified_mapping_system:
            return jsonify({
                'status': 'error',
                'message': 'Unified mapping system not initialized',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        nodes = unified_mapping_system.find_nodes_by_samgov_name(name)
        
        return jsonify({
            'status': 'success',
            'samgov_name': name,
            'nodes': nodes,
            'node_count': len(nodes),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"[{datetime.now()}] Error finding nodes by SAM.gov name: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error finding nodes: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

@unified_mapping_api.route('/api/unified/coordinates', methods=['POST'])
def find_by_coordinates():
    """Find nodes by 13D coordinates."""
    try:
        from main import unified_mapping_system
        
        if not unified_mapping_system:
            return jsonify({
                'status': 'error',
                'message': 'Unified mapping system not initialized',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        # Get request data
        data = request.json
        if not data or 'coordinates' not in data:
            return jsonify({
                'status': 'error',
                'message': 'No coordinates provided',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        coordinates = np.array(data['coordinates'])
        distance_threshold = data.get('distance_threshold', 0.2)
        
        # Find nearby nodes
        nearby_nodes = unified_mapping_system.find_nodes_in_coordinate_vicinity(
            coordinates, distance_threshold)
        
        return jsonify({
            'status': 'success',
            'coordinates': coordinates.tolist(),
            'distance_threshold': distance_threshold,
            'nearby_nodes': nearby_nodes,
            'node_count': len(nearby_nodes),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"[{datetime.now()}] Error finding nodes by coordinates: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error finding nodes: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

@unified_mapping_api.route('/api/unified/memory_locate', methods=['POST'])
def locate_in_memory():
    """Locate data in the simulated memory space."""
    try:
        from main import unified_mapping_system
        
        if not unified_mapping_system:
            return jsonify({
                'status': 'error',
                'message': 'Unified mapping system not initialized',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        # Get request data
        data = request.json
        if not data or 'coordinates' not in data:
            return jsonify({
                'status': 'error',
                'message': 'No coordinates provided',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        coordinates = np.array(data['coordinates'])
        precision = data.get('precision', 0.1)
        
        # Locate data in memory space
        result = unified_mapping_system.locate_data_in_memory_space(
            coordinates, precision)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"[{datetime.now()}] Error locating data in memory: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error locating data: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500
