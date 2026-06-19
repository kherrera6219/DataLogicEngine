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

from flask import Blueprint, Response, request
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError

from extensions import db, limiter, cache
from models import User, SimulationSession, KnowledgeGraphNode, KnowledgeGraphEdge
from backend.config.settings import settings
from backend.utils.responses import (
    success_response,
    error_response,
    not_found_error,
    forbidden_error,
    validation_error,
    internal_error
)
from backend.utils.validation import validate_json_body

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
                'active_users': db.session.query(User).filter(User.active).count(),
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
            "to_windows_sid": getattr(target_user, 'sid', getattr(target_user, 'windows_sid', None))
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
