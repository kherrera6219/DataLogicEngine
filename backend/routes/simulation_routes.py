# ruff: noqa: E402
"""
Simulation Routes Blueprint

Handles CRUD and execution of Simulation Sessions.
"""

import datetime
import asyncio
import hashlib
import json
import logging
import uuid
from datetime import UTC

from flask import Blueprint, current_app, g, jsonify, request
from flask_login import current_user

from backend.auth.api_decorators import api_login_required
from backend.schemas.api_request_schemas import SimulationCreateRequest
from backend.simulation.contracts import SimulationDepth, SimulationScenario
from backend.utils.error_normalization import normalize_public_error_message
from backend.utils.flask_request_validation import get_validated_payload, validate_json_payload
from extensions import db
from models import SimulationEventRecord, SimulationSession

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


def _build_scenario(parameters: dict) -> SimulationScenario:
    depth_value = parameters.get("depth") or parameters.get("sim_type") or "standard"
    if depth_value not in {item.value for item in SimulationDepth}:
        depth_value = "standard"
    allowed = {
        "query": parameters.get("query"),
        "context": parameters.get("context") or {},
        "execution_mode": parameters.get("execution_mode", "live"),
        "provider": parameters.get("provider"),
        "model": parameters.get("model"),
        "depth": depth_value,
        "seed": parameters.get("seed", 0),
        "participants": parameters.get("participants") or [],
        "input_corpus": parameters.get("input_corpus") or [],
        "max_total_tokens": parameters.get("max_total_tokens", 10_000),
        "max_tool_calls": parameters.get("max_tool_calls", 0),
        "max_cost_usd": parameters.get("max_cost_usd"),
        "timeout_seconds": parameters.get("timeout_seconds", 300),
        "expected_artifacts": parameters.get("expected_artifacts")
        or [
            {"type": "transcript", "required": True},
            {"type": "result", "required": True},
        ],
    }
    return SimulationScenario.model_validate(allowed)


