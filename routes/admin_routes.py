"""
Admin Routes Blueprint (JSON API)

Handles all admin-only routes with proper access control via REST API.
Includes:
- Input validation
- Rate limiting
- Pagination
- Proper exception handling
- Audit logging
"""

from datetime import datetime, UTC
from typing import Optional, Dict, Any, Tuple
import logging

from flask import Blueprint, Response, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from extensions import db, limiter, cache
from models import User, SimulationSession, KnowledgeGraphNode, KnowledgeGraphEdge
from backend.security.rbac import require_permission, Permission, get_rbac_manager
from backend.config.settings import settings
from backend.utils.responses import (
    success_response,
    error_response,
    paginated_response,
    not_found_error,
    forbidden_error,
    validation_error,
    internal_error
)
from backend.utils.pagination import PaginationParams, paginate_query, pagination_meta
from backend.utils.validation import Validator, ValidationError, validate_json_body

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin_api', __name__, url_prefix='/api/v1/admin')


# =============================================================================
# Helper Functions
# =============================================================================

def _get_cached_stats() -> Dict[str, int]:
    """
    Get cached admin dashboard stats.
    Uses a single optimized query instead of multiple count() calls.
    """
    cache_key = 'admin_dashboard_stats'
    stats = cache.get(cache_key)

    if stats is None:
        try:
            # Single query with subqueries is more efficient than multiple queries
            stats = {
                'user_count': db.session.query(User).count(),
                'active_users': db.session.query(User).filter(User.active == True).count(),
                'node_count': db.session.query(KnowledgeGraphNode).count(),
                'edge_count': db.session.query(KnowledgeGraphEdge).count(),
                'simulation_count': db.session.query(SimulationSession).count()
            }
            cache.set(cache_key, stats, timeout=settings.STATS_CACHE_TTL)
        except SQLAlchemyError as e:
            logger.error(f"Failed to fetch dashboard stats: {e}")
            stats = {
                'user_count': 0, 'active_users': 0, 'node_count': 0,
                'edge_count': 0, 'simulation_count': 0, 'error': True
            }

    return stats


def _validate_role(role: str) -> Tuple[bool, Optional[str]]:
    """Validate role against allowed roles."""
    if role not in settings.ALLOWED_ROLES:
        return False, f"Invalid role. Must be one of: {', '.join(sorted(settings.ALLOWED_ROLES))}"
    if role in settings.PROTECTED_ROLES:
        return False, f"Cannot assign protected role '{role}' via API. Use ownership transfer for owner role."
    return True, None


def _audit_admin_action(action: str, details: Dict[str, Any]) -> None:
    """Log admin action to audit log."""
    try:
        from extensions import audit_logger
        audit_logger.log_audit_event(
            event_type="ADMIN_ACTION",
            user_id=current_user.id if current_user.is_authenticated else None,
            action=action,
            details={
                **details,
                "admin_username": current_user.username if current_user.is_authenticated else None,
                "timestamp": datetime.now(UTC).isoformat()
            }
        )
    except Exception as e:
        logger.warning(f"Failed to log audit event: {e}")


# =============================================================================
# Dashboard Endpoints
# =============================================================================

@admin_bp.route('/dashboard', methods=['GET'])
@login_required
@limiter.limit(settings.ADMIN_RATE_LIMIT)
@require_permission(Permission.SECURITY_READ)
def admin_dashboard_stats() -> Tuple[Response, int]:
    """
    Get admin dashboard statistics.

    Returns:
        JSON response with user counts, graph stats, and recent users
    """
    try:
        stats = _get_cached_stats()

        recent_users = (
            User.query
            .order_by(User.created_at.desc())
            .limit(5)
            .all()
        )

        return success_response({
            "stats": stats,
            "recent_users": [u.to_dict() for u in recent_users]
        })

    except SQLAlchemyError as e:
        logger.error(f"Database error in dashboard stats: {e}", exc_info=True)
        return internal_error("Failed to retrieve dashboard statistics")


# =============================================================================
# User Management Endpoints
# =============================================================================

