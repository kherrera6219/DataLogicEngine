
"""
UKG Compliance Standards API

This module provides API endpoints for managing and accessing compliance standards
in the Universal Knowledge Graph (UKG) system.
"""

from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app

from backend.auth.api_decorators import api_login_required, api_admin_required
from backend.schemas.api_request_schemas import (
    ComplianceReportRequest,
    ComplianceStandardCreateRequest,
    RegulatoryComplianceMapRequest,
)
from backend.utils.error_normalization import normalize_public_error_message
from backend.utils.flask_request_validation import get_validated_payload, validate_json_payload

compliance_bp = Blueprint('compliance_api', __name__, url_prefix='/api/v1/compliance')

@compliance_bp.route('/standards', methods=['GET'])
@api_login_required
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

@compliance_bp.route('/standards', methods=['POST'])
@api_admin_required
@validate_json_payload(ComplianceStandardCreateRequest)
def create_compliance_standard():
    """Create a new compliance standard."""
    try:
        payload = get_validated_payload(ComplianceStandardCreateRequest)
        if payload is None:
            return jsonify({
                "status": "error",
                "message": "Invalid request payload",
                "timestamp": datetime.now().isoformat(),
            }), 422

        data = payload.model_dump()
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
            'message': normalize_public_error_message(str(e), "Error creating compliance standard"),
            'timestamp': datetime.now().isoformat()
        }), 500

@compliance_bp.route('/standards/<standard_id>', methods=['GET'])
@api_login_required
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

@compliance_bp.route('/sector/<sector_id>', methods=['GET'])
@api_login_required
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

@compliance_bp.route('/map-regulatory', methods=['POST'])
@api_admin_required
@validate_json_payload(RegulatoryComplianceMapRequest)
def map_regulatory_to_compliance():
    """Map a regulatory framework to a compliance standard."""
    try:
        payload = get_validated_payload(RegulatoryComplianceMapRequest)
        if payload is None:
            return jsonify({
                "status": "error",
                "message": "Invalid request payload",
                "timestamp": datetime.now().isoformat(),
            }), 422

        regulatory_uid = payload.regulatory_uid
        compliance_uid = payload.compliance_uid
        relationship_type = payload.relationship_type
        confidence = payload.confidence
        
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
            'message': normalize_public_error_message(str(e), "Error mapping regulatory to compliance"),
            'timestamp': datetime.now().isoformat()
        }), 500

@compliance_bp.route('/audit/export', methods=['GET'])
@api_admin_required
def export_audit_logs_route():
    """Export audit logs to CSV."""
    from backend.security.audit_logger import AuditLogger
    import os
    from flask import send_file
    
    try:
        days = request.args.get('days', 30, type=int)
        
        filename = f"audit_export_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        filepath = os.path.join("logs", "audit", filename)
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        logger_instance = AuditLogger()
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        count = logger_instance.export_to_csv(filepath, start_time=start_time, end_time=end_time)
        
        if count == 0:
            return jsonify({
                "status": "success",
                "message": "No logs found for the specified period",
                "count": 0
            })

        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        current_app.logger.error(f"Error exporting audit logs: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': normalize_public_error_message(str(e), "Error exporting logs")
        }), 500

@compliance_bp.route('/report/pdf', methods=['POST'])
@api_login_required
@validate_json_payload(ComplianceReportRequest)
def export_compliance_report():
    """Generate and export a real compliance report PDF."""
    from backend.reports.compliance import compliance_reporter, ComplianceFramework
    from flask import send_file
    import os
        
    try:
        payload = get_validated_payload(ComplianceReportRequest)
        if payload is None:
            return jsonify({"error": "Invalid request payload"}), 422

        framework_val = payload.framework
        framework = ComplianceFramework(framework_val)
        
        # In a real scenario, we'd fetch data_points from DB
        data_points = payload.data_points
        
        report = compliance_reporter.generate_report(
            framework=framework,
            start_date=datetime.now(),
            end_date=datetime.now(),
            data_points=data_points
        )
        
        pdf_path = report.get('pdf_export_path')
        if pdf_path and os.path.exists(pdf_path):
            return send_file(pdf_path, as_attachment=True)
        else:
            return jsonify({"error": "Failed to generate PDF"}), 500
            
    except Exception as e:
        current_app.logger.error(f"Compliance report generation failed: {e}")
        return jsonify({"error": normalize_public_error_message(str(e), "Compliance report generation failed")}), 500

