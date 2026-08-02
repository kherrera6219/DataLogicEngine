"""
Knowledge Algorithm API Endpoints

Provides catalog, compatibility, and durable product workflows for the
canonical Knowledge Algorithm manifest.
"""

import asyncio
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

from flask import Blueprint, current_app, g, jsonify, request

from backend.auth.api_decorators import api_login_required, get_authenticated_principal
from backend.knowledge_algorithms.contracts import (
    KABudget,
    KAExecutionContext,
    KAExecutionMode,
)
from backend.knowledge_algorithms.ka_master_controller import get_controller
from backend.knowledge_algorithms.product_workflow import (
    TERMINAL_STATES,
    KAProductWorkflowError,
    confirm_and_queue_product_run,
    decrypt_product_result,
    get_ka_product_runner,
    plan_product_run,
    product_run_expired,
    result_artifacts,
    result_effects,
    trace_summary,
    validate_plan_request,
)
from backend.knowledge_algorithms.selection import KASelectionRequest
from backend.llm_gateway.external_contract import (
    normalize_client_scopes,
    scope_allows,
)

logger = logging.getLogger(__name__)

ka_bp = Blueprint('ka', __name__)

# Lazy-initialized master controller — avoids import-time DB/config access
# before the Flask app context is available.
_controller = None


def _error_response(message, status=500):
    return jsonify({'success': False, 'error': message}), status


def _get_controller():
    global _controller
    if _controller is None:
        _controller = get_controller()
    return _controller