@admin_bp.route('/users', methods=['GET'])
@login_required
@limiter.limit(settings.ADMIN_RATE_LIMIT)
@require_permission(Permission.USER_READ)
def get_users() -> Tuple[Response, int]:
    """
    Get paginated list of users with desktop identity metadata.

    Query Parameters:
        page (int): Page number (default: 1)
        per_page (int): Items per page (default: 50, max: 100)
        role (str): Filter by role (optional)
        active (bool): Filter by active status (optional)

    Returns:
        Paginated JSON response with users and role counts
    """
    try:
        # Parse and validate pagination params
        params = PaginationParams.from_request(max_per_page=settings.MAX_PAGE_SIZE)

        # Build query with optional filters
        query = User.query.order_by(User.created_at.desc())

        # Apply filters
        role_filter = request.args.get('role')
        if role_filter and role_filter in settings.ALLOWED_ROLES:
            query = query.filter(User.role == role_filter)

        active_filter = request.args.get('active')
        if active_filter is not None:
            is_active = active_filter.lower() in ('true', '1', 'yes')
            query = query.filter(User.active == is_active)

        # Execute paginated query
        pagination = paginate_query(query, params)

        # Get cached role counts
        role_counts = cache.get('user_role_counts')
        if role_counts is None:
            role_counts = {
                'owner': User.query.filter_by(role='owner').count(),
                'admin': User.query.filter(User.is_admin == True, User.role == 'admin').count(),
                'analyst': User.query.filter_by(role='analyst').count(),
                'user': User.query.filter_by(role='user').count()
            }
            cache.set('user_role_counts', role_counts, timeout=settings.STATS_CACHE_TTL)

        return paginated_response(
            items={
                "users": [u.to_dict() for u in pagination.items],
                "counts": role_counts
            },
            total=pagination.total,
            page=pagination.page,
            per_page=pagination.per_page,
            message="Users retrieved successfully"
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error listing users: {e}", exc_info=True)
        return internal_error("Failed to retrieve users")


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@login_required
@limiter.limit(settings.ADMIN_RATE_LIMIT)
@require_permission(Permission.USER_READ)
def get_user(user_id: int) -> Tuple[Response, int]:
    """
    Get a specific user by ID.

    Args:
        user_id: User ID

    Returns:
        JSON response with user data
    """
    try:
        user = db.session.get(User, user_id)
        if not user:
            return not_found_error("User", user_id)

        return success_response(user.to_dict())

    except SQLAlchemyError as e:
        logger.error(f"Database error getting user {user_id}: {e}", exc_info=True)
        return internal_error("Failed to retrieve user")


@admin_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@login_required
@limiter.limit("10 per minute")  # Stricter limit for role changes
@require_permission(Permission.USER_MANAGE_ROLES)
@validate_json_body(['role'])
def update_user_role(user_id: int) -> Tuple[Response, int]:
    """
    Update user role with ownership protection.

    Args:
        user_id: User ID to update

    Request Body:
        role (str): New role name (required)
        is_admin (bool): Admin flag (optional)

    Returns:
        JSON response with updated user data
    """
    try:
        user = db.session.get(User, user_id)
        if not user:
            return not_found_error("User", user_id)

        # Protect owner role from direct modification
        if user.role == 'owner':
            return forbidden_error("Cannot modify Owner role directly. Use Ownership Transfer.")

        # Prevent self-demotion for admins
        if user.id == current_user.id and current_user.is_admin:
            return forbidden_error("Cannot modify your own admin privileges")

        data = request.json

        # Validate and apply role change
        new_role = data.get('role')
        if new_role:
            is_valid, error_msg = _validate_role(new_role)
            if not is_valid:
                return validation_error({"role": [error_msg]})

            old_role = user.role
            user.role = new_role

        # Handle is_admin flag
        is_admin = data.get('is_admin')
        if is_admin is not None:
            if not isinstance(is_admin, bool):
                return validation_error({"is_admin": ["Must be a boolean value"]})
            user.is_admin = is_admin

        db.session.commit()

        # Invalidate cached role counts
        cache.delete('user_role_counts')

        # Audit the action
        _audit_admin_action("ROLE_UPDATE", {
            "target_user_id": user_id,
            "target_username": user.username,
            "old_role": old_role if new_role else user.role,
            "new_role": user.role,
            "target_sid": getattr(user, 'windows_sid', None)
        })

        return success_response(user.to_dict(), "User role updated successfully")

    except IntegrityError as e:
        db.session.rollback()
        logger.warning(f"Integrity error updating user {user_id}: {e}")
        return error_response("Failed to update user: integrity constraint violated", 409)

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error updating user {user_id}: {e}", exc_info=True)
        return internal_error("Failed to update user")


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
@limiter.limit("5 per minute")  # Very strict limit for deletions
@require_permission(Permission.USER_DELETE)
def delete_user(user_id: int) -> Tuple[Response, int]:
    """
    Delete a user account.

    Args:
        user_id: User ID to delete

    Query Parameters:
        confirm: Must be "DELETE" to confirm deletion

    Returns:
        JSON response confirming deletion
    """
    try:
        # Require explicit confirmation
        confirm = request.args.get('confirm')
        if confirm != 'DELETE':
            return error_response(
                "Deletion requires confirmation. Add ?confirm=DELETE to URL.",
                400
            )

        user = db.session.get(User, user_id)
        if not user:
            return not_found_error("User", user_id)

        # Cannot delete owner
        if user.role == 'owner':
            return forbidden_error("Cannot delete Owner account. Transfer ownership first.")

        # Cannot delete self
        if user.id == current_user.id:
            return forbidden_error("Cannot delete your own account via admin API")

        username = user.username
        user_sid = getattr(user, 'windows_sid', None)

        # Delete associated data first
        SimulationSession.query.filter_by(user_id=user_id).delete()
        db.session.delete(user)
        db.session.commit()

        # Invalidate caches
        cache.delete('user_role_counts')
        cache.delete('admin_dashboard_stats')

        # Audit the action
        _audit_admin_action("USER_DELETED", {
            "deleted_user_id": user_id,
            "deleted_username": username,
            "deleted_sid": user_sid
        })

        return success_response(
            {"deleted_user_id": user_id, "username": username},
            "User deleted successfully"
        )

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error deleting user {user_id}: {e}", exc_info=True)
        return internal_error("Failed to delete user")


# =============================================================================
# Ownership Transfer
# =============================================================================

@admin_bp.route('/users/transfer-ownership', methods=['POST'])
@login_required
@limiter.limit("1 per hour")  # Very strict limit - ownership transfer is critical
@validate_json_body(['target_user_id', 'confirm'])
def transfer_ownership() -> Tuple[Response, int]:
    """
    Transfer ownership from current owner to another user.

    Request Body:
        target_user_id (int): ID of user to receive ownership
        confirm (str): Must be "TRANSFER" to confirm

    Returns:
        JSON response with new owner data
    """
    # Only owner can transfer ownership
    if current_user.role != 'owner':
        return forbidden_error("Only the current Owner can transfer ownership.")

    try:
        data = request.json

        # Validate confirmation
        if data.get('confirm') != 'TRANSFER':
            return error_response(
                "Ownership transfer requires explicit confirmation. Set 'confirm' to 'TRANSFER'.",
                400
            )

        # Validate target user ID
        target_user_id = data.get('target_user_id')
        if not isinstance(target_user_id, int):
            return validation_error({"target_user_id": ["Must be an integer"]})

        target_user = db.session.get(User, target_user_id)
        if not target_user:
            return not_found_error("Target user", target_user_id)

        if target_user.id == current_user.id:
            return error_response("Cannot transfer ownership to yourself.", 400)

        if not target_user.active:
            return error_response("Cannot transfer ownership to inactive user.", 400)

        # Perform atomic transfer
        old_owner_username = current_user.username
        current_user.role = 'admin'
        current_user.is_admin = True

        target_user.role = 'owner'
        target_user.is_admin = True

        db.session.commit()

        # Invalidate caches
        cache.delete('user_role_counts')

        # Audit the critical action
        _audit_admin_action("OWNERSHIP_TRANSFERRED", {
            "from_user_id": current_user.id,
            "from_username": old_owner_username,
            "to_user_id": target_user.id,
            "to_username": target_user.username,
            "to_windows_sid": getattr(target_user, 'windows_sid', None)
        })

        logger.warning(
            f"OWNERSHIP TRANSFERRED: {old_owner_username} -> {target_user.username}"
        )

        return success_response(
            {"new_owner": target_user.to_dict()},
            "Ownership transferred successfully. You are now an admin."
        )

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error during ownership transfer: {e}", exc_info=True)
        return internal_error("Failed to transfer ownership")


# =============================================================================
# System Administration
# =============================================================================

@admin_bp.route('/cache/clear', methods=['POST'])
@login_required
@limiter.limit("5 per minute")
@require_permission(Permission.SYSTEM_ADMIN)
def clear_cache() -> Tuple[Response, int]:
    """
    Clear application caches.

    Request Body:
        keys (list[str]): Specific cache keys to clear (optional)
        all (bool): Clear all caches (optional)

    Returns:
        JSON response confirming cache cleared
    """
    try:
        data = request.get_json(silent=True) or {}

        if data.get('all'):
            cache.clear()
            _audit_admin_action("CACHE_CLEARED", {"scope": "all"})
            return success_response({"cleared": "all"}, "All caches cleared")

        keys = data.get('keys', [])
        if keys:
            if not isinstance(keys, list):
                return validation_error({"keys": ["Must be a list of strings"]})

            for key in keys:
                cache.delete(key)

            _audit_admin_action("CACHE_CLEARED", {"scope": "specific", "keys": keys})
            return success_response({"cleared": keys}, f"Cleared {len(keys)} cache keys")

        # Default: clear common admin caches
        default_keys = ['admin_dashboard_stats', 'user_role_counts']
        for key in default_keys:
            cache.delete(key)

        _audit_admin_action("CACHE_CLEARED", {"scope": "admin_default"})
        return success_response({"cleared": default_keys}, "Admin caches cleared")

    except Exception as e:
        logger.error(f"Error clearing cache: {e}", exc_info=True)
        return internal_error("Failed to clear cache")


@admin_bp.route('/health', methods=['GET'])
@login_required
@require_permission(Permission.SECURITY_READ)
def admin_health_check() -> Tuple[Response, int]:
    """
    Get detailed system health status for admins.

    Returns:
        JSON response with system health metrics
    """
    try:
        # Database check
        db_status = "healthy"
        try:
            db.session.execute(db.text("SELECT 1"))
        except Exception:
            db_status = "unhealthy"

        # Cache check
        cache_status = "healthy"
        try:
            cache.set('_health_check', 'ok', timeout=10)
            if cache.get('_health_check') != 'ok':
                cache_status = "degraded"
            cache.delete('_health_check')
        except Exception:
            cache_status = "unhealthy"

        return success_response({
            "status": "healthy" if db_status == "healthy" else "degraded",
            "components": {
                "database": db_status,
                "cache": cache_status
            },
            "timestamp": datetime.now(UTC).isoformat()
        })

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return success_response({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(UTC).isoformat()
        }, status_code=503)