def _scenario_revision(scenario: SimulationScenario) -> str:
    payload = json.dumps(
        scenario.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _preflight_payload(scenario: SimulationScenario) -> dict:
    plan = scenario.plan.to_dict()
    provider_budget = _provider_budget_preflight(scenario)
    return {
        "scenario": scenario.model_dump(mode="json"),
        "scenario_revision": _scenario_revision(scenario),
        "plan": plan,
        "budget": {
            "max_provider_calls": plan["max_provider_calls"],
            "max_total_tokens": scenario.max_total_tokens,
            "max_output_tokens": plan["max_output_tokens"],
            "max_tool_calls": scenario.max_tool_calls,
            "max_cost_usd": scenario.max_cost_usd,
            "estimated_cost_usd": provider_budget["estimated_cost_usd"],
            "pricing_status": provider_budget["pricing_status"],
            "provider_status": (
                "available"
                if provider_budget["code"] not in {"SIMULATION_PROVIDER_UNAVAILABLE"}
                else "unavailable"
            ),
            "admissible": provider_budget["ok"],
            "blocking_code": provider_budget["code"],
        },
    }


def _provider_budget_preflight(scenario: SimulationScenario) -> dict:
    from backend.simulation.jobs import SimulationJobRunner
    from backend.simulation.providers import (
        FixedSeedSimulationTurnProvider,
        GatewaySimulationTurnProvider,
    )

    provider = (
        FixedSeedSimulationTurnProvider(seed=scenario.seed)
        if scenario.execution_mode == "fixed_seed_local"
        else GatewaySimulationTurnProvider(
            db_session=db.session,
            preferred_provider=scenario.provider,
            model=scenario.model,
        )
    )
    result = SimulationJobRunner._preflight_provider_budget(provider, scenario)
    close = getattr(provider, "close", None)
    if callable(close):
        try:
            asyncio.run(close())
        except Exception:
            logger.warning("Simulation preflight provider cleanup failed", exc_info=True)
    return result


@simulation_bp.route('/simulations', methods=['GET'])
@api_login_required
def get_simulations():
    """Get all simulation sessions for current user."""
    user = _get_authenticated_user()
    if user is None:
        return error_response("Authentication required", 401)
    simulations = SimulationSession.query.filter_by(user_id=user.id).order_by(SimulationSession.created_at.desc()).all()
    return success_response([s.to_dict() for s in simulations])


@simulation_bp.route('/simulations/preflight', methods=['POST'])
@api_login_required
def preflight_simulation():
    raw_payload = request.get_json(silent=True) or {}
    parameters = dict(raw_payload.get("parameters") or raw_payload)
    try:
        scenario = _build_scenario(parameters)
    except (TypeError, ValueError) as exc:
        return error_response(
            "Invalid simulation scenario",
            422,
            error_code="VALIDATION_ERROR",
            details={"reason": normalize_public_error_message(str(exc), "Scenario validation failed")},
        )
    return success_response(_preflight_payload(scenario), "Simulation preflight complete")

@simulation_bp.route('/simulations/<session_id>', methods=['GET'])
@api_login_required
def get_simulation(session_id):
    simulation = _get_owned_simulation(session_id)
    if not simulation:
        return error_response(f"Simulation {session_id} not found", 404)
    from backend.simulation.jobs import get_simulation_job_runner

    runner = get_simulation_job_runner(current_app._get_current_object())
    runner.reconcile_artifacts(simulation)
    data = simulation.to_dict()
    live_state = runner.live_state(session_id)
    if live_state:
        data["live_state"] = live_state
    return success_response(data)

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
    try:
        scenario = _build_scenario(parameters)
    except (TypeError, ValueError) as exc:
        return error_response(
            "Invalid simulation scenario",
            422,
            error_code="VALIDATION_ERROR",
            details={"reason": normalize_public_error_message(str(exc), "Scenario validation failed")},
        )
    preflight = _preflight_payload(scenario)
    
    new_simulation = SimulationSession(
        session_id=str(uuid.uuid4()),
        name=payload.name,
        user_id=user.id,
        parameters=preflight["scenario"],
        status="draft",
        current_step=0,
        total_steps=int(preflight["plan"]["max_provider_calls"]),
        results={},
        contract_version=scenario.contract_version,
        engine_id=str(preflight["plan"]["engine"]),
        engine_version=str(preflight["plan"]["engine_version"]),
        scenario_revision=preflight["scenario_revision"],
        seed=scenario.seed,
        plan=preflight["plan"],
        budget=preflight["budget"],
    )
    
    db.session.add(new_simulation)
    try:
        db.session.commit()
        return success_response(new_simulation.to_dict(), "Simulation created", 201)
    except Exception as e:
        db.session.rollback()
        logger.exception("Failed to persist simulation session")
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
    if simulation.status != "draft":
        return error_response(
            f"Simulation cannot run from status: {simulation.status}",
            409,
            error_code="SIMULATION_STATE_CONFLICT",
        )
    simulation.status = "queued"
    simulation.completed_at = None
    db.session.commit()
    from backend.simulation.jobs import get_simulation_job_runner

    get_simulation_job_runner(current_app._get_current_object()).submit(session_id)
    return success_response(simulation.to_dict(), "Simulation queued", 202)


@simulation_bp.route('/simulations/<session_id>/events', methods=['GET'])
@api_login_required
def get_simulation_events(session_id):
    simulation = _get_owned_simulation(session_id)
    if not simulation:
        return error_response(f"Simulation {session_id} not found", 404)
    try:
        after = max(0, int(request.args.get("after", 0)))
        limit = max(1, min(500, int(request.args.get("limit", 100))))
    except ValueError:
        return error_response("Invalid event cursor", 422, error_code="VALIDATION_ERROR")
    events = (
        SimulationEventRecord.query.filter(
            SimulationEventRecord.session_id == session_id,
            SimulationEventRecord.sequence > after,
        )
        .order_by(SimulationEventRecord.sequence)
        .limit(limit)
        .all()
    )
    return success_response(
        [
            {
                "sequence": event.sequence,
                "event_type": event.event_type,
                "status": event.status,
                "step_key": event.step_key,
                "current_step": event.progress_current,
                "total_steps": event.progress_total,
                "details": event.details or {},
                "created_at": event.created_at.isoformat(),
            }
            for event in events
        ]
    )


def _control_simulation(session_id: str, action: str):
    simulation = _get_owned_simulation(session_id)
    if not simulation:
        return error_response(f"Simulation {session_id} not found", 404)
    from backend.simulation.jobs import get_simulation_job_runner

    runner = get_simulation_job_runner(current_app._get_current_object())
    if action == "pause":
        if simulation.status not in {"queued", "running"}:
            return error_response("Simulation is not pausable", 409)
        runner.request_pause(simulation)
        if simulation.status == "queued":
            simulation.status = "paused"
            simulation.pause_requested_at = None
    elif action == "cancel":
        if simulation.status not in {"draft", "queued", "running", "paused"}:
            return error_response("Simulation is not cancellable", 409)
        runner.request_cancel(simulation)
        if simulation.status in {"draft", "queued", "paused"}:
            simulation.status = "cancelled"
            simulation.completed_at = datetime.datetime.now(UTC)
    elif action == "resume":
        if simulation.status != "paused":
            return error_response("Simulation is not resumable", 409)
        runner.resume(simulation)
    elif action == "retry":
        if simulation.status != "failed":
            return error_response("Simulation is not retryable", 409)
        try:
            runner.retry(simulation)
        except ValueError as exc:
            return error_response(
                "Simulation retry is unsafe after an uncheckpointed provider call",
                409,
                error_code=str(exc),
            )
    db.session.commit()
    return success_response(simulation.to_dict(), f"Simulation {action} accepted", 202)


@simulation_bp.route('/simulations/<session_id>/pause', methods=['POST'])
@api_login_required
def pause_simulation(session_id):
    return _control_simulation(session_id, "pause")


@simulation_bp.route('/simulations/<session_id>/resume', methods=['POST'])
@api_login_required
def resume_simulation(session_id):
    return _control_simulation(session_id, "resume")


@simulation_bp.route('/simulations/<session_id>/retry', methods=['POST'])
@api_login_required
def retry_simulation(session_id):
    return _control_simulation(session_id, "retry")

@simulation_bp.route('/simulations/<session_id>/stop', methods=['POST'])
@simulation_bp.route('/simulations/<session_id>/cancel', methods=['POST'])
@api_login_required
def stop_simulation(session_id):
    return _control_simulation(session_id, "cancel")
