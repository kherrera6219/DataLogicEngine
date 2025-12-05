
"""
UKG Compliance Standards API

This module provides API endpoints for managing and accessing compliance standards
in the Universal Knowledge Graph (UKG) system.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify, current_app

compliance_api = Blueprint('compliance_api', __name__, url_prefix='/api/compliance')

@compliance_api.route('/standards', methods=['GET'])
def get_compliance_standards():
    """Get all compliance standards or filtered by type."""
    try:
        standard_type = request.args.get('type')
        
        axis_system = current_app.config.get('AXIS_SYSTEM')
        compliance_manager = axis_system.axis_managers.get(7)
        
        if not compliance_manager:
            return jsonify({
                'status': 'error',
                'message': 'Compliance manager not initialized',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        result = compliance_manager.get_compliance_hierarchy(standard_type)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error getting compliance standards: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error getting compliance standards: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

@compliance_api.route('/standards', methods=['POST'])
def create_compliance_standard():
    """Create a new compliance standard."""
    try:
        data = request.json
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'Missing request body',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        parent_id = data.pop('parent_id', None)
        
        axis_system = current_app.config.get('AXIS_SYSTEM')
        compliance_manager = axis_system.axis_managers.get(7)
        
        if not compliance_manager:
            return jsonify({
                'status': 'error',
                'message': 'Compliance manager not initialized',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        result = compliance_manager.register_compliance_standard(data, parent_id)
        
        if result.get('status') == 'error':
            return jsonify(result), 400
        
        return jsonify(result), 201
        
    except Exception as e:
        current_app.logger.error(f"Error creating compliance standard: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error creating compliance standard: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

@compliance_api.route('/standards/<standard_id>', methods=['GET'])
def get_compliance_standard(standard_id):
    """Get a specific compliance standard by ID."""
    try:
        db_manager = current_app.config.get('DB_MANAGER')
        
        if not db_manager:
            return jsonify({
                'status': 'error',
                'message': 'Database manager not initialized',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        standards = db_manager.get_nodes_by_properties({
            'id': standard_id,
            'node_type': 'compliance_standard'
        })
        
        if not standards:
            return jsonify({
                'status': 'error',
                'message': f'Compliance standard not found: {standard_id}',
                'timestamp': datetime.now().isoformat()
            }), 404
        
        standard = standards[0]
        
        # Get parent standard if it exists
        parent_edge = None
        parent_standard = None
        
        incoming_edges = db_manager.get_incoming_edges(standard['uid'], ['has_standard'])
        if incoming_edges:
            parent_edge = incoming_edges[0]
            parent_uid = parent_edge['source_id']
            parent_standard = db_manager.get_node(parent_uid)
        
        # Get child standards
        child_standards = []
        outgoing_edges = db_manager.get_outgoing_edges(standard['uid'], ['has_standard'])
        
        for edge in outgoing_edges:
            child_uid = edge['target_id']
            child_node = db_manager.get_node(child_uid)
            
            if child_node:
                child_standards.append({
                    'standard': child_node,
                    'edge': edge
                })
        
        return jsonify({
            'status': 'success',
            'standard': standard,
            'parent': parent_standard,
            'parent_edge': parent_edge,
            'child_standards': child_standards,
            'child_count': len(child_standards),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting compliance standard: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error getting compliance standard: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

@compliance_api.route('/sector/<sector_id>', methods=['GET'])
def get_sector_compliance(sector_id):
    """Get compliance standards for a sector."""
    try:
        standard_type = request.args.get('type')
        
        axis_system = current_app.config.get('AXIS_SYSTEM')
        compliance_manager = axis_system.axis_managers.get(7)
        
        if not compliance_manager:
            return jsonify({
                'status': 'error',
                'message': 'Compliance manager not initialized',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        result = compliance_manager.find_compliance_for_sector(sector_id, standard_type)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error getting sector compliance: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error getting sector compliance: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

@compliance_api.route('/map-regulatory', methods=['POST'])
def map_regulatory_to_compliance():
    """Map a regulatory framework to a compliance standard."""
    try:
        data = request.json
        if not data or 'regulatory_uid' not in data or 'compliance_uid' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields: regulatory_uid, compliance_uid',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        regulatory_uid = data['regulatory_uid']
        compliance_uid = data['compliance_uid']
        relationship_type = data.get('relationship_type', 'implements')
        confidence = data.get('confidence', 0.9)
        
        axis_system = current_app.config.get('AXIS_SYSTEM')
        compliance_manager = axis_system.axis_managers.get(7)
        
        if not compliance_manager:
            return jsonify({
                'status': 'error',
                'message': 'Compliance manager not initialized',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        result = compliance_manager.map_regulatory_to_compliance(
            regulatory_uid, compliance_uid, relationship_type, confidence
        )
        
        if result.get('status') == 'error':
            return jsonify(result), 400
        
        return jsonify(result), 201
        
    except Exception as e:
        current_app.logger.error(f"Error mapping regulatory to compliance: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error mapping regulatory to compliance: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500
