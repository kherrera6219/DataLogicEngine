"""Compatibility routes for retired privacy deletion endpoints."""

from flask import Blueprint, jsonify

from backend.auth.api_decorators import api_session_login_required


privacy_bp = Blueprint("privacy", __name__, url_prefix="/api/v1/privacy")


@privacy_bp.route("/purge-request", methods=["POST"])
@api_session_login_required
def purge_user_data():
    """Retire the partial purge path in favor of the canonical delete contract."""
    return (
        jsonify(
            {
                "success": False,
                "error": "This deletion endpoint has been retired.",
                "replacement": {
                    "endpoint": "/api/v1/user/data/delete",
                    "method": "POST",
                    "required_body": {"confirm": "DELETE"},
                },
            }
        ),
        410,
    )


@privacy_bp.route("/tenant-cleanup", methods=["POST"])
@api_session_login_required
def cleanup_tenant_data():
    """Fail closed until a separately authorized tenant-wide workflow exists."""
    return (
        jsonify(
            {
                "success": False,
                "error": "Tenant-wide deletion is not an approved product operation.",
                "safe_reason": "tenant_delete_workflow_not_authorized",
            }
        ),
        501,
    )
