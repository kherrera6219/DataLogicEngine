
"""
Regulatory API for Axis 6

This module provides API endpoints for working with the Regulatory Framework axis.
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import logging

regulatory_api = Blueprint('regulatory_api', __name__)

@regulatory_api.route('/api/regulatory/frameworks', methods=['GET'])
def get_frameworks():
    """Get all regulatory frameworks, optionally filtered by level."""
    try:
        node_level = request.args.get('node_level')
        limit = int(request.args.get('limit', 50))
        
        axis_system = current_app.config.get('AXIS_SYSTEM')
        db_manager = current_app.config.get('DB_MANAGER')
        
        if not db_manager:
            return jsonify({
                'status': 'error',
                'message': 'Database manager not available',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        query = {
            'node_type': 'regulatory_framework',
            'axis_number': 6
        }
        
        if node_level:
            query['node_level'] = node_level
        
        frameworks = db_manager.get_nodes_by_properties(query, limit=limit)
        
        return jsonify({
            'status': 'success',
            'frameworks': frameworks,
            'count': len(frameworks),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting regulatory frameworks: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error getting regulatory frameworks: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

@regulatory_api.route('/api/regulatory/frameworks', methods=['POST'])
def create_framework():
    """Create a new regulatory framework."""
    try:
        data = request.json
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        axis_system = current_app.config.get('AXIS_SYSTEM')
        regulatory_manager = axis_system.axis_managers.get(6)
        
        if not regulatory_manager:
            return jsonify({
                'status': 'error',
                'message': 'Regulatory manager not available',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        # Determine the framework level and create accordingly
        node_level = data.get('node_level', 'mega')
        parent_uid = data.get('parent_uid')
        
        if node_level == 'mega':
            result = regulatory_manager.create_mega_framework(data)
        elif node_level == 'large' and parent_uid:
            result = regulatory_manager.create_large_framework(data, parent_uid)
        elif node_level == 'medium' and parent_uid:
            result = regulatory_manager.create_medium_framework(data, parent_uid)
        elif node_level == 'small' and parent_uid:
            result = regulatory_manager.create_small_framework(data, parent_uid)
        else:
            return jsonify({
                'status': 'error',
                'message': f'Invalid node level or missing parent_uid: {node_level}',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        status_code = 201 if result.get('status') == 'success' else 400
        return jsonify(result), status_code
        
    except Exception as e:
        current_app.logger.error(f"Error creating regulatory framework: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error creating regulatory framework: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

@regulatory_api.route('/api/regulatory/requirements', methods=['POST'])
def create_requirement():
    """Create a new granular requirement."""
    try:
        data = request.json
        if not data or 'parent_uid' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing data or parent_uid',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        axis_system = current_app.config.get('AXIS_SYSTEM')
        regulatory_manager = axis_system.axis_managers.get(6)
        
        if not regulatory_manager:
            return jsonify({
                'status': 'error',
                'message': 'Regulatory manager not available',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        parent_uid = data.get('parent_uid')
        result = regulatory_manager.create_granular_requirement(data, parent_uid)
        
        status_code = 201 if result.get('status') == 'success' else 400
        return jsonify(result), status_code
        
    except Exception as e:
        current_app.logger.error(f"Error creating requirement: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error creating requirement: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

@regulatory_api.route('/api/regulatory/octopus/<framework_uid>', methods=['GET'])
def get_octopus_structure(framework_uid):
    """Get the complete octopus structure for a mega framework."""
    try:
        axis_system = current_app.config.get('AXIS_SYSTEM')
        regulatory_manager = axis_system.axis_managers.get(6)
        
        if not regulatory_manager:
            return jsonify({
                'status': 'error',
                'message': 'Regulatory manager not available',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        result = regulatory_manager.get_octopus_structure(framework_uid)
        
        status_code = 200 if result.get('status') == 'success' else 400
        return jsonify(result), status_code
        
    except Exception as e:
        current_app.logger.error(f"Error getting octopus structure: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error getting octopus structure: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

@regulatory_api.route('/api/regulatory/crosswalk', methods=['POST'])
def create_crosswalk():
    """Create a crosswalk between regulatory frameworks or requirements."""
    try:
        data = request.json
        if not data or 'source_uid' not in data or 'target_uid' not in data or 'crosswalk_type' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields: source_uid, target_uid, crosswalk_type',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        axis_system = current_app.config.get('AXIS_SYSTEM')
        regulatory_manager = axis_system.axis_managers.get(6)
        
        if not regulatory_manager:
            return jsonify({
                'status': 'error',
                'message': 'Regulatory manager not available',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        source_uid = data.get('source_uid')
        target_uid = data.get('target_uid')
        crosswalk_type = data.get('crosswalk_type')
        attributes = data.get('attributes')
        
        result = regulatory_manager.create_regulatory_crosswalk(
            source_uid, 
            target_uid, 
            crosswalk_type, 
            attributes
        )
        
        status_code = 201 if result.get('status') == 'success' else 400
        return jsonify(result), status_code
        
    except Exception as e:
        current_app.logger.error(f"Error creating crosswalk: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error creating crosswalk: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

@regulatory_api.route('/api/regulatory/jurisdiction', methods=['POST'])
def map_jurisdiction():
    """Map a regulatory framework to a jurisdiction."""
    try:
        data = request.json
        if not data or 'framework_uid' not in data or 'jurisdiction_data' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields: framework_uid, jurisdiction_data',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        axis_system = current_app.config.get('AXIS_SYSTEM')
        regulatory_manager = axis_system.axis_managers.get(6)
        
        if not regulatory_manager:
            return jsonify({
                'status': 'error',
                'message': 'Regulatory manager not available',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        framework_uid = data.get('framework_uid')
        jurisdiction_data = data.get('jurisdiction_data')
        
        result = regulatory_manager.map_jurisdictions(framework_uid, jurisdiction_data)
        
        status_code = 201 if result.get('status') == 'success' else 400
        return jsonify(result), status_code
        
    except Exception as e:
        current_app.logger.error(f"Error mapping jurisdiction: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error mapping jurisdiction: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

@regulatory_api.route('/api/regulatory/compliance_link', methods=['POST'])
def create_compliance_link():
    """Create a link between a regulatory framework and a compliance standard."""
    try:
        data = request.json
        if not data or 'framework_uid' not in data or 'compliance_standard_uid' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields: framework_uid, compliance_standard_uid',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        axis_system = current_app.config.get('AXIS_SYSTEM')
        regulatory_manager = axis_system.axis_managers.get(6)
        
        if not regulatory_manager:
            return jsonify({
                'status': 'error',
                'message': 'Regulatory manager not available',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        framework_uid = data.get('framework_uid')
        compliance_standard_uid = data.get('compliance_standard_uid')
        link_type = data.get('link_type', 'implements')
        attributes = data.get('attributes')
        
        result = regulatory_manager.create_compliance_link(
            framework_uid,
            compliance_standard_uid,
            link_type,
            attributes
        )
        
        status_code = 201 if result.get('status') == 'success' else 400
        return jsonify(result), status_code
        
    except Exception as e:
        current_app.logger.error(f"Error creating compliance link: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error creating compliance link: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500