def _run_async(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(asyncio.run, coro).result()


def _current_user_id():
    principal = get_authenticated_principal()
    return getattr(principal, "id", None)


def _current_tenant_id():
    principal = get_authenticated_principal()
    value = getattr(principal, "tenant_id", None)
    return str(value) if value else None


def _current_api_key():
    return getattr(g, "external_api_key", None)


def _current_ka_scopes() -> set[str]:
    api_key = _current_api_key()
    if api_key is None:
        return {"ka:read", "ka:plan", "ka:execute", "ka:cancel"}
    return set(normalize_client_scopes(api_key.permissions or {}))


def _require_ka_scope(required_scope):
    if scope_allows(_current_ka_scopes(), required_scope):
        return None
    return jsonify({
        "success": False,
        "error": "API key scope denied",
        "code": "KA_SCOPE_DENIED",
        "required_scope": required_scope,
    }), 403


def _workflow_error_response(error):
    return jsonify({
        "success": False,
        "error": error.public_message,
        "code": error.code,
    }), error.status


def _product_run_for_principal(run_id):
    from extensions import db
    from models import KAProductRun

    try:
        parsed = uuid.UUID(str(run_id))
    except (TypeError, ValueError, AttributeError):
        return None, _error_response("Knowledge Algorithm run not found", 404)
    run = db.session.get(KAProductRun, parsed)
    if (
        run is None
        or product_run_expired(run)
        or run.user_id != _current_user_id()
    ):
        return None, _error_response("Knowledge Algorithm run not found", 404)
    api_key = _current_api_key()
    principal_key = str(api_key.id) if api_key is not None else "desktop"
    if run.principal_key != principal_key:
        return None, _error_response("Knowledge Algorithm run not found", 404)
    return run, None


def _product_run_envelope(run):
    return run.to_dict()


def _execute_compatibility_plan(
    ka_id_norm,
    input_data,
    *,
    allow_nonproduction,
):
    """Route retained synchronous callers through selector/plan/controller."""
    controller = _get_controller()
    definition = controller._canonical_controller.manifest.entries[ka_id_norm]
    risk_classes = {
        str(value).strip().lower()
        for value in definition.contract.risk_classes
        if str(value).strip()
    }
    if (
        bool(risk_classes & {"high", "critical"})
        or definition.contract.effect_class
        == "effect_oriented_review_required"
    ):
        return None, {
            "code": "KA_PLAN_CONFIRMATION_REQUIRED",
            "error": (
                "This Knowledge Algorithm requires an exact reviewed plan; "
                "use /api/v1/ka/runs/plan"
            ),
            "status": 409,
        }

    manifest = controller._canonical_controller.manifest
    service_capabilities = {
        definition.integration.effect_port
        for definition in manifest.entries.values()
        if definition.integration.effect_port
        and definition.admission.production_enabled
    }
    selection_request = KASelectionRequest(
        requested_ids=[ka_id_norm],
        shared_input=input_data,
        service_capabilities=service_capabilities,
        context=KAExecutionContext(
            principal_id=str(_current_user_id()),
            scopes=_current_ka_scopes(),
            workflow="legacy_ka_api_compatibility",
            capability_state={
                capability: True
                for capability in service_capabilities
            },
            budget=KABudget(
                max_provider_calls=0,
                max_effects=64,
            ),
        ),
        mode=(
            KAExecutionMode.EVALUATION
            if allow_nonproduction
            else KAExecutionMode.PRODUCTION
        ),
    )
    plan = controller.plan_algorithms(selection_request)
    if not plan.valid:
        return None, {
            "code": "KA_PLAN_BLOCKED",
            "error": "Knowledge Algorithm plan did not pass admission",
            "status": 422,
            "plan": {
                "plan_id": plan.plan_id,
                "validation_errors": plan.validation_errors,
            },
        }
    report = _run_async(
        controller.execute_algorithm_plan(plan, selection_request)
    )
    result = report.results.get(ka_id_norm)
    if result is None:
        return None, {
            "code": "KA_RESULT_UNAVAILABLE",
            "error": "Knowledge Algorithm result is unavailable",
            "status": 422,
        }
    return result, None


def _bounded_int_query(name, default, *, minimum, maximum):
    value = request.args.get(name, default, type=int)
    if value is None:
        value = default
    return max(minimum, min(value, maximum))


def _request_body_object(data):
    if data is None:
        return {}, None
    if not isinstance(data, dict):
        return None, 'JSON body must be an object'
    return data, None


def _request_input_payload(data):
    data, body_error = _request_body_object(data)
    if body_error:
        return None, body_error

    input_data = data.get('input')
    if input_data is None:
        input_data = data.get('data', {})
    if input_data is None:
        input_data = {}
    if not isinstance(input_data, dict):
        return None, 'input/data must be an object'

    context = data.get('context')
    if context is not None:
        if not isinstance(context, dict):
            return None, 'context must be an object'
        input_data = {**input_data, 'context': context}

    return input_data, None


def _layer_sort_key(item):
    layer = str(item[0])
    if layer.upper().startswith('L') and layer[1:].isdigit():
        return (0, int(layer[1:]), layer)
    return (1, layer)


def _iso_datetime(value):
    return value.isoformat() if value else None


def parse_list_field(value):
    """Parse semicolon or comma-separated field into list"""
    if not value:
        return []
    return [v.strip() for v in str(value).replace(';', ',').split(',') if v.strip()]


def _first_text_value(*values):
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None

def format_algorithm(ka):
    """Format algorithm data for API response"""
    ka_id = ka.get('KA_ID') or ka.get('id')
    ka_name = ka.get('KA_Name') or ka.get('name') or ka_id
    purpose = _first_text_value(
        ka.get('Purpose'),
        ka.get('purpose'),
        ka.get('description'),
        ka.get('Notes'),
    )

    return {
        'id': ka_id,
        'name': ka_name,
        'short_name': ka.get('Short_Name'),
        'purpose': purpose,
        'description': purpose,
        'category': ka.get('Category'),
        'primary_layers': parse_list_field(ka.get('Primary_Layers')),
        'allowed_layers': parse_list_field(ka.get('Allowed_Layers')),
        'inputs': parse_list_field(ka.get('Inputs')),
        'outputs': parse_list_field(ka.get('Outputs')),
        'capabilities': {
            'reads_memory': ka.get('Reads_Memory') == 'Yes',
            'writes_memory': ka.get('Writes_Memory') == 'Yes',
            'can_invoke_chaos': ka.get('Can_Invoke_Chaos') == 'Yes',
            'can_invoke_external_research': ka.get('Can_Invoke_External_Research') == 'Yes',
            'can_trigger_recursion': ka.get('Can_Trigger_Recursion') == 'Yes',
            'can_veto': ka.get('Can_Veto') == 'Yes'
        },
        'risk_class': ka.get('Risk_Class'),
        'confidence_impact': ka.get('Confidence_Impact'),
        'entropy_signal': ka.get('Entropy_Signal'),
        'dependencies': parse_list_field(ka.get('Dependencies')),
        'produces_artifacts': ka.get('Produces_Artifacts') == 'Yes',
        'audit_events': ka.get('Audit_Events') == 'Yes',
        'version': ka.get('Version'),
        'owner': ka.get('Owner'),
        'status': ka.get('Status') or 'Unknown',
        'classification': ka.get('classification'),
        'production_enabled': bool(ka.get('production_enabled')),
        'deterministic': bool(ka.get('deterministic')),
        'guarantee': ka.get('guarantee'),
        'limitations': ka.get('limitations'),
        'catalog_version': ka.get('version'),
        'notes': ka.get('Notes'),
        'implementation': {
            'mode': ka.get('Implementation_Mode'),
            'runtime_env': ka.get('Runtime_Env'),
            'primary_libraries': parse_list_field(ka.get('Primary_Libraries')),
            'primary_library_versions': ka.get('Primary_Library_Versions'),
            'fallback_libraries': parse_list_field(ka.get('Fallback_Libraries')),
            'fallback_library_versions': ka.get('Fallback_Library_Versions'),
            'test_harness': ka.get('Test_Harness')
        },
        'math': {
            'has_math': ka.get('Has_Math') == 'Yes',
            'component_type': ka.get('Math_Component_Type'),
            'object_ids': ka.get('Math_Object_IDs'),
            'scope': ka.get('Math_Scope'),
            'variables_used': ka.get('Variables_Used'),
            'units_normalization': ka.get('Units_Normalization'),
            'assumptions_constraints': ka.get('Assumptions_Constraints')
        }
    }

def _parse_ka_id_param(ka_id):
    """
    Normalize a URL ka_id param (e.g. 'KA-001', 'KA-1', '1') to the
    controller's canonical form ('ka-001').
    Returns (ka_id_norm, error_response) where error_response is None on success.
    """
    if isinstance(ka_id, str) and ka_id.upper().startswith('KA-'):
        try:
            num = int(ka_id.upper().replace('KA-', '').lstrip('0') or '0')
        except ValueError:
            return None, _error_response('Invalid algorithm ID', 400)
    else:
        try:
            num = int(ka_id)
        except (ValueError, TypeError):
            return None, _error_response('Invalid algorithm ID', 400)
    return _get_controller()._normalize_ka_id(f"KA-{num:03d}"), None


@ka_bp.route('/history', methods=['GET'])
@api_login_required
def get_execution_history():
    """Return the retained device-local legacy feed for desktop sessions only."""
    scope_error = _require_ka_scope("ka:read")
    if scope_error:
        return scope_error
    if _current_api_key() is not None:
        return jsonify({
            "success": False,
            "error": "Legacy KA history is not available to external clients",
            "code": "KA_LEGACY_HISTORY_RETIRED",
            "successor": "/api/v1/ka/runs",
        }), 410
    try:
        from models import KAExecution

        limit = _bounded_int_query('limit', 50, minimum=1, maximum=200)
        executions = (
            KAExecution.query
            .order_by(KAExecution.started_at.desc(), KAExecution.id.desc())
            .limit(limit)
            .all()
        )

        risk_tier_map = {
            'low': 'read_only',
            'medium': 'write',
            'high': 'destructive',
            'critical': 'destructive',
        }

        def _metadata_for(ka_id):
            try:
                ka_id_norm = _get_controller()._normalize_ka_id(ka_id)
            except Exception:
                ka_id_norm = ka_id
            algorithms = _get_controller().get_available_algorithms()
            info = algorithms.get(ka_id_norm) or algorithms.get(ka_id) or {}
            return ka_id_norm, info.get('metadata') or {}

        def _risk_tier(metadata):
            rc = (metadata.get('Risk_Class') or '').lower()
            return risk_tier_map.get(rc, 'read_only')

        def _ka_name(ka_id_norm, metadata):
            return metadata.get('KA_Name') or metadata.get('name') or ka_id_norm

        def _status(raw):
            normalized = str(raw or '').lower()
            if normalized in {'completed', 'success', 'succeeded'}:
                return 'success'
            if normalized in {'failed', 'failure', 'error'}:
                return 'failure'
            return 'blocked'

        def _trace_run_id(execution):
            for payload in (execution.output_data, execution.input_data):
                if isinstance(payload, dict):
                    run_id = payload.get('run_id') or payload.get('trace_run_id')
                    if run_id:
                        return str(run_id)
            return None

        records = []
        for execution in executions:
            ka_id_norm, metadata = _metadata_for(execution.ka_id)
            records.append({
                'id': str(execution.id),
                'ka_id': ka_id_norm,
                'ka_name': _ka_name(ka_id_norm, metadata),
                'risk_tier': _risk_tier(metadata),
                'status': _status(execution.status),
                'triggered_by': 'user',
                'run_id': _trace_run_id(execution),
                'duration_ms': execution.execution_time_ms,
                'created_at': _iso_datetime(execution.started_at or execution.completed_at),
                'error': execution.error_message,
            })

        return jsonify({'success': True, 'executions': records}), 200
    except Exception:
        logger.exception("Error fetching execution history")
        return jsonify({
            'success': False,
            'executions': [],
            'error': 'Execution history is unavailable',
        }), 500


@ka_bp.route('/runs/plan', methods=['POST'])
@api_login_required
def create_product_run_plan():
    """Create one durable manifest-selected KA plan without executing it."""
    scope_error = _require_ka_scope("ka:plan")
    if scope_error:
        return scope_error
    try:
        validated = validate_plan_request(request.get_json(silent=True))
        api_key = _current_api_key()
        run, plan, confirmation_token, replayed = plan_product_run(
            validated,
            user_id=_current_user_id(),
            api_key_id=str(api_key.id) if api_key is not None else None,
            tenant_id=_current_tenant_id(),
            scopes=_current_ka_scopes(),
            retention_hours=int(
                current_app.config.get("DLE_KA_PRODUCT_RETENTION_HOURS", 24)
            ),
            confirmation_ttl_minutes=int(
                current_app.config.get(
                    "DLE_KA_CONFIRMATION_TTL_MINUTES",
                    15,
                )
            ),
        )
        payload = {
            "success": bool(plan.get("valid")),
            "run": _product_run_envelope(run),
            "plan": plan,
            "confirmation_token": confirmation_token,
        }
        response = jsonify(payload)
        response.headers["Location"] = f"/api/v1/ka/runs/{run.id}"
        if replayed:
            response.headers["Idempotent-Replay"] = "true"
        return response, 200 if replayed else 201
    except KAProductWorkflowError as exc:
        return _workflow_error_response(exc)
    except Exception:
        logger.exception("Error creating KA product plan")
        return _error_response("Knowledge Algorithm plan could not be created", 500)


@ka_bp.route('/runs', methods=['GET'])
@api_login_required
def list_product_runs():
    """List content-free KA product runs owned by the current principal."""
    scope_error = _require_ka_scope("ka:read")
    if scope_error:
        return scope_error
    from models import KAProductRun

    limit = _bounded_int_query("limit", 50, minimum=1, maximum=200)
    query = KAProductRun.query.filter(
        KAProductRun.user_id == _current_user_id(),
        KAProductRun.expires_at > datetime.now(UTC),
    )
    api_key = _current_api_key()
    principal_key = str(api_key.id) if api_key is not None else "desktop"
    query = query.filter_by(principal_key=principal_key)
    runs = query.order_by(
        KAProductRun.created_at.desc(),
        KAProductRun.id.desc(),
    ).limit(limit).all()
    return jsonify({
        "success": True,
        "runs": [_product_run_envelope(run) for run in runs],
    })


@ka_bp.route('/runs/<run_id>', methods=['GET'])
@api_login_required
def get_product_run(run_id):
    scope_error = _require_ka_scope("ka:read")
    if scope_error:
        return scope_error
    run, lookup_error = _product_run_for_principal(run_id)
    if lookup_error:
        return lookup_error
    return jsonify({
        "success": True,
        "run": _product_run_envelope(run),
        "plan": dict(run.plan_payload),
    })


@ka_bp.route('/runs/<run_id>/execute', methods=['POST'])
@api_login_required
def execute_product_run(run_id):
    """Confirm the exact plan when required and queue canonical execution."""
    scope_error = _require_ka_scope("ka:execute")
    if scope_error:
        return scope_error
    run, lookup_error = _product_run_for_principal(run_id)
    if lookup_error:
        return lookup_error
    data = request.get_json(silent=True)
    if data is None:
        data = {}
    if not isinstance(data, dict):
        return _error_response("JSON body must be an object", 400)
    try:
        confirm_and_queue_product_run(
            run,
            confirmation_token=data.get("confirmation_token"),
        )
        get_ka_product_runner(
            current_app._get_current_object()
        ).submit(str(run.id))
        response = jsonify({
            "success": True,
            "run": _product_run_envelope(run),
        })
        response.headers["Location"] = f"/api/v1/ka/runs/{run.id}"
        response.headers["Retry-After"] = "1"
        return response, 202
    except KAProductWorkflowError as exc:
        return _workflow_error_response(exc)
    except Exception:
        logger.exception("Error queueing KA product run")
        return _error_response("Knowledge Algorithm run could not be queued", 500)


@ka_bp.route('/runs/<run_id>/cancel', methods=['POST'])
@api_login_required
def cancel_product_run(run_id):
    """Cancel a planned/queued run or request cooperative running cancellation."""
    scope_error = _require_ka_scope("ka:cancel")
    if scope_error:
        return scope_error
    run, lookup_error = _product_run_for_principal(run_id)
    if lookup_error:
        return lookup_error
    if run.status in TERMINAL_STATES:
        return jsonify({
            "success": False,
            "error": "Knowledge Algorithm run is already terminal",
            "code": "KA_RUN_TERMINAL",
            "run": _product_run_envelope(run),
        }), 409
    from extensions import db

    runner = get_ka_product_runner(current_app._get_current_object())
    runner.cancel(run)
    if run.status in {"planned", "queued"}:
        run.status = "cancelled"
        run.completed_at = datetime.now(UTC)
    db.session.commit()
    return jsonify({
        "success": True,
        "run": _product_run_envelope(run),
    }), 202


def _completed_product_payload(run):
    if run.status in {"planned", "queued", "running"}:
        response = jsonify({
            "success": True,
            "run": _product_run_envelope(run),
        })
        response.headers["Retry-After"] = "1"
        return None, (response, 202)
    try:
        return decrypt_product_result(run), None
    except KAProductWorkflowError as exc:
        return None, _workflow_error_response(exc)


@ka_bp.route('/runs/<run_id>/result', methods=['GET'])
@api_login_required
def get_product_run_result(run_id):
    scope_error = _require_ka_scope("ka:read")
    if scope_error:
        return scope_error
    run, lookup_error = _product_run_for_principal(run_id)
    if lookup_error:
        return lookup_error
    result, pending_or_error = _completed_product_payload(run)
    if pending_or_error:
        return pending_or_error
    return jsonify({
        "success": run.status in {"succeeded", "partial", "dry_run"},
        "run": _product_run_envelope(run),
        **result,
    })


@ka_bp.route('/runs/<run_id>/trace', methods=['GET'])
@api_login_required
def get_product_run_trace(run_id):
    scope_error = _require_ka_scope("ka:read")
    if scope_error:
        return scope_error
    run, lookup_error = _product_run_for_principal(run_id)
    if lookup_error:
        return lookup_error
    result, pending_or_error = _completed_product_payload(run)
    if pending_or_error:
        return pending_or_error
    return jsonify({
        "success": True,
        "run": _product_run_envelope(run),
        "trace": trace_summary(result),
    })


@ka_bp.route('/runs/<run_id>/artifacts', methods=['GET'])
@api_login_required
def get_product_run_artifacts(run_id):
    scope_error = _require_ka_scope("ka:read")
    if scope_error:
        return scope_error
    run, lookup_error = _product_run_for_principal(run_id)
    if lookup_error:
        return lookup_error
    result, pending_or_error = _completed_product_payload(run)
    if pending_or_error:
        return pending_or_error
    return jsonify({
        "success": True,
        "run": _product_run_envelope(run),
        "artifacts": result_artifacts(result),
    })


@ka_bp.route('/runs/<run_id>/effects', methods=['GET'])
@api_login_required
def get_product_run_effects(run_id):
    scope_error = _require_ka_scope("ka:read")
    if scope_error:
        return scope_error
    run, lookup_error = _product_run_for_principal(run_id)
    if lookup_error:
        return lookup_error
    result, pending_or_error = _completed_product_payload(run)
    if pending_or_error:
        return pending_or_error
    return jsonify({
        "success": True,
        "run": _product_run_envelope(run),
        "effects": result_effects(result),
    })


@ka_bp.route('/algorithms', methods=['GET'])
@api_login_required
def list_algorithms():
    """List all available Knowledge Algorithms"""
    scope_error = _require_ka_scope("ka:read")
    if scope_error:
        return scope_error
    try:
        category = request.args.get('category')
        status = request.args.get('status')
        risk_class = request.args.get('risk_class')
        layer = request.args.get('layer')
        page = _bounded_int_query('page', 1, minimum=1, maximum=100000)
        per_page = _bounded_int_query('per_page', 50, minimum=1, maximum=300)

        live_registry = _get_controller().get_available_algorithms()
        algorithms = [
            format_algorithm(ka.get("metadata", {}))
            for ka in live_registry.values()
            if ka.get("metadata")
        ]
        if not algorithms:
            algorithms = [
                format_algorithm({"KA_ID": k, "KA_Name": k})
                for k in _get_controller().algorithms.keys()
            ]

        if category:
            algorithms = [a for a in algorithms if a['category'] and a['category'].lower() == category.lower()]
        if status:
            algorithms = [a for a in algorithms if a['status'] and a['status'].lower() == status.lower()]
        if risk_class:
            algorithms = [a for a in algorithms if a['risk_class'] and a['risk_class'].lower() == risk_class.lower()]
        if layer:
            algorithms = [a for a in algorithms if layer in a['primary_layers'] or layer in a['allowed_layers']]

        algorithms.sort(key=lambda x: x.get('id') or '')

        total = len(algorithms)
        start = (page - 1) * per_page
        end = start + per_page
        paginated = algorithms[start:end]

        categories = sorted({
            ka.get('Category')
            for ka in (v.get('metadata', {}) for v in live_registry.values())
            if ka.get('Category')
        })

        return jsonify({
            'success': True,
            'algorithms': paginated,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            },
            'categories': categories,
            'total_count': len(live_registry)
        }), 200
    except Exception:
        logger.exception("Error listing algorithms")
        return _error_response('Algorithm list is unavailable', 500)


