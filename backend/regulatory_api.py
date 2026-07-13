
"""
Regulatory API for Axis 6

This module provides API endpoints for working with the Regulatory Framework axis.
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
from backend.auth.api_decorators import api_login_required, api_admin_required
from backend.utils.error_normalization import normalize_public_error_message

regulatory_api = Blueprint('regulatory_api', __name__)

@regulatory_api.route('/frameworks', methods=['GET'])
@api_login_required
def get_frameworks():
    """Get all regulatory frameworks, optionally filtered by level."""
    try:
        node_level = request.args.get('node_level')
        try:
            limit = int(request.args.get('limit', 50))
        except (ValueError, TypeError):
            limit = 50
        
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
            'message': normalize_public_error_message(str(e), "Error getting regulatory frameworks"),
            'timestamp': datetime.now().isoformat()
        }), 500

@regulatory_api.route('/frameworks', methods=['POST'])
@api_admin_required
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
        if not axis_system:
            return jsonify({
                'status': 'error',
                'message': 'Axis system not available',
                'timestamp': datetime.now().isoformat()
            }), 500
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
            'message': normalize_public_error_message(str(e), "Error creating regulatory framework"),
            'timestamp': datetime.now().isoformat()
        }), 500

@regulatory_api.route('/requirements', methods=['POST'])
@api_admin_required
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
        if not axis_system:
            return jsonify({
                'status': 'error',
                'message': 'Axis system not available',
                'timestamp': datetime.now().isoformat()
            }), 500
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
            'message': normalize_public_error_message(str(e), "Error creating requirement"),
            'timestamp': datetime.now().isoformat()
        }), 500

@regulatory_api.route('/octopus/<framework_uid>', methods=['GET'])
@api_login_required
def get_octopus_structure(framework_uid):
    """Get the complete octopus structure for a mega framework."""
    try:
        axis_system = current_app.config.get('AXIS_SYSTEM')
        if not axis_system:
            return jsonify({
                'status': 'error',
                'message': 'Axis system not available',
                'timestamp': datetime.now().isoformat()
            }), 500
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
            'message': normalize_public_error_message(str(e), "Error getting octopus structure"),
            'timestamp': datetime.now().isoformat()
        }), 500

@regulatory_api.route('/crosswalk', methods=['POST'])
@api_admin_required
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
        if not axis_system:
            return jsonify({
                'status': 'error',
                'message': 'Axis system not available',
                'timestamp': datetime.now().isoformat()
            }), 500
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
            'message': normalize_public_error_message(str(e), "Error creating crosswalk"),
            'timestamp': datetime.now().isoformat()
        }), 500

@regulatory_api.route('/jurisdiction', methods=['POST'])
@api_admin_required
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
        if not axis_system:
            return jsonify({
                'status': 'error',
                'message': 'Axis system not available',
                'timestamp': datetime.now().isoformat()
            }), 500
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
            'message': normalize_public_error_message(str(e), "Error mapping jurisdiction"),
            'timestamp': datetime.now().isoformat()
        }), 500

@regulatory_api.route('/compliance_link', methods=['POST'])
@api_admin_required
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
        if not axis_system:
            return jsonify({
                'status': 'error',
                'message': 'Axis system not available',
                'timestamp': datetime.now().isoformat()
            }), 500
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
            'message': normalize_public_error_message(str(e), "Error creating compliance link"),
            'timestamp': datetime.now().isoformat()
        }), 500

@regulatory_api.route('/standards', methods=['GET'])
@api_login_required
def get_standards():
    """Get all compliance standards (e.g., NIST, SOC2, GDPR)."""
    try:
        # In a real system, these would come from Axis 7 or a similar manager
        standards = [
            {
                "id": "nist-800-171",
                "name": "NIST 800-171",
                "version": "Rev 2",
                "description": "Protecting Controlled Unclassified Information",
                "status": "active",
                "coverage": 94
            },
            {
                "id": "soc2-type-2",
                "name": "SOC2 Type 2",
                "version": "2024",
                "description": "Security, Availability, and Confidentiality Trust Services",
                "status": "active",
                "coverage": 88
            },
            {
                "id": "gdpr-eu",
                "name": "GDPR (EU)",
                "version": "2018",
                "description": "General Data Protection Regulation",
                "status": "warning",
                "coverage": 72
            }
        ]
        
        return jsonify({
            'success': True,
            'data': standards,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        current_app.logger.error(f"Error getting standards: {str(e)}")
        return jsonify({
            'success': False,
            'error': normalize_public_error_message(str(e), "Error getting standards"),
            'timestamp': datetime.now().isoformat()
        }), 500
