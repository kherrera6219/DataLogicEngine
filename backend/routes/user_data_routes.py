"""
User Data Management Routes (Privacy & Compliance)

Supports Data Portability (Export) and the Right to be Forgotten (Delete).
Implements GDPR Article 17 (Right to Erasure) and Article 20 (Data Portability).
"""

import json
from datetime import datetime, UTC
from typing import Tuple, Dict, Any

from flask import Blueprint, Response, current_app, request
from sqlalchemy.exc import SQLAlchemyError
import logging

from extensions import db, limiter
from models import SimulationSession
from backend.auth.api_decorators import api_session_login_required, get_authenticated_principal
from backend.config.settings import settings
from backend.storage.retention import DeletionSubject, RetentionDeleteError
from backend.utils.responses import success_response, error_response, internal_error
from backend.utils.validation import validate_json_body

logger = logging.getLogger(__name__)
user_data_bp = Blueprint('user_data', __name__, url_prefix='/api/v1/user/data')


@user_data_bp.route('/export', methods=['GET'])
@api_session_login_required
@limiter.limit("5 per hour")  # Rate limit exports to prevent abuse
def export_user_data() -> Tuple[Response, int]:
    """
    Export all data associated with the current user in JSON format.

    Includes profile, simulation history (results only), and metadata.
    Implements GDPR Article 20 (Data Portability).

    Returns:
        JSON file download with all user data
    """
    try:
        auth_user = get_authenticated_principal()
        user_id = auth_user.id

        # Optimized query: Only fetch needed columns, not full objects
        # This fixes the N+1 query issue
        simulation_results = (
            db.session.query(
                SimulationSession.session_id,
                SimulationSession.results,
                SimulationSession.status
            )
            .filter(SimulationSession.user_id == user_id)
            .all()
        )

        # Build export data
        data: Dict[str, Any] = {
            "version": "1.0",
            "export_date": datetime.now(UTC).isoformat(),
            "profile": auth_user.to_dict(),
            "simulations": [
                {
                    "session_id": sim.session_id,
                    "status": sim.status,
                    "results": sim.results
                }
                for sim in simulation_results
            ],
            "simulation_count": len(simulation_results),
            "notice": "This export contains your local DataLogicEngine profile and results."
        }

        json_data = json.dumps(data, indent=2, default=str)

        # Log the export for audit
        try:
            from extensions import audit_logger
            audit_logger.log_audit_event(
                event_type="DATA_EXPORT",
                user_id=user_id,
                action="USER_DATA_EXPORTED",
                status="success",
                details={
                    "username": auth_user.username,
                    "simulation_count": len(simulation_results)
                }
            )
        except Exception as e:
            logger.warning(f"Failed to log data export audit event: {e}")

        return Response(
            json_data,
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment;filename=ukg_data_export_{auth_user.username}.json'
            }
        )

    except SQLAlchemyError as e:
        logger.error("Database error during data export: %s", e, exc_info=True)
        return internal_error("Failed to compile data export due to database error")

    except (TypeError, ValueError) as e:
        logger.error(f"Serialization error during data export: {e}", exc_info=True)
        return internal_error("Failed to serialize data export")