@ka_bp.route('/algorithms/<ka_id>', methods=['GET'])
@api_login_required
def get_algorithm(ka_id):
    """Get public manifest detail for one canonical or approved alias ID."""
    scope_error = _require_ka_scope("ka:read")
    if scope_error:
        return scope_error
    try:
        ka_id_norm, err = _parse_ka_id_param(ka_id)
        if err:
            return err

        if ka_id_norm not in _get_controller().algorithms:
            return _error_response('Algorithm not found', 404)

        controller = _get_controller()
        ka_data = controller.algorithms[ka_id_norm].get("metadata", {})
        definition = controller._canonical_controller.manifest.entries[ka_id_norm]
        algorithm = format_algorithm(ka_data)
        algorithm["runtime_contract"] = definition.model_dump(
            mode="json",
            exclude={"implementation": {"entrypoint"}},
        )
        return jsonify({'success': True, 'algorithm': algorithm}), 200
    except Exception:
        logger.exception("Error getting algorithm")
        return _error_response('Algorithm details are unavailable', 500)


@ka_bp.route('/algorithms/<ka_id>/execute', methods=['POST'])
@api_login_required
def execute_algorithm(ka_id):
    """Compatibility execution through the canonical selector and plan executor."""
    scope_error = _require_ka_scope("ka:execute")
    if scope_error:
        return scope_error
    try:
        ka_id_norm, err = _parse_ka_id_param(ka_id)
        if err:
            return err

        if ka_id_norm not in _get_controller().algorithms:
            return _error_response('Algorithm not found', 404)

        request_data = request.get_json()
        input_data, payload_error = _request_input_payload(request_data)
        if payload_error:
            return _error_response(payload_error, 400)

        metadata = _get_controller().algorithms[ka_id_norm].get("metadata", {})
        allow_nonproduction = bool(
            isinstance(request_data, dict) and request_data.get("allow_nonproduction") is True
        )
        if metadata.get("production_enabled") is False and not allow_nonproduction:
            return jsonify({
                'success': False,
                'error': 'Algorithm is not enabled for production execution',
                'code': 'KA_NONPRODUCTION_OPT_IN_REQUIRED',
                'classification': metadata.get('classification'),
                'limitations': metadata.get('limitations'),
            }), 409

        ka_result, plan_error = _execute_compatibility_plan(
            ka_id_norm,
            input_data,
            allow_nonproduction=allow_nonproduction,
        )
        if plan_error:
            status = plan_error.pop("status")
            return jsonify({"success": False, **plan_error}), status

        result = {
            'algorithm_id': ka_id_norm,
            'executed_at': datetime.now(UTC).isoformat(),
            'status': 'completed' if ka_result.success else 'failed',
            'output': ka_result.output,
            'log': '',
            'execution_time_ms': int(ka_result.duration_ms),
            'trace_id': ka_result.trace_id,
            'canonical_result': ka_result.model_dump(
                mode='json',
                exclude_none=True,
            ),
        }

        logger.info("Executed %s for user %s", ka_id_norm, _current_user_id())

        return jsonify({'success': ka_result.success, 'result': result}), (
            200 if ka_result.success else 422
        )
    except Exception:
        logger.exception("Error executing algorithm")
        return _error_response('Algorithm execution failed', 500)


