"""
Admin Routes Blueprint (JSON API)

Handles all admin-only routes with proper access control via REST API.
"""

import datetime
from datetime import UTC
import logging

from models import User, SimulationSession, KnowledgeGraphNode, KnowledgeGraphEdge
from backend.security.rbac import require_permission, Permission

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
    """Get list of users."""
    users = User.query.order_by(User.created_at.desc()).all()
    
    role_counts = {
        'admin': User.query.filter_by(is_admin=True).count(),
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
    """Update user role."""
    user = User.query.get(user_id)
    if not user: return error_response("User not found", 404)
    
    data = request.json
    new_role = data.get('role')
    is_admin = data.get('is_admin')
    
    if new_role: user.role = new_role
    if is_admin is not None: user.is_admin = is_admin
    
    try:
        db.session.commit()
        return success_response(user.to_dict(), "User updated")
    except Exception as e:
        db.session.rollback()
        return error_response(str(e), 500)