@user_data_bp.route('/delete', methods=['POST'])
@api_session_login_required
@limiter.limit("1 per hour")  # Very strict - profile deletion is critical
@validate_json_body(['confirm'])
def delete_user_profile() -> Tuple[Response, int]:
    """
    Delete the current user's profile and all associated local data.

    Requires explicit confirmation for desktop residency protection.
    Implements GDPR Article 17 (Right to Erasure).

    Request Body:
        confirm (str): Must be "DELETE" to proceed

    Returns:
        JSON response confirming deletion or error
    """
    try:
        auth_user = get_authenticated_principal()
        user_id = auth_user.id
        username = auth_user.username
        data = request.json

        # Confirmation gating (Security Shield)
        if data.get('confirm') != 'DELETE':
            return error_response(
                "Confirmation required. Please provide 'confirm': 'DELETE' in request.",
                400
            )

        # Single-mode / OS-level auth: there is one owner and no ownership transfer,
        # so the GDPR self-deletion proceeds (the desktop auto-login recreates the
        # local user on next launch). The legacy owner-self-delete guard was removed
        # with roles (auth-deprecation Phase E).

        # Audit destructive action BEFORE deletion
        sid = getattr(auth_user, 'windows_sid', getattr(auth_user, 'sid', 'LOCAL_FALLBACK'))
        try:
            from extensions import audit_logger
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
        except Exception as e:
            logger.warning(f"Failed to log deletion audit event: {e}")

        from backend.storage.user_deletion import run_user_deletion

        tombstone = run_user_deletion(
            current_app._get_current_object(),
            DeletionSubject(
                "user",
                str(user_id),
                tenant_id=getattr(auth_user, "tenant_id", None),
            ),
        )
        postgres_deleted = int(
            tombstone.store_status.get("postgresql", {}).get("deleted_count") or 0
        )

        logger.info(
            f"User {username} (SID: {sid}) has permanently wiped their profile. "
            f"Cross-store deletion {tombstone.deletion_id} completed; "
            f"PostgreSQL rows deleted={postgres_deleted}."
        )

        # Final audit entry
        try:
            from extensions import audit_logger
            audit_logger.log_audit_event(
                event_type="DATA_DELETION",
                user_id=None,  # User no longer exists
                action="PROFILE_WIPE",
                status="completed",
                details={
                    "deletion_id": str(tombstone.deletion_id),
                    "subject_digest": tombstone.subject_digest,
                    "policy_version": tombstone.policy_version,
                }
            )
        except Exception as e:
            logger.warning(f"Failed to log deletion completion audit: {e}")

        return success_response(
            {
                "deletion_id": str(tombstone.deletion_id),
                "policy_version": tombstone.policy_version,
                "store_status": tombstone.store_status,
                "postgresql_rows_deleted": postgres_deleted,
            },
            "Your profile and associated data have been permanently deleted."
        )

    except RetentionDeleteError as e:
        db.session.rollback()
        logger.error("Cross-store profile deletion incomplete: %s", e)
        return internal_error(
            "Deletion is incomplete and safely recorded for retry. No completion was claimed."
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error during profile deletion: {e}", exc_info=True)
        return internal_error("Deletion failed due to database error. Please try again.")


@user_data_bp.route('/summary', methods=['GET'])
@api_session_login_required
@limiter.limit(settings.API_RATE_LIMIT)
def get_user_data_summary() -> Tuple[Response, int]:
    """
    Get a summary of user's data without full export.

    Returns counts and metadata about stored data.

    Returns:
        JSON response with data summary
    """
    try:
        auth_user = get_authenticated_principal()
        user_id = auth_user.id

        # Efficient count query
        simulation_count = (
            db.session.query(SimulationSession)
            .filter(SimulationSession.user_id == user_id)
            .count()
        )

        # Get status breakdown
        status_counts = (
            db.session.query(SimulationSession.status, db.func.count(SimulationSession.id))
            .filter(SimulationSession.user_id == user_id)
            .group_by(SimulationSession.status)
            .all()
        )

        return success_response({
            "user_id": user_id,
            "username": auth_user.username,
            "account_created": auth_user.created_at.isoformat() if auth_user.created_at else None,
            "data_summary": {
                "total_simulations": simulation_count,
                "simulations_by_status": dict(status_counts)
            },
            "available_actions": [
                {"action": "export", "endpoint": "/api/v1/user/data/export", "method": "GET"},
                {"action": "delete", "endpoint": "/api/v1/user/data/delete", "method": "POST"}
            ]
        })

    except SQLAlchemyError as e:
        logger.error(f"Database error getting data summary: {e}", exc_info=True)
        return internal_error("Failed to retrieve data summary")