@ka_bp.route('/categories', methods=['GET'])
@api_login_required
def list_categories():
    """List all KA categories with their algorithms"""
    scope_error = _require_ka_scope("ka:read")
    if scope_error:
        return scope_error
    try:
        categories = {}
        for ka_id, ka_info in _get_controller().get_available_algorithms().items():
            ka = ka_info.get("metadata", {})
            cat = ka.get('Category')
            if not cat:
                continue
            if cat not in categories:
                categories[cat] = {'name': cat, 'algorithms': [], 'count': 0}
            categories[cat]['algorithms'].append({
                'id': ka.get('KA_ID'),
                'name': ka.get('KA_Name'),
                'short_name': ka.get('Short_Name'),
                'status': ka.get('Status')
            })
            categories[cat]['count'] += 1

        for cat in categories.values():
            cat['algorithms'].sort(key=lambda x: x.get('id') or '')

        return jsonify({
            'success': True,
            'categories': categories,
            'category_list': sorted(categories.keys()),
            'count': len(categories)
        }), 200
    except Exception:
        logger.exception("Error listing categories")
        return _error_response('Algorithm categories are unavailable', 500)


@ka_bp.route('/workflow/high-stakes', methods=['POST'])
@api_login_required
def execute_high_stakes_workflow():
    """Execute the full 12-step high-stakes refinement workflow."""
    scope_error = _require_ka_scope("ka:execute")
    if scope_error:
        return scope_error
    try:
        data, body_error = _request_body_object(request.get_json())
        if body_error:
            return _error_response(body_error, 400)
        query = data.get('query')
        if not query:
            return jsonify({'success': False, 'error': 'Query is required'}), 400

        context = data.get('context', {})
        if context is None:
            context = {}
        if not isinstance(context, dict):
            return jsonify({'success': False, 'error': 'context must be an object'}), 400

        from backend.truth_engine.api import get_truth_core_engine
        engine = get_truth_core_engine()

        session = _run_async(engine.create_session(
            query=query,
            user_id=_current_user_id(),
            tier='high_stakes',
            context=context
        ))

        result = _run_async(engine.process(session['session_id']))

        governed = result.get('result') if isinstance(result.get('result'), dict) else {}
        success = bool(governed.get('ok'))
        return jsonify({
            'success': success,
            'session_id': session['session_id'],
            'result': result
        }), 200 if success else 503
    except Exception:
        logger.exception("Error executing high-stakes workflow")
        return _error_response('High-stakes workflow execution failed', 500)


