"""
User Data Management Routes (Privacy & Compliance)
Supports Data Portability (Export) and the Right to be Forgotten (Delete).
"""

import json
from datetime import datetime
from flask import Blueprint, jsonify, Response, request
from flask_login import login_required, current_user
from extensions import db
from models import User, SimulationSession
import logging

logger = logging.getLogger(__name__)
user_data_bp = Blueprint('user_data', __name__, url_prefix='/api/v1/user/data')

@user_data_bp.route('/export', methods=['GET'])
@login_required
def export_user_data():
    """
    Exports all data associated with the current user in JSON format.
    Includes profile, simulation history, and audit logs.
    """
    try:
        data = {
            "version": "1.0",
            "export_date": datetime.utcnow().isoformat(),
            "profile": current_user.to_dict(),
            "simulations": [sim.results for sim in SimulationSession.query.filter_by(user_id=current_user.id).all()],
            # In a full app, we'd include chat history, analytics, etc.
            "notice": "This export contains your local DataLogicEngine profile and results."
        }
        
        json_data = json.dumps(data, indent=2)
        
        return Response(
            json_data,
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment;filename=ukg_data_export_{current_user.username}.json'}
        )
    except Exception as e:
        logger.error(f"Data export failed: {e}")
        return jsonify({"success": False, "error": "Failed to compile data export"}), 500

@user_data_bp.route('/delete', methods=['POST'])
@login_required
def delete_user_profile():
    """
    Deletes the current user's profile and all associated local data.
    Requires explicit confirmation for desktop residency protection.
    """
    try:
        user_id = current_user.id
        username = current_user.username
        data = request.get_json() or {}
        
        # 0. Confirmation Gating (Security Shield)
        if data.get('confirm') != 'DELETE':
            return jsonify({
                "success": False, 
                "error": "Confirmation required. Please provide 'confirm': 'DELETE' in request."
            }), 400

        # 1. Audit destructive action
        from extensions import audit_logger
        sid = getattr(current_user, 'windows_sid', 'LOCAL_FALLBACK')
        audit_logger.log_audit_event(
            event_type="DATA_DELETION",
            user_id=user_id,
            action="PROFILE_WIPE",
            status="initiated",
            details={
                "username": username,
                "windows_sid": sid,
                "scope": "FULL_PROFILE_AND_SIMULATIONS"
            }
        )
        
        # 2. Delete associated data
        SimulationSession.query.filter_by(user_id=user_id).delete()
        
        # 3. Delete the user
        db.session.delete(current_user)
        db.session.commit()
        
        logger.info(f"User {username} (SID: {sid}) has permanently wiped their profile.")
        
        return jsonify({
            "success": True, 
            "message": "Your profile and associated data have been permanently deleted from this machine."
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Profile deletion failed: {e}")
        return jsonify({"success": False, "error": "Deletion failed due to system error"}), 500
