# ruff: noqa: E402
"""
Simulation Routes Blueprint

Handles CRUD and execution of Simulation Sessions.
"""

import uuid
import datetime
import asyncio
from datetime import UTC
import logging
from flask import Blueprint, jsonify, g, request
from extensions import db
from models import SimulationSession
from backend.auth.api_decorators import api_login_required
from flask_login import current_user
from backend.schemas.api_request_schemas import SimulationCreateRequest
from backend.utils.flask_request_validation import get_validated_payload, validate_json_payload
from backend.utils.error_normalization import normalize_public_error_message

simulation_bp = Blueprint('simulation_api', __name__, url_prefix='/api/v1')
logger = logging.getLogger(__name__)

from backend.utils.responses import error_response

def success_response(data, message="Operation successful", status_code=200):
    response = {"success": True, "message": message, "data": data}
    return jsonify(response), status_code


def _get_authenticated_user():
    auth_user = getattr(g, "auth_user", None)
    if auth_user is not None:
        return auth_user
    if getattr(current_user, "is_authenticated", False):
        return current_user
    return None


def _get_owned_simulation(session_id: str) -> SimulationSession | None:
    user = _get_authenticated_user()
    if user is None:
        return None
    return SimulationSession.query.filter_by(session_id=session_id, user_id=user.id).first()


def _build_simulation_parameters(payload: SimulationCreateRequest, raw_payload: dict) -> dict:
    parameters = dict(payload.parameters or {})
    if parameters:
        return parameters

    legacy_fields = (
        "query",
        "context",
        "sim_type",
        "confidenceThreshold",
        "maxLayer",
        "refinementSteps",
    )
    return {
        key: raw_payload[key]
        for key in legacy_fields
        if raw_payload.get(key) is not None
    }


def _run_phase10_boundary(simulation: SimulationSession, user_id: int):
    """Enter the canonical contract without executing a legacy simulation engine."""

    from backend.governed_execution.contracts import GovernedMode, GovernedRequest
    from backend.llm_gateway.gateway import LLMGateway

    query = str((simulation.parameters or {}).get("query") or "").strip()
    governed = GovernedRequest(
        messages=[{"role": "user", "content": query}],
        mode=GovernedMode.SIMULATION,
        source="simulation_route",
        principal_kind="desktop",
        principal_id=str(user_id),
        user_id=user_id,
        session_id=str(simulation.session_id),
        metadata={
            "simulation_id": str(simulation.session_id),
            "simulation_context": (simulation.parameters or {}).get("context", {}),
        },
    )
    return asyncio.run(LLMGateway(db_session=db.session).execute(governed))

@simulation_bp.route('/simulations', methods=['GET'])
@api_login_required
def get_simulations():
    """Get all simulation sessions for current user."""
    user = _get_authenticated_user()
    if user is None:
        return error_response("Authentication required", 401)
    simulations = SimulationSession.query.filter_by(user_id=user.id).order_by(SimulationSession.created_at.desc()).all()
    return success_response([s.to_dict() for s in simulations])

@simulation_bp.route('/simulations/<session_id>', methods=['GET'])
@api_login_required
def get_simulation(session_id):
    simulation = _get_owned_simulation(session_id)
    if not simulation:
        return error_response(f"Simulation {session_id} not found", 404)
    return success_response(simulation.to_dict())

@simulation_bp.route('/simulations', methods=['POST'])
@api_login_required
@validate_json_payload(SimulationCreateRequest)
def create_simulation():
    payload = get_validated_payload(SimulationCreateRequest)
    if payload is None:
        return error_response("Invalid request payload", 422)
    user = _get_authenticated_user()
    if user is None:
        return error_response("Authentication required", 401)

    raw_payload = request.get_json(silent=True) or {}
    parameters = _build_simulation_parameters(payload, raw_payload)
    if not parameters:
        return error_response("Missing parameters")
    
    new_simulation = SimulationSession(
        session_id=str(uuid.uuid4()),
        name=payload.name,
        user_id=user.id,
        parameters=parameters,
        status="active",
        current_step=0,
        results={}
    )
    
    db.session.add(new_simulation)
    try:
        db.session.commit()
        return success_response(new_simulation.to_dict(), "Simulation created", 201)
    except Exception as e:
        db.session.rollback()
        return error_response(
            normalize_public_error_message(str(e), "Failed to create simulation"),
            500,
        )

@simulation_bp.route('/simulations/<session_id>/step', methods=['POST'])
@simulation_bp.route('/simulations/<session_id>/run', methods=['POST'])
@api_login_required
def run_simulation_step(session_id):
    simulation = _get_owned_simulation(session_id)
    if not simulation:
        return error_response(f"Simulation {session_id} not found", 404)
    if simulation.status != "active":
        return error_response(f"Simulation not active: {simulation.status}")
    
    # Phase 10 owns the selected simulation engine and its provider budget. The
    # request enters the canonical contract now so no legacy engine or recursive
    # gateway loop can run while that capability remains unqualified.
    try:
        query = str(simulation.parameters.get('query') or '').strip()
        if not query:
            return error_response("Simulation query is required", 422)
        governed = _run_phase10_boundary(simulation, int(simulation.user_id))
        payload = governed.to_dict()
        simulation.status = "deferred" if governed.failure and governed.failure.code == "SIMULATION_PHASE10_BOUNDARY" else "failed"
        simulation.completed_at = datetime.datetime.now(UTC)
        simulation.results = {"governed_boundary": payload}
        db.session.commit()
        failure = governed.failure
        return error_response(
            failure.message if failure else "Simulation execution is unavailable",
            503,
            error_code=failure.code if failure else "SIMULATION_UNAVAILABLE",
            details={
                "trace_id": governed.trace_id,
                "contract_version": governed.contract_version,
                "status": governed.status,
            },
        )
    except Exception as e:
        logger.error(f"Engine execution failed: {e}", exc_info=True)
        return error_response(
            normalize_public_error_message(str(e), "Engine failure"),
            500,
        )

@simulation_bp.route('/simulations/<session_id>/stop', methods=['POST'])
@api_login_required
def stop_simulation(session_id):
    simulation = _get_owned_simulation(session_id)
    if not simulation:
        return error_response(f"Simulation {session_id} not found", 404)
    
    simulation.status = "completed"
    simulation.completed_at = datetime.datetime.now(UTC)
    
    db.session.commit()
    return success_response(simulation.to_dict(), "Simulation stopped")