@ka_bp.route('/trace/<session_id>', methods=['GET'])
@api_login_required
def get_workflow_trace(session_id):
    """Get the execution trace of a workflow session."""
    scope_error = _require_ka_scope("ka:read")
    if scope_error:
        return scope_error
    try:
        from backend.truth_engine.api import get_truth_core_engine
        engine = get_truth_core_engine()

        status = engine.get_session_status(session_id)
        if 'error' in status:
            return _error_response('Workflow trace not found', 404)

        return jsonify({
            'success': True,
            'session_id': session_id,
            'trace': status.get('workflow_steps', []),
            'status': status.get('status')
        }), 200
    except Exception:
        logger.exception("Error getting workflow trace")
        return _error_response('Workflow trace is unavailable', 500)


@ka_bp.route('/layers', methods=['GET'])
@api_login_required
def list_layers():
    """List all simulation layers and their associated algorithms"""
    scope_error = _require_ka_scope("ka:read")
    if scope_error:
        return scope_error
    try:
        layers = {}
        for ka_id, ka_info in _get_controller().get_available_algorithms().items():
            ka = ka_info.get("metadata", {})
            primary = parse_list_field(ka.get('Primary_Layers'))
            allowed = parse_list_field(ka.get('Allowed_Layers'))
            all_layers = set(primary + allowed)

            for layer in all_layers:
                if layer not in layers:
                    layers[layer] = {
                        'layer': layer,
                        'primary_algorithms': [],
                        'allowed_algorithms': []
                    }

                algo_info = {
                    'id': ka.get('KA_ID'),
                    'name': ka.get('KA_Name'),
                    'short_name': ka.get('Short_Name')
                }

                if layer in primary:
                    layers[layer]['primary_algorithms'].append(algo_info)
                elif layer in allowed:
                    layers[layer]['allowed_algorithms'].append(algo_info)

        sorted_layers = dict(sorted(
            layers.items(),
            key=_layer_sort_key
        ))

        return jsonify({'success': True, 'layers': sorted_layers, 'count': len(layers)}), 200
    except Exception:
        logger.exception("Error listing layers")
        return _error_response('Algorithm layers are unavailable', 500)


