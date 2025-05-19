
"""
Universal Knowledge Graph (UKG) Security API

This module provides REST API endpoints for security and compliance management.
"""

from flask import Blueprint, jsonify, request, current_app
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json
import uuid

# Import security components
from backend.security import get_security_manager, get_audit_logger, get_compliance_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the blueprint
security_bp = Blueprint('security', __name__, url_prefix='/api/security')

def register_security_api(app):
    """Register the security API blueprint with the Flask app."""
    app.register_blueprint(security_bp)
    logger.info("Security API registered")

# Health check endpoint
@security_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for the Security API."""
    return jsonify({
        'status': 'healthy',
        'service': 'UKG Security API',
        'timestamp': datetime.now().isoformat()
    })

# Security status endpoint
@security_bp.route('/status', methods=['GET'])
def security_status():
    """Get the current security status."""
    # Get the security manager instance
    security_manager = get_security_manager()
    
    # Get the current status
    status = security_manager.get_security_status()
    
    return jsonify(status)

# Compliance status endpoint
@security_bp.route('/compliance/status', methods=['GET'])
def compliance_status():
    """Get the current compliance status."""
    # Get the compliance manager instance
    compliance_manager = get_compliance_manager()
    
    # Get the current compliance status
    status = compliance_manager.get_compliance_status()
    
    return jsonify(status)

# Compliance events endpoint
@security_bp.route('/compliance/events', methods=['GET'])
def compliance_events():
    """Get compliance events based on filter criteria."""
    # Get the compliance manager instance
    compliance_manager = get_compliance_manager()
    
    # Parse query parameters
    try:
        start_time = request.args.get('start_time')
        if start_time:
            start_time = datetime.fromisoformat(start_time)
            
        end_time = request.args.get('end_time')
        if end_time:
            end_time = datetime.fromisoformat(end_time)
            
        category = request.args.get('category')
        event_type = request.args.get('event_type')
        limit = int(request.args.get('limit', 100))
        
        # Get the compliance events
        events = compliance_manager.get_compliance_events(
            start_time=start_time,
            end_time=end_time,
            category=category,
            event_type=event_type,
            limit=limit
        )
        
        return jsonify({
            'events': events,
            'count': len(events)
        })
        
    except Exception as e:
        logger.error(f"Error retrieving compliance events: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

# Generate compliance report endpoint
@security_bp.route('/compliance/report', methods=['POST'])
def generate_compliance_report():
    """Generate a SOC 2 compliance report."""
    # Get the compliance manager instance
    compliance_manager = get_compliance_manager()
    
    # Parse request data
    try:
        data = request.json or {}
        
        start_date = data.get('start_date')
        if start_date:
            start_date = datetime.fromisoformat(start_date)
            
        end_date = data.get('end_date')
        if end_date:
            end_date = datetime.fromisoformat(end_date)
            
        # Generate the compliance report
        report = compliance_manager.generate_compliance_report(
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify(report)
        
    except Exception as e:
        logger.error(f"Error generating compliance report: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

# Audit log retrieval endpoint
@security_bp.route('/audit/events', methods=['GET'])
def audit_events():
    """Get audit events based on filter criteria."""
    # Get the audit logger instance
    audit_logger = get_audit_logger()
    
    # Parse query parameters
    try:
        start_time = request.args.get('start_time')
        if start_time:
            start_time = datetime.fromisoformat(start_time)
            
        end_time = request.args.get('end_time')
        if end_time:
            end_time = datetime.fromisoformat(end_time)
            
        event_type = request.args.get('event_type')
        user_id = request.args.get('user_id')
        resource_id = request.args.get('resource_id')
        action = request.args.get('action')
        status = request.args.get('status')
        limit = int(request.args.get('limit', 100))
        
        # Get the audit events
        events = audit_logger.get_audit_events(
            start_time=start_time,
            end_time=end_time,
            event_type=event_type,
            user_id=user_id,
            resource_id=resource_id,
            action=action,
            status=status,
            limit=limit
        )
        
        return jsonify({
            'events': events,
            'count': len(events)
        })
        
    except Exception as e:
        logger.error(f"Error retrieving audit events: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

# Security scan endpoint
@security_bp.route('/scan', methods=['POST'])
def run_security_scan():
    """Run a security scan."""
    # Get the security manager instance
    security_manager = get_security_manager()
    
    try:
        # Trigger a security scan
        security_manager._perform_security_scan()
        
        # Get the latest scan results
        results = security_manager.last_scan_results
        
        return jsonify({
            'status': 'success',
            'scan_id': results['scan_id'],
            'timestamp': results['timestamp'],
            'vulnerabilities_count': len(results['vulnerabilities']),
            'warnings_count': len(results['warnings'])
        })
        
    except Exception as e:
        logger.error(f"Error running security scan: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Verify audit log integrity endpoint
@security_bp.route('/audit/verify', methods=['POST'])
def verify_audit_log():
    """Verify the integrity of an audit log file."""
    # Get the audit logger instance
    audit_logger = get_audit_logger()
    
    try:
        data = request.json or {}
        log_file = data.get('log_file')
        
        # Verify the audit log integrity
        results = audit_logger.verify_audit_log_integrity(log_file)
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error verifying audit log: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
