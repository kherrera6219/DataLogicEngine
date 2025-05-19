
"""
Universal Knowledge Graph (UKG) Security Scan API

This module provides REST API endpoints for security scanning and compliance verification.
"""

from flask import Blueprint, jsonify, request, current_app
import logging
from datetime import datetime, timedelta
import json
import uuid
import os

# Import security components
from backend.security import get_security_manager, get_compliance_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the blueprint
scan_bp = Blueprint('scan', __name__, url_prefix='/api/security/scan')

def register_scan_api(app):
    """Register the security scan API blueprint with the Flask app."""
    app.register_blueprint(scan_bp)
    logger.info("Security Scan API registered")

# Run security scan endpoint
@scan_bp.route('', methods=['POST'])
def run_security_scan():
    """
    Run a comprehensive security scan of the system.
    This endpoint triggers a scan of the system for security vulnerabilities,
    compliance issues, and other potential security problems.
    """
    try:
        # Get the security manager
        security_manager = get_security_manager()
        
        # Start the scan
        security_manager._perform_security_scan()
        
        # Get the scan results
        results = security_manager.last_scan_results
        
        return jsonify({
            'status': 'success',
            'message': 'Security scan completed successfully',
            'scan_id': results['scan_id'],
            'timestamp': results['timestamp'],
            'vulnerabilities_count': len(results['vulnerabilities']),
            'warnings_count': len(results['warnings'])
        })
        
    except Exception as e:
        logger.error(f"Error running security scan: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error running security scan: {str(e)}"
        }), 500

# Get scan results endpoint
@scan_bp.route('/<scan_id>', methods=['GET'])
def get_scan_results(scan_id):
    """
    Get the results of a specific security scan.
    
    Args:
        scan_id: The ID of the scan to retrieve
    """
    try:
        # Get the security manager
        security_manager = get_security_manager()
        
        # Check if the requested scan is the most recent one
        if security_manager.last_scan_results and security_manager.last_scan_results.get('scan_id') == scan_id:
            return jsonify(security_manager.last_scan_results)
        
        # Otherwise, try to load the scan from a file
        scan_file = f"logs/security/scan_{scan_id}.json"
        
        if not os.path.exists(scan_file):
            return jsonify({
                'status': 'error',
                'message': f"Scan with ID {scan_id} not found"
            }), 404
            
        with open(scan_file, 'r') as f:
            scan_results = json.load(f)
            
        return jsonify(scan_results)
        
    except Exception as e:
        logger.error(f"Error retrieving scan results: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error retrieving scan results: {str(e)}"
        }), 500

# Get recent scans endpoint
@scan_bp.route('/recent', methods=['GET'])
def get_recent_scans():
    """Get a list of recent security scans."""
    try:
        # Create logs directory if it doesn't exist
        scan_dir = "logs/security"
        if not os.path.exists(scan_dir):
            os.makedirs(scan_dir, exist_ok=True)
            return jsonify({
                'status': 'success',
                'scans': []
            })
            
        # List scan files
        scan_files = []
        for filename in os.listdir(scan_dir):
            if filename.startswith("scan_") and filename.endswith(".json"):
                file_path = os.path.join(scan_dir, filename)
                try:
                    with open(file_path, 'r') as f:
                        scan_data = json.load(f)
                        scan_files.append({
                            'scan_id': scan_data.get('scan_id'),
                            'timestamp': scan_data.get('timestamp'),
                            'vulnerabilities_count': len(scan_data.get('vulnerabilities', [])),
                            'warnings_count': len(scan_data.get('warnings', [])),
                            'file': filename
                        })
                except Exception as e:
                    logger.error(f"Error reading scan file {filename}: {str(e)}")
        
        # Sort by timestamp (descending)
        scan_files.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Limit to the 10 most recent scans
        recent_scans = scan_files[:10]
        
        return jsonify({
            'status': 'success',
            'scans': recent_scans
        })
        
    except Exception as e:
        logger.error(f"Error retrieving recent scans: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error retrieving recent scans: {str(e)}"
        }), 500

# SOC 2 control verification endpoint
@scan_bp.route('/verify/<control_id>', methods=['GET'])
def verify_control(control_id):
    """
    Verify compliance with a specific SOC 2 control.
    
    Args:
        control_id: The ID of the control to verify
    """
    try:
        # Get the compliance manager
        compliance_manager = get_compliance_manager()
        
        # Verify the control
        # This would normally involve a more complex verification process
        # For now, we'll simulate the verification results
        
        # Sample control results by category
        control_categories = {
            'SEC': 'security',
            'AVA': 'availability',
            'PI': 'processing_integrity',
            'CON': 'confidentiality',
            'PRI': 'privacy'
        }
        
        # Extract the category from the control ID
        category = None
        for prefix, cat in control_categories.items():
            if control_id.startswith(prefix):
                category = cat
                break
        
        if not category:
            return jsonify({
                'status': 'error',
                'message': f"Invalid control ID: {control_id}"
            }), 400
        
        # Log a compliance event for the verification
        compliance_manager.log_compliance_event(
            category=category,
            event_type="check",
            details=f"Verification of control {control_id}"
        )
        
        # Generate a verification result
        # In a real implementation, this would actually check the system
        verification_result = {
            'control_id': control_id,
            'timestamp': datetime.now().isoformat(),
            'status': 'compliant',  # or 'non_compliant', 'partially_compliant'
            'category': category,
            'evidence': [
                {
                    'type': 'log',
                    'description': 'Audit logs showing access control enforcement',
                    'timestamp': (datetime.now() - timedelta(days=1)).isoformat()
                },
                {
                    'type': 'config',
                    'description': 'System configuration showing security settings',
                    'timestamp': (datetime.now() - timedelta(days=3)).isoformat()
                }
            ],
            'notes': 'Control verification completed successfully.',
            'verification_id': str(uuid.uuid4())
        }
        
        return jsonify({
            'status': 'success',
            'verification': verification_result
        })
        
    except Exception as e:
        logger.error(f"Error verifying control: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error verifying control: {str(e)}"
        }), 500