@ka_bp.route('/batch', methods=['POST'])
@api_login_required
def batch_execute():
    """Execute multiple Knowledge Algorithms in sequence"""
    scope_error = _require_ka_scope("ka:execute")
    if scope_error:
        return scope_error
    try:
        data, body_error = _request_body_object(request.get_json())
        if body_error:
            return _error_response(body_error, 400)

        algorithm_ids = data.get('algorithms', [])

        if not algorithm_ids:
            return jsonify({'success': False, 'error': 'No algorithms specified'}), 400

        if not isinstance(algorithm_ids, list):
            return jsonify({'success': False, 'error': 'algorithms must be a list'}), 400

        if len(algorithm_ids) > 20:
            return jsonify({'success': False, 'error': 'Maximum 20 algorithms per batch'}), 400

        input_data, payload_error = _request_input_payload(data)
        if payload_error:
            return _error_response(payload_error, 400)
        allow_nonproduction = data.get("allow_nonproduction") is True

        results = []
        for ka_id in algorithm_ids:
            ka_id_norm, ka_id_error = _parse_ka_id_param(ka_id)
            if ka_id_error:
                results.append({
                    'ka_id': None,
                    'status': 'error',
                    'error': 'Invalid algorithm ID'
                })
                continue

            if ka_id_norm not in _get_controller().algorithms:
                results.append({
                    'ka_id': ka_id_norm,
                    'status': 'error',
                    'error': 'Algorithm not found'
                })
                continue

            ka_meta = _get_controller().algorithms[ka_id_norm].get("metadata", {})
            if ka_meta.get("production_enabled") is False and not allow_nonproduction:
                results.append({
                    'ka_id': ka_id_norm,
                    'status': 'blocked',
                    'error': 'Algorithm is not enabled for production execution',
                    'code': 'KA_NONPRODUCTION_OPT_IN_REQUIRED',
                    'classification': ka_meta.get('classification'),
                })
                continue

            try:
                ka_result, plan_error = _execute_compatibility_plan(
                    ka_id_norm,
                    input_data,
                    allow_nonproduction=allow_nonproduction,
                )
                if plan_error:
                    results.append({
                        "ka_id": ka_id_norm,
                        "status": "blocked",
                        "error": plan_error["error"],
                        "code": plan_error["code"],
                    })
                    continue
                results.append({
                    'ka_id': ka_meta.get('KA_ID', ka_id_norm),
                    'name': ka_meta.get('KA_Name') or ka_meta.get('KA_ID') or ka_id_norm,
                    'short_name': ka_meta.get('Short_Name'),
                    'category': ka_meta.get('Category'),
                    'status': 'completed' if ka_result.success else 'failed',
                    'output': ka_result.output,
                    'execution_time_ms': int(ka_result.duration_ms),
                    'layers_used': parse_list_field(ka_meta.get('Primary_Layers')),
                    'trace_id': ka_result.trace_id,
                    'canonical_result': ka_result.model_dump(
                        mode='json',
                        exclude_none=True,
                    ),
                })
            except Exception:
                logger.exception("Batch execution error for %s", ka_id_norm)
                results.append({
                    'ka_id': ka_id_norm,
                    'status': 'error',
                    'error': 'Algorithm execution failed'
                })

        return jsonify({
            'success': True,
            'results': results,
            'executed_count': len([r for r in results if r['status'] == 'completed']),
            'failed_count': len([r for r in results if r['status'] in ('error', 'failed')])
        }), 200
    except Exception:
        logger.exception("Error in batch execution")
        return _error_response('Batch execution failed', 500)


