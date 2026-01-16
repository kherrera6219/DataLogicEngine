"""
Admin Routes Blueprint (JSON API)

Handles all admin-only routes with proper access control via REST API.
"""

import datetime
from datetime import UTC
import logging
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from extensions import db
from models import User, SimulationSession, KnowledgeGraphNode, KnowledgeGraphEdge
from backend.security.rbac import require_permission, Permission, get_rbac_manager

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin_api', __name__, url_prefix='/api/v1/admin')

def success_response(data, message="Operation successful"):
    return jsonify({"success": True, "message": message, "data": data})

def error_response(message, status_code=400):
    return jsonify({"success": False, "error": message}), status_code

@admin_bp.route('/dashboard', methods=['GET'])
@login_required
@require_permission(Permission.SECURITY_READ)
def admin_dashboard_stats():
    """Get admin dashboard statistics."""
    stats = {
        'user_count': User.query.count(),
        'active_users': User.query.filter_by(active=True).count(),
        'node_count': KnowledgeGraphNode.query.count(),
        'edge_count': KnowledgeGraphEdge.query.count(),
        'simulation_count': SimulationSession.query.count()
    }
    
    recent_users = [u.to_dict() for u in User.query.order_by(User.created_at.desc()).limit(5).all()]
    
    return success_response({
        "stats": stats,
        "recent_users": recent_users
    })

@admin_bp.route('/users', methods=['GET'])
@login_required
@require_permission(Permission.USER_READ)
def get_users():
    """Get list of users with desktop identity metadata."""
    users = User.query.order_by(User.created_at.desc()).all()
    
    role_counts = {
        'owner': User.query.filter_by(role='owner').count(),
        'admin': User.query.filter_by(is_admin=True, role='admin').count(),
        'analyst': User.query.filter_by(role='analyst').count(),
        'user': User.query.filter_by(role='user').count()
    }
    
    return success_response({
        "users": [u.to_dict() for u in users],
        "counts": role_counts
    })

@admin_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@login_required
@require_permission(Permission.USER_MANAGE_ROLES)
def update_user_role(user_id):
    """Update user role with ownership protection."""
    user = User.query.get(user_id)
    if not user: return error_response("User not found", 404)
    
    if user.role == 'owner':
        return error_response("Cannot modify Owner role directly. Use Ownership Transfer.", 403)
    
    data = request.json
    new_role = data.get('role')
    is_admin = data.get('is_admin')
    
    if new_role: 
        if new_role == 'owner':
            return error_response("Cannot promote to Owner. Use Ownership Transfer.", 403)
        user.role = new_role
        
    if is_admin is not None: user.is_admin = is_admin
    
    try:
        db.session.commit()
        from extensions import audit_logger
        audit_logger.log_audit_event(
            event_type="ADMIN_ACTION",
            user_id=current_user.id,
            action="ROLE_UPDATE",
            details={
                "target_user": user.username,
                "new_role": user.role,
                "target_sid": getattr(user, 'windows_sid', None)
            }
        )
        return success_response(user.to_dict(), "User updated")
    except Exception as e:
        db.session.rollback()
        return error_response(str(e), 500)

@admin_bp.route('/users/transfer-ownership', methods=['POST'])
@login_required
def transfer_ownership():
    """Transfer ownership from current owner to another user."""
    if current_user.role != 'owner':
        return error_response("Only the current Owner can transfer ownership.", 403)
    
    data = request.json
    target_user_id = data.get('target_user_id')
    confirm = data.get('confirm')
    
    if confirm != 'TRANSFER':
        return error_response("Confirmation 'TRANSFER' required.", 400)
        
    target_user = User.query.get(target_user_id)
    if not target_user: return error_response("Target user not found.", 404)
    
    try:
        # Perform atomic transfer
        current_user.role = 'admin'
        current_user.is_admin = True
        
        target_user.role = 'owner'
        target_user.is_admin = True
        
        db.session.commit()
        
        from extensions import audit_logger
        audit_logger.log_audit_event(
            event_type="OWNERSHIP_TRANSFER",
            user_id=current_user.id,
            action="OWNER_PROMOTED",
            details={
                "from_user": current_user.username,
                "to_user": target_user.username,
                "windows_sid": target_user.windows_sid
            }
        )
        
        return success_response({
            "new_owner": target_user.to_dict()
        }, "Ownership transferred successfully.")
    except Exception as e:
        db.session.rollback()
        return error_response(str(e), 500)
