"""
Admin Routes Blueprint (JSON API) — operational endpoints only.

Under the single-mode / OS-level auth architecture there are no users, roles, or
ownership to manage, so the user-management dashboard, role update, user
delete, and ownership-transfer routes were removed (auth-deprecation Phase E).
What remains are operational admin endpoints (cache control, health) available
to the authenticated owner.
"""

from datetime import datetime, UTC
from typing import Dict, Any, Tuple
import logging

from flask import Blueprint, Response, request

from extensions import db, limiter, cache
from backend.auth.api_decorators import api_session_login_required, get_authenticated_principal
from backend.utils.responses import (
    success_response,
    validation_error,
    internal_error,
)

logger = logging.getLogger(__name__)

# Ops-only admin surface. Gateway keys/providers live under
# `/api/v1/admin/gateway/*` (backend.llm_gateway.api.admin_bp).
admin_bp = Blueprint('admin_api', __name__, url_prefix='/api/v1/admin')


# =============================================================================
# Helper Functions
# =============================================================================

def _audit_admin_action(action: str, details: Dict[str, Any]) -> None:
    """Log admin action to audit log."""
    try:
        user = get_authenticated_principal()
        from extensions import audit_logger
        audit_logger.log_audit_event(
            event_type="ADMIN_ACTION",
            user_id=user.id,
            action=action,
            details={
                **details,
                "admin_username": user.username,
                "timestamp": datetime.now(UTC).isoformat()
            }
        )
    except Exception as e:
        logger.warning(f"Failed to log audit event: {e}")


# =============================================================================
# System Administration
# =============================================================================

@admin_bp.route('/cache/clear', methods=['POST'])
@api_session_login_required
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
@api_session_login_required
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
            "error": "Administrative health check failed",
            "timestamp": datetime.now(UTC).isoformat()
        }, status_code=503)