@ka_bp.route('/search', methods=['GET'])
@api_login_required
def search_algorithms():
    """Search algorithms by name, purpose, or notes"""
    scope_error = _require_ka_scope("ka:read")
    if scope_error:
        return scope_error
    try:
        query = request.args.get('q', '').lower()
        if not query or len(query) < 2:
            return jsonify({'success': False, 'error': 'Query must be at least 2 characters'}), 400

        results = []
        for ka_id, ka_info in _get_controller().get_available_algorithms().items():
            ka = ka_info.get("metadata", {})
            name = (ka.get('KA_Name') or '').lower()
            purpose = (_first_text_value(ka.get('Purpose'), ka.get('purpose'), ka.get('description')) or '').lower()
            notes = (ka.get('Notes') or '').lower()
            short_name = (ka.get('Short_Name') or '').lower()

            if query in name or query in purpose or query in notes or query in short_name:
                results.append(format_algorithm(ka))

        results.sort(key=lambda x: x.get('id') or '')

        return jsonify({'success': True, 'query': query, 'results': results, 'count': len(results)}), 200
    except Exception:
        logger.exception("Error searching algorithms")
        return _error_response('Algorithm search is unavailable', 500)


@ka_bp.route('/dependencies/<ka_id>', methods=['GET'])
@api_login_required
def get_dependencies(ka_id):
    """Get dependency graph for a specific algorithm"""
    scope_error = _require_ka_scope("ka:read")
    if scope_error:
        return scope_error
    try:
        ka_id_norm, err = _parse_ka_id_param(ka_id)
        if err:
            return err

        if ka_id_norm not in _get_controller().algorithms:
            return _error_response('Algorithm not found', 404)

        ka_data = _get_controller().algorithms[ka_id_norm].get("metadata", {})
        dependencies = parse_list_field(ka_data.get('Dependencies'))

        dep_details = []
        for dep in dependencies:
            dep_id = _get_controller()._normalize_ka_id(dep)
            if dep_id in _get_controller().algorithms:
                dep_ka = _get_controller().algorithms[dep_id].get("metadata", {})
                dep_details.append({
                    'id': dep_ka.get('KA_ID'),
                    'name': dep_ka.get('KA_Name'),
                    'short_name': dep_ka.get('Short_Name'),
                    'category': dep_ka.get('Category'),
                    'status': dep_ka.get('Status')
                })

        dependents = []
        for other_id, other_info in _get_controller().get_available_algorithms().items():
            other_ka = other_info.get("metadata", {})
            other_deps = parse_list_field(other_ka.get('Dependencies'))
            if ka_id_norm in [_get_controller()._normalize_ka_id(d) for d in other_deps]:
                dependents.append({
                    'id': other_ka.get('KA_ID'),
                    'name': other_ka.get('KA_Name'),
                    'short_name': other_ka.get('Short_Name'),
                    'category': other_ka.get('Category')
                })

        return jsonify({
            'success': True,
            'algorithm': {'id': ka_data.get('KA_ID'), 'name': ka_data.get('KA_Name')},
            'dependencies': dep_details,
            'dependents': dependents,
            'dependency_count': len(dep_details),
            'dependent_count': len(dependents)
        }), 200
    except Exception:
        logger.exception("Error getting dependencies")
        return _error_response('Algorithm dependencies are unavailable', 500)


