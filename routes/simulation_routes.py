# ruff: noqa: E402
"""
Simulation Routes Blueprint

Handles CRUD and execution of Simulation Sessions.
"""

import uuid
import datetime
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

# Initialize production engine
from backend.simulation.multi_agent_engine import create_multi_agent_simulation_engine
engine = create_multi_agent_simulation_engine()

def error_response(message, status_code=400):
    return jsonify({"error": message, "success": False}), status_code

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
    
    # Real Production Execution
    try:
        query = simulation.parameters.get('query', 'Standard Analysis')
        context = simulation.parameters.get('context', {})
        
        # Run one step of the production engine
        result = engine.process_query(query, context)
        result_status = result.get('status')

        if result_status != 'completed':
            simulation.status = result_status or "failed"
            if simulation.status in {"failed", "timeout", "completed"}:
                simulation.completed_at = datetime.datetime.now(UTC)
            simulation.results = {"latest_result": result}
            db.session.commit()
            fallback = "Simulation step failed"
            status_code = 504 if simulation.status == "timeout" else 502
            public_error = normalize_public_error_message(
                result.get("metadata", {}).get("error"),
                fallback,
            )
            return error_response(public_error, status_code)
        
        simulation.current_step += 1
        if simulation.started_at is None:
            simulation.started_at = datetime.datetime.now(UTC)
        
        results = simulation.results or {}
        results[str(simulation.current_step)] = result
        simulation.results = results
        
        simulation.status = "completed"
        simulation.completed_at = datetime.datetime.now(UTC)
            
        db.session.commit()
        return success_response(simulation.to_dict(), "Simulation executed successfully")
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
