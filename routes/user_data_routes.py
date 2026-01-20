"""
User Data Management Routes (Privacy & Compliance)

Supports Data Portability (Export) and the Right to be Forgotten (Delete).
Implements GDPR Article 17 (Right to Erasure) and Article 20 (Data Portability).
"""

import json
from datetime import datetime, UTC
from typing import Tuple, Dict, Any

from flask import Blueprint, jsonify, Response, request
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError
import logging

from extensions import db, limiter
from models import User, SimulationSession
from backend.config.settings import settings
from backend.utils.responses import success_response, error_response, internal_error
from backend.utils.validation import validate_json_body

logger = logging.getLogger(__name__)
user_data_bp = Blueprint('user_data', __name__, url_prefix='/api/v1/user/data')


@user_data_bp.route('/export', methods=['GET'])
@login_required
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
        user_id = current_user.id

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
            "profile": current_user.to_dict(),
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
                    "username": current_user.username,
                    "simulation_count": len(simulation_results)
                }
            )
        except Exception as e:
            logger.warning(f"Failed to log data export audit event: {e}")

        return Response(
            json_data,
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment;filename=ukg_data_export_{current_user.username}.json'
            }
        )

    except SQLAlchemyError as e:
        logger.error(f"Database error during data export for user {current_user.id}: {e}", exc_info=True)
        return internal_error("Failed to compile data export due to database error")

    except (TypeError, ValueError) as e:
        logger.error(f"Serialization error during data export: {e}", exc_info=True)
        return internal_error("Failed to serialize data export")


@user_data_bp.route('/delete', methods=['POST'])
@login_required
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
        user_id = current_user.id
        username = current_user.username
        data = request.json

        # Confirmation gating (Security Shield)
        if data.get('confirm') != 'DELETE':
            return error_response(
                "Confirmation required. Please provide 'confirm': 'DELETE' in request.",
                400
            )

        # Cannot delete owner account (must transfer ownership first)
        if current_user.role == 'owner':
            return error_response(
                "Owner account cannot be self-deleted. Transfer ownership first.",
                403
            )

        # Audit destructive action BEFORE deletion
        sid = getattr(current_user, 'windows_sid', getattr(current_user, 'sid', 'LOCAL_FALLBACK'))
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

        # Delete associated data first (maintain referential integrity)
        deleted_simulations = SimulationSession.query.filter_by(user_id=user_id).delete()

        # Delete the user
        user_to_delete = db.session.get(User, user_id)
        if user_to_delete:
            db.session.delete(user_to_delete)

        db.session.commit()

        logger.info(
            f"User {username} (SID: {sid}) has permanently wiped their profile. "
            f"Deleted {deleted_simulations} simulations."
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
                    "deleted_username": username,
                    "deleted_user_id": user_id,
                    "windows_sid": sid,
                    "simulations_deleted": deleted_simulations
                }
            )
        except Exception as e:
            logger.warning(f"Failed to log deletion completion audit: {e}")

        return success_response(
            {
                "deleted_user_id": user_id,
                "simulations_deleted": deleted_simulations
            },
            "Your profile and associated data have been permanently deleted."
        )

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error during profile deletion: {e}", exc_info=True)
        return internal_error("Deletion failed due to database error. Please try again.")


@user_data_bp.route('/summary', methods=['GET'])
@login_required
@limiter.limit(settings.API_RATE_LIMIT)
def get_user_data_summary() -> Tuple[Response, int]:
    """
    Get a summary of user's data without full export.

    Returns counts and metadata about stored data.

    Returns:
        JSON response with data summary
    """
    try:
        user_id = current_user.id

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
            "username": current_user.username,
            "account_created": current_user.created_at.isoformat() if current_user.created_at else None,
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