@ka_bp.route('/stats', methods=['GET'])
@api_login_required
def get_stats():
    """Get KA system statistics"""
    scope_error = _require_ka_scope("ka:read")
    if scope_error:
        return scope_error
    try:
        live_registry = _get_controller().get_available_algorithms()
        categories = {}
        risk_classes = {}
        statuses = {}
        impl_modes = {}
        has_math_count = 0

        for ka_info in live_registry.values():
            ka = ka_info.get("metadata", {})
            cat = ka.get('Category')
            if cat:
                categories[cat] = categories.get(cat, 0) + 1
            risk = ka.get('Risk_Class')
            if risk:
                risk_classes[risk] = risk_classes.get(risk, 0) + 1
            status = ka.get('Status')
            if status:
                statuses[status] = statuses.get(status, 0) + 1
            impl = ka.get('Implementation_Mode')
            if impl:
                impl_modes[impl] = impl_modes.get(impl, 0) + 1
            if ka.get('Has_Math') == 'Yes':
                has_math_count += 1

        return jsonify({
            'success': True,
            'stats': {
                'total_algorithms': len(live_registry),
                'by_category': categories,
                'by_risk_class': risk_classes,
                'by_status': statuses,
                'by_implementation_mode': impl_modes,
                'with_math_components': has_math_count
            }
        }), 200
    except Exception:
        logger.exception("Error getting stats")
        return _error_response('Algorithm statistics are unavailable', 500)


@ka_bp.route('/health', methods=['GET'])
def health_check():
    """Check KA system health"""
    algorithms = _get_controller().get_available_algorithms()
    available = len(algorithms) > 0
    return jsonify({
        'success': True,
        'status': 'healthy' if available else 'degraded',
        'total_algorithms': len(algorithms),
        'available': available,
        'version': _get_controller()._canonical_controller.manifest.manifest_version,
        'registry_source': 'canonical_runtime_manifest'
    }), 200
