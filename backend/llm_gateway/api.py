# ruff: noqa: E402
"""
LLM Gateway API Endpoints

Provides the public API for external clients to access UKG-enhanced LLM.
Also includes admin endpoints for provider and API key management.
"""

import asyncio
from datetime import datetime, timedelta, UTC
from functools import wraps
from flask import Blueprint, request, jsonify, Response, stream_with_context, g
from flask_login import current_user
import json
import logging
import os
import uuid
from typing import Optional

from models import (
    LLMProvider,
    LLMProviderUsage,
    ExternalAPIKey,
    ChatSession,
    ChatMessage,
    PromptTemplate,
    ModelRoutingPolicy,
    AIAuditEvent,
)
from backend.llm_gateway.gateway import LLMGateway, NetworkState
from backend.governed_execution import GovernedRequest
from backend.llm_gateway.model_defaults import SUPPORTED_PROVIDER_TYPES, default_model_for_provider
from backend.llm_gateway.provider_manifest import normalize_provider_type, validate_provider_model
from backend.llm_gateway.provider_errors import (
    ProviderFailureClass,
    classify_provider_failure,
)
from backend.llm_gateway.provider_budget import ProviderBudgetPolicy
from backend.llm_gateway.schemas import GatewayChatRequest
from backend.auth.api_decorators import (
    api_session_login_required,
    current_user_is_owner,
    get_authenticated_principal,
)
from backend.desktop.offline_queue import (
    REPLAYABLE_FAILURE_CLASSES,
    delete_item,
    enqueue_chat_request,
    list_queue,
    mark_item,
)
from backend.governed_execution.cancellation import CANCELLATION_REGISTRY
from backend.storage.runtime_settings import get_offline_queue_enabled
from backend.utils.request_validation import validate_pydantic_payload
from backend.utils.error_normalization import normalize_public_error_message
try:
    from extensions import db, cache, limiter
except ImportError:
    # Final fallback for unusual packaging contexts
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from extensions import db, cache, limiter

logger = logging.getLogger(__name__)

gateway_bp = Blueprint('gateway', __name__, url_prefix='/api/v1/gateway')
admin_bp = Blueprint('gateway_admin', __name__, url_prefix='/api/admin')


def _parse_uuid_or_404(value: str, field_name: str):
    """Parse UUID path params and provide consistent 404-style errors."""
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError, AttributeError):
        return jsonify({'error': f'Invalid {field_name}'}), 404


def _normalize_allowlist(values) -> set[str]:
    """Normalize provider/model allowlists from API key records."""
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, (list, tuple, set)):
        return set()

    normalized: set[str] = set()
    for value in values:
        if value is None:
            continue
        text = str(value).strip().lower()
        if text:
            normalized.add(text)
    return normalized


def _cache_counter_value(raw_value) -> int:
    """Coerce cache counter values to int safely."""
    if raw_value is None:
        return 0
    if isinstance(raw_value, bytes):
        raw_value = raw_value.decode('utf-8', errors='ignore')
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return 0


def _positive_int(value):
    """Parse positive integer values from model fields/config."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _public_gateway_error(raw_error: Optional[str], fallback: str = "Gateway request failed") -> str:
    """Sanitize provider/internal failures before returning API responses."""
    return normalize_public_error_message(raw_error=raw_error, fallback=fallback)


def _provider_failure_class(response) -> Optional[str]:
    failure = getattr(response, "failure", None)
    if not isinstance(failure, dict):
        return None
    details = failure.get("details") if isinstance(failure.get("details"), dict) else {}
    provider_failure = (
        details.get("provider_failure")
        if isinstance(details.get("provider_failure"), dict)
        else {}
    )
    classified = str(provider_failure.get("class") or "").strip().lower()
    if classified:
        return classified
    kind = str(failure.get("kind") or "").strip().lower()
    return "timeout" if kind == "timeout" else None


def _audit_trail_for_run(run_id: Optional[str]) -> Optional[dict]:
    """Build the frontend trace contract for a gateway run."""
    if not run_id:
        return None
    return {
        "decision_path": f"/api/v1/trace/runs/{run_id}",
        "complete_trace_url": f"/api/v1/trace/runs/{run_id}/bundle",
        "download_url": f"/api/v1/trace/runs/{run_id}/export",
    }


def _trace_summary_for_response(response) -> Optional[dict]:
    """Translate gateway trace records into the renderer's progress contract."""
    trace = getattr(response, "trace", None)
    if not isinstance(trace, list) or not trace:
        return None

    steps = []
    for index, item in enumerate(trace):
        if not isinstance(item, dict):
            continue
        raw_status = str(item.get("status") or "completed").lower()
        status = {
            "ok": "completed",
            "pass": "completed",
            "completed": "completed",
            "running": "processing",
            "fail": "error",
            "failed": "error",
        }.get(raw_status, "pending")
        steps.append({
            "id": str(item.get("ka_id") or f"stage-{index + 1}"),
            "name": str(item.get("stage_name") or item.get("ka_id") or f"Stage {index + 1}"),
            "status": status,
            "durationMs": item.get("duration_ms"),
            "percentage": 100 if status == "completed" else 0,
            "details": item.get("output") if isinstance(item.get("output"), dict) else {},
            "timestamp": item.get("end_time") or item.get("start_time") or datetime.now(UTC).isoformat(),
        })

    if not steps:
        return None
    latency_ms = getattr(response, "usage", {}).get("latency_ms", 0)
    return {
        "currentStepId": steps[-1]["id"],
        "steps": steps,
        "totalDurationMs": latency_ms,
        "estimatedTotalMs": latency_ms,
        "overallProgress": 100 if all(step["status"] == "completed" for step in steps) else 0,
    }


def _apply_api_key_request_policy(payload: dict):
    """
    Enforce API key policy controls on gateway requests.

    Returns a Flask response tuple on policy violation, otherwise None.
    """
    api_key = getattr(g, 'api_key', None)
    if not api_key:
        return None

    permissions = api_key.permissions if isinstance(api_key.permissions, dict) else {}
    if permissions:
        can_chat = bool(
            permissions.get('write')
            or permissions.get('chat')
            or permissions.get('read')
        )
        if not can_chat:
            return jsonify({'error': 'API key permission denied'}), 403

    requested_provider = str(payload.get('provider') or '').strip().lower()
    requested_model = str(payload.get('model') or '').strip().lower()

    allowed_providers = _normalize_allowlist(api_key.allowed_providers)
    if allowed_providers and requested_provider and requested_provider not in allowed_providers:
        return jsonify({'error': 'Requested provider is not allowed for this API key'}), 403

    allowed_models = _normalize_allowlist(api_key.allowed_models)
    if allowed_models and requested_model and requested_model not in allowed_models:
        return jsonify({'error': 'Requested model is not allowed for this API key'}), 403

    max_tokens_allowed = _positive_int(api_key.max_tokens_per_request)
    max_tokens_requested = payload.get('max_tokens')
    if max_tokens_allowed and max_tokens_requested is not None:
        try:
            parsed_max_tokens = int(max_tokens_requested)
        except (TypeError, ValueError):
            return jsonify({'error': 'max_tokens must be an integer'}), 400
        if parsed_max_tokens > max_tokens_allowed:
            return jsonify({
                'error': 'Requested max_tokens exceeds API key policy',
                'max_tokens_per_request': max_tokens_allowed,
            }), 400

    meta = payload.get('meta')
    if not isinstance(meta, dict):
        meta = {}
        payload['meta'] = meta

    if permissions:
        meta['api_key_permissions'] = permissions
    if allowed_providers:
        meta['allowed_provider_types'] = sorted(allowed_providers)
    if allowed_models:
        meta['allowed_models'] = sorted(allowed_models)

    return None


def _gateway_failure_http_status(response) -> tuple[int, str]:
    """Map the typed governed/provider failure to a truthful public HTTP state."""
    failure = getattr(response, 'failure', None)
    if not isinstance(failure, dict):
        return 500, 'GATEWAY_INTERNAL_ERROR'
    details = failure.get('details') if isinstance(failure.get('details'), dict) else {}
    provider_failure = (
        details.get('provider_failure')
        if isinstance(details.get('provider_failure'), dict)
        else {}
    )
    failure_class = str(provider_failure.get('class') or '').strip().lower()
    provider_code = str(provider_failure.get('code') or failure.get('code') or '').strip().upper()
    if provider_code == 'BUDGET_WARNING_CONFIRMATION_REQUIRED':
        return 409, provider_code
    if provider_code.endswith('_HARD_LIMIT'):
        return 429, provider_code
    mapping = {
        ProviderFailureClass.INVALID_KEY.value: (401, 'INVALID_API_KEY'),
        ProviderFailureClass.UNAUTHORIZED_MODEL.value: (403, 'MODEL_NOT_AUTHORIZED'),
        ProviderFailureClass.INVALID_MODEL.value: (422, 'INVALID_MODEL'),
        ProviderFailureClass.QUOTA_EXHAUSTED.value: (429, 'QUOTA_EXHAUSTED'),
        ProviderFailureClass.BILLING_SUSPENDED.value: (402, 'BILLING_SUSPENDED'),
        ProviderFailureClass.RATE_LIMITED.value: (429, 'RATE_LIMITED'),
        ProviderFailureClass.NETWORK.value: (503, 'PROVIDER_NETWORK_ERROR'),
        ProviderFailureClass.PROVIDER_OUTAGE.value: (503, 'PROVIDER_OUTAGE'),
        ProviderFailureClass.TIMEOUT.value: (504, 'PROVIDER_TIMEOUT'),
        ProviderFailureClass.POLICY_BLOCK.value: (403, provider_code or 'POLICY_BLOCK'),
        ProviderFailureClass.MALFORMED_RESPONSE.value: (502, 'MALFORMED_PROVIDER_RESPONSE'),
        ProviderFailureClass.CANCELLED.value: (409, 'REQUEST_CANCELLED'),
        ProviderFailureClass.PERSISTENCE.value: (500, 'PERSISTENCE_FAILED'),
        ProviderFailureClass.INTERNAL.value: (500, 'GATEWAY_INTERNAL_ERROR'),
        ProviderFailureClass.UNKNOWN.value: (500, 'UNKNOWN_PROVIDER_FAILURE'),
    }
    if failure_class in mapping:
        return mapping[failure_class]
    kind = str(failure.get('kind') or '').strip().lower()
    if kind == 'timeout':
        return 504, 'REQUEST_TIMEOUT'
    if kind == 'cancelled':
        return 409, 'REQUEST_CANCELLED'
    if kind == 'policy_block':
        return 403, provider_code or 'POLICY_BLOCK'
    return 500, provider_code or 'GATEWAY_INTERNAL_ERROR'


# ============== API Key Authentication ==============

def api_key_required(f):
    """Decorator for endpoints that accept API key or session auth."""
    import inspect
    @wraps(f)
    async def decorated(*args, **kwargs):
        # Check for API key in header
        auth_header = request.headers.get('Authorization', '')
        api_key = request.headers.get('X-API-Key')
        if not api_key and auth_header.lower().startswith('bearer '):
            api_key = auth_header.split(' ', 1)[1].strip()
        
        if api_key and api_key.startswith('ukg_'):
            # Validate API key
            key_record = ExternalAPIKey.verify_key(api_key)
            if not key_record:
                return jsonify({'error': 'Invalid API key'}), 401

            rpm_limit = _positive_int(getattr(key_record, 'rate_limit_rpm', None))
            daily_limit = _positive_int(getattr(key_record, 'rate_limit_daily', None))

            # Rate Limiting (Redis-backed)
            if cache and rpm_limit:
                limit_key = f"rl:{key_record.id}:{int(datetime.now().timestamp() // 60)}"
                # Use current minute bucket
                current_usage = _cache_counter_value(cache.get(limit_key))
                if current_usage >= rpm_limit:
                    return jsonify({'error': 'Rate limit exceeded', 'limit': f'{rpm_limit}/min'}), 429
                
                cache.set(limit_key, current_usage + 1, timeout=60)

            if cache and daily_limit:
                daily_key = f"rld:{key_record.id}:{datetime.now(UTC).strftime('%Y%m%d')}"
                daily_usage = _cache_counter_value(cache.get(daily_key))
                if daily_usage >= daily_limit:
                    return jsonify({'error': 'Daily rate limit exceeded', 'limit': f'{daily_limit}/day'}), 429

                cache.set(daily_key, daily_usage + 1, timeout=24 * 60 * 60)
            
            # Update usage stats
            key_record.total_requests = (key_record.total_requests or 0) + 1
            key_record.last_used_at = db.func.now()
            db.session.commit()
            
            g.api_key = key_record
            g.user_id = key_record.user_id
            
            if inspect.iscoroutinefunction(f):
                return await f(*args, **kwargs)
            return f(*args, **kwargs)
        
        # Fall back to session auth
        if current_user.is_authenticated:
            g.api_key = None
            g.user_id = current_user.id
            if inspect.iscoroutinefunction(f):
                return await f(*args, **kwargs)
            return f(*args, **kwargs)
        
        return jsonify({'error': 'Authentication required'}), 401
    
    decorated.__dle_auth_guard__ = "gateway-api-key-or-session"
    return decorated


# ============== Gateway Endpoints ==============


from backend.utils.responses import api_response

@gateway_bp.route('/chat', methods=['POST'])
@api_key_required
async def gateway_chat():
    """
    Main gateway endpoint for chat completions.
    """
    raw_data = request.get_json(silent=True) or {}
    if not raw_data.get('messages'):
        return jsonify({'error': 'messages required'}), 400

    validated_payload, validation_error_response = validate_pydantic_payload(
        GatewayChatRequest,
        raw_data,
    )
    if validation_error_response:
        return validation_error_response

    data = validated_payload.model_dump() if validated_payload else {}
    messages = data.get('messages', [])

    policy_error = _apply_api_key_request_policy(data)
    if policy_error:
        return policy_error
        
    gateway_request = GovernedRequest(
        messages=messages,
        request_id=data.get('request_id') or str(uuid.uuid4()),
        provider=data.get('provider'),
        model=data.get('model'),
        mode=data.get('mode', 'standard'),
        constraints=data.get('constraints', {}),
        temperature=data.get('temperature', 0.7),
        max_tokens=data.get('max_tokens') or 1024,
        user_id=g.user_id,
        session_id=data.get('session_id'),
        api_key_id=str(g.api_key.id) if g.api_key else None,
        metadata={
            **data.get('meta', {}),
            "legacy_run_ukg_pipeline": data.get('run_ukg_pipeline', True),
        },
        source="external_gateway" if g.api_key else "desktop_gateway",
        principal_kind="external_client" if g.api_key else "desktop",
        principal_id=str(g.api_key.id) if g.api_key else str(g.user_id),
    )
    
    # Process request. Pass the request-scoped DB session so governance can
    # persist AIAuditEvent rows and enforce the daily token budget (A3-5):
    # a bare LLMGateway() leaves AIGovernanceEngine.db None, silently no-opping
    # both. Mirrors the known-good chat.py live path.
    gateway = LLMGateway(db_session=db.session)
    response = await gateway.process(gateway_request)
    
    if not response:
        return jsonify({'error': 'No response generated from any provider'}), 503

    confidence_measurement = getattr(response, 'confidence_measurement', None)
    if not isinstance(confidence_measurement, dict):
        confidence_measurement = None
    convergence = getattr(response, 'convergence', None)
    if not isinstance(convergence, dict):
        convergence = None

    if not getattr(response, "ok", True):
        failure_class = _provider_failure_class(response)
        if get_offline_queue_enabled() and failure_class in REPLAYABLE_FAILURE_CLASSES:
            queued = enqueue_chat_request(
                data,
                reason=failure_class,
                failure_class=failure_class,
            )
            return jsonify({
                'error': _public_gateway_error(
                    response.error,
                    fallback='Gateway failed to generate a response',
                ),
                'code': 'GATEWAY_QUEUED_OFFLINE',
                'run_id': response.run_id,
                'audit_trail': _audit_trail_for_run(response.run_id),
                'provider_used': response.provider_used,
                'model_used': response.model_used,
                'contract_version': response.contract_version,
                'status': response.status,
                'failure': response.failure,
                'queued': True,
                'queue_item': queued,
            }), 202
        http_status, public_code = _gateway_failure_http_status(response)
        return jsonify({
            'error': _public_gateway_error(
                response.error,
                fallback='Gateway failed to generate a response',
            ),
            'code': public_code,
            'run_id': response.run_id,
            'audit_trail': _audit_trail_for_run(response.run_id),
            'provider_used': response.provider_used,
            'model_used': response.model_used,
            'contract_version': response.contract_version,
            'status': response.status,
            'failure': response.failure,
            'confidence_measurement': confidence_measurement,
            'convergence': convergence,
        }), http_status

    output_classification = None
    if isinstance(response.explainability, dict):
        output_classification = response.explainability.get('output_classification')
    confidence_score = getattr(response, "confidence", None)
    if not isinstance(confidence_score, (int, float)):
        confidence_score = None
    claims = getattr(response, "claims", None)
    if not isinstance(claims, list):
        claims = []
    evidence_count = getattr(response, "evidence_count", 0)
    if not isinstance(evidence_count, int):
        evidence_count = 0
    citations = getattr(response, 'citations', None)
    if not isinstance(citations, list):
        citations = []
    validators = getattr(response, 'validators', None)
    if not isinstance(validators, list):
        validators = []

    return api_response({
        'response': response.content,
        'run_id': response.run_id,
        'audit_trail': _audit_trail_for_run(response.run_id),
        'provider_used': response.provider_used,
        'model_used': response.model_used,
        'usage': response.usage,
        'trace_summary': _trace_summary_for_response(response),
        'coordinates': response.coordinate,
        'confidence_score': confidence_score,
        'confidence_measurement': confidence_measurement,
        'convergence': convergence,
        'claims': claims,
        'citations': citations,
        'validators': validators,
        'evidence_count': evidence_count,
        'output_classification': output_classification,
        'warnings': response.warnings,
        'contract_version': response.contract_version,
        'status': response.status,
        'failure': response.failure,
        'source_ids': response.meta.get('source_ids', []),
    })


@gateway_bp.route('/offline-queue', methods=['GET'])
@api_session_login_required
def get_offline_queue():
    """Return locally persisted desktop chat requests waiting for replay."""
    return api_response(list_queue())


@gateway_bp.route('/requests/<request_id>/cancel', methods=['POST'])
@api_session_login_required
def cancel_gateway_request(request_id: str):
    """Cancel an active request by its client-visible request id or trace id."""
    if not CANCELLATION_REGISTRY.cancel(request_id):
        return jsonify({
            'cancelled': False,
            'code': 'REQUEST_NOT_ACTIVE',
            'message': 'No active request matched that identifier.',
        }), 404
    return api_response({
        'cancelled': True,
        'request_id': request_id,
        'code': 'CANCELLATION_REQUESTED',
    }, status_code=202)


@gateway_bp.route('/offline-queue', methods=['POST'])
@api_session_login_required
def add_offline_queue_item():
    """Explicitly queue a chat payload from the desktop renderer."""
    if not get_offline_queue_enabled():
        return jsonify({'error': 'Offline queue is disabled'}), 409

    raw_data = request.get_json(silent=True) or {}
    payload = raw_data.get("payload") if isinstance(raw_data.get("payload"), dict) else raw_data
    if not isinstance(payload, dict) or not payload.get("messages"):
        return jsonify({'error': 'payload.messages required'}), 400

    failure_class = str(raw_data.get("failure_class") or "").strip().lower()
    compatibility = {
        "renderer_offline": "network",
        "network_unavailable": "network",
    }
    failure_class = compatibility.get(failure_class, failure_class)
    if failure_class not in REPLAYABLE_FAILURE_CLASSES:
        return jsonify({
            'error': 'failure_class must be network, provider_outage, or timeout',
            'code': 'FAILURE_NOT_REPLAYABLE',
        }), 400
    try:
        queued = enqueue_chat_request(
            payload,
            reason=failure_class,
            failure_class=failure_class,
        )
    except ValueError:
        logger.warning("Offline replay queue rejected an item at a configured limit")
        return jsonify({
            'error': 'Offline replay queue limit exceeded',
            'code': 'OFFLINE_QUEUE_LIMIT',
        }), 409
    return api_response({"queued": True, "queue_item": queued}, status_code=202)


@gateway_bp.route('/offline-queue/<item_id>', methods=['DELETE'])
@api_session_login_required
def delete_offline_queue_item(item_id: str):
    if not delete_item(item_id):
        return jsonify({'error': 'Queue item not found'}), 404
    return api_response({'deleted': True, 'id': item_id})


@gateway_bp.route('/offline-queue/replay', methods=['POST'])
@api_session_login_required
async def replay_offline_queue():
    """Replay pending desktop chat requests through the normal gateway path."""
    queue = list_queue(include_payload=True)
    pending = [item for item in queue["items"] if item.get("status") == "pending"]
    results = []
    # DB-bound so replayed requests are governance-audited (A3-5).
    gateway = LLMGateway(db_session=db.session)

    for item in pending:
        payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
        mark_item(str(item.get("id")), "pending")
        gateway_request = GovernedRequest(
            messages=payload.get("messages", []),
            request_id=str(payload.get("request_id") or uuid.uuid4()),
            provider=payload.get("provider"),
            model=payload.get("model"),
            mode=payload.get("mode", "standard"),
            constraints=payload.get("constraints", {}),
            temperature=payload.get("temperature", 0.7),
            max_tokens=payload.get("max_tokens") or 1024,
            user_id=getattr(g.auth_user, "id", None),
            session_id=payload.get("session_id"),
            api_key_id=None,
            metadata={**payload.get("meta", {}), "offline_replay": True},
            source="offline_replay",
            principal_kind="desktop",
            principal_id=str(getattr(g.auth_user, "id", "desktop")),
        )
        response = await gateway.process(gateway_request)
        if response and getattr(response, "ok", True):
            replay_response = {
                "run_id": response.run_id,
                "audit_trail": _audit_trail_for_run(response.run_id),
                "provider_used": response.provider_used,
                "model_used": response.model_used,
            }
            mark_item(str(item.get("id")), "completed", response=replay_response)
            results.append({"id": item.get("id"), "status": "completed", **replay_response})
        else:
            error = getattr(response, "error", None) if response else "No response generated"
            replay_response = {}
            if response:
                replay_response = {
                    "run_id": response.run_id,
                    "audit_trail": _audit_trail_for_run(response.run_id),
                    "provider_used": response.provider_used,
                    "model_used": response.model_used,
                }
            public_error = _public_gateway_error(error, fallback="Replay failed")
            failure_class = _provider_failure_class(response) if response else None
            next_status = "pending" if failure_class in REPLAYABLE_FAILURE_CLASSES else "failed"
            mark_item(str(item.get("id")), next_status, error=public_error, response=replay_response or None)
            results.append({"id": item.get("id"), "status": next_status, "error": public_error, **replay_response})

    return api_response({"replayed": len(results), "results": results, "queue": list_queue()})


@gateway_bp.route('/chat/stream', methods=['POST'])
@api_key_required
def gateway_chat_stream():
    """
    Streaming gateway endpoint.
    
    Returns Server-Sent Events (SSE) stream.
    """
    raw_data = request.get_json(silent=True) or {}
    if not raw_data.get('messages'):
        return jsonify({'error': 'messages required'}), 400

    validated_payload, validation_error_response = validate_pydantic_payload(
        GatewayChatRequest,
        raw_data,
    )
    if validation_error_response:
        return validation_error_response

    data = validated_payload.model_dump() if validated_payload else {}
    messages = data.get('messages', [])

    policy_error = _apply_api_key_request_policy(data)
    if policy_error:
        return policy_error
    
    gateway_request = GovernedRequest(
        messages=messages,
        provider=data.get('provider'),
        model=data.get('model'),
        mode=data.get('mode', 'standard'),
        constraints=data.get('constraints', {}),
        temperature=data.get('temperature', 0.7),
        max_tokens=data.get('max_tokens') or 1024,
        user_id=g.user_id,
        session_id=data.get('session_id'),
        api_key_id=str(g.api_key.id) if g.api_key else None,
        metadata=data.get('meta', {}),
        source="gateway_stream",
        principal_kind="external_client" if g.api_key else "desktop",
        principal_id=str(g.api_key.id) if g.api_key else str(g.user_id),
    )
    
    def generate():
        # DB-bound so streamed chats are governance-audited (A3-5).
        gateway = LLMGateway(db_session=db.session)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            async def stream():
                async for chunk in gateway.process_stream(gateway_request):
                    if isinstance(chunk, dict) and chunk.get('run_id') and chunk.get('type') in {'done', 'error'}:
                        chunk = {**chunk, 'audit_trail': _audit_trail_for_run(chunk.get('run_id'))}
                    if isinstance(chunk, dict) and chunk.get('type') == 'error':
                        chunk = {
                            **chunk,
                            'error': _public_gateway_error(
                                chunk.get('error'),
                                fallback='Gateway stream failed',
                            ),
                            'code': 'GATEWAY_STREAM_FAILED',
                        }
                    yield f"data: {json.dumps(chunk)}\n\n"
            
            # Run async generator
            gen = stream()
            while True:
                try:
                    chunk = loop.run_until_complete(gen.__anext__())
                    yield chunk
                except StopAsyncIteration:
                    break
                    
        except Exception:
            logger.error("Streaming gateway execution failed", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': 'Gateway stream failed', 'code': 'GATEWAY_STREAM_FAILED'})}\n\n"
        finally:
            loop.close()
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        }
    )


@gateway_bp.route('/providers', methods=['GET'])
@api_key_required
def list_active_providers():
    """List active providers available to the user."""
    providers = [
        provider
        for provider in LLMProvider.query.filter_by(is_active=True).order_by(LLMProvider.priority).all()
        if str(getattr(provider, 'provider_type', '')).lower() in SUPPORTED_PROVIDER_TYPES
    ]
    api_key = getattr(g, 'api_key', None)
    if api_key:
        allowed_providers = _normalize_allowlist(api_key.allowed_providers)
        if allowed_providers:
            providers = [
                p for p in providers
                if str(getattr(p, 'provider_type', '')).lower() in allowed_providers
                or str(getattr(p, 'name', '')).lower() in allowed_providers
            ]
    
    return jsonify({
        'providers': [
            {
                'id': str(p.id),
                'name': p.name,
                'type': p.provider_type,
                'model': p.model_id,
                'is_default': p.is_default,
                'has_api_key': bool(getattr(p, 'api_key_encrypted', None)),
                'status': str((p.config or {}).get('availability_status') or ('stored' if p.api_key_encrypted else 'not_configured')),
                'status_checked_at': (p.config or {}).get('availability_checked_at'),
            }
            for p in providers
        ]
    })


@gateway_bp.route('/keys', methods=['POST'])
@api_session_login_required
def save_provider_key():
    """Create or update an LLM provider API key (basic UI helper).

    The app uses one user-selected cloud model (OpenAI ``gpt-5.5`` or Google
    ``gemini-3.1-pro-preview``), so an API key is required.
    """
    data = request.get_json() or {}
    provider_type = str(data.get('provider') or '').strip().lower()
    api_key = str(data.get('key') or '').strip()
    model_id = str(data.get('model') or '').strip()
    auth_user = getattr(g, 'auth_user', None) or current_user

    if not provider_type or not api_key:
        return jsonify({'error': 'provider and key required'}), 400

    if provider_type not in SUPPORTED_PROVIDER_TYPES:
        return jsonify({
            'error': 'Unsupported provider selection',
            'supported_providers': sorted(SUPPORTED_PROVIDER_TYPES),
        }), 400

    provider = LLMProvider.query.filter_by(provider_type=provider_type).order_by(
        LLMProvider.created_at.desc()
    ).first()

    if provider is None:
        provider = LLMProvider(
            name=provider_type.title(),
            provider_type=provider_type,
            is_active=True,
            created_by=auth_user.id,
        )
        db.session.add(provider)

    try:
        provider.model_id = validate_provider_model(
            provider_type,
            model_id or provider.model_id or default_model_for_provider(provider_type),
        )
    except ValueError:
        return jsonify({
            'error': 'Unsupported provider or model selection',
            'code': 'INVALID_PROVIDER_MODEL',
        }), 400
    provider.is_active = True
    provider.is_default = True
    provider.priority = 1
    provider.set_api_key(api_key)
    provider.config = {
        **(provider.config or {}),
        'availability_status': 'stored',
        'availability_checked_at': None,
    }

    # Only one provider holds is_default=True.
    LLMProvider.query.filter(
        LLMProvider.id != provider.id,
        LLMProvider.is_default.is_(True),
    ).update({'is_default': False}, synchronize_session=False)

    db.session.commit()

    return jsonify({
        'success': True,
        'provider': provider.to_dict()
    })


@gateway_bp.route('/health', methods=['GET'])
def gateway_health():
    """Gateway health check."""
    # Check provider availability
    providers = LLMProvider.query.filter_by(is_active=True).count()
    
    return jsonify({
        'status': 'healthy' if providers > 0 else 'degraded',
        'active_providers': providers,
        'message': 'Gateway operational' if providers > 0 else 'No providers configured',
    })


@gateway_bp.route('/network-status', methods=['GET'])
@limiter.exempt
@api_session_login_required
def network_status():
    """Cached local-first provider/network status for desktop IPC."""
    force = str(request.args.get("force") or "").lower() in {"1", "true", "yes", "on"}
    return jsonify(NetworkState.check(force=force))


@gateway_bp.route('/quad-analysis-status', methods=['GET'])
@api_session_login_required
def quad_analysis_status():
    """Latest compact quad analysis status for desktop IPC."""
    return jsonify(LLMGateway.get_quad_analysis_status())


@gateway_bp.route('/dmrf-status', methods=['GET'])
@api_session_login_required
def dmrf_status():
    """Latest compact DMRF status for desktop IPC."""
    try:
        from backend.dmrf import DMRFOrchestrator

        return jsonify(DMRFOrchestrator.status())
    except Exception as exc:
        logger.warning("DMRF status unavailable: %s", exc)
        return jsonify({"status": "unavailable"}), 503


@gateway_bp.route('/dsqp-persona-profiles', methods=['GET'])
@api_session_login_required
def dsqp_persona_profiles():
    """Construct compact DSQP persona profiles for desktop IPC."""
    query = request.args.get("query") or "DataLogicEngine desktop reasoning workflow"
    risk_domain = request.args.get("risk_domain") or "standard"
    try:
        from backend.dsqp import DSQPOrchestrator

        result = DSQPOrchestrator(timeout_seconds=5).construct_all_sync(
            query,
            {"active_axes": [8, 9, 10, 11]},
            active_axes=[8, 9, 10, 11],
            context={"query": query, "risk_domain": risk_domain, "dsqp_mode": True},
        )
        compact_profiles = []
        for axis, profile in sorted(result.get("profiles", {}).items()):
            components = profile.get("components", {})
            compact_profiles.append(
                {
                    "axis": int(axis),
                    "persona_type": profile.get("persona_type"),
                    "name": profile.get("name"),
                    "coverage_score": profile.get("coverage_score", 0),
                    "job_role": components.get("job_role", {}).get("title"),
                    "skills": components.get("skills", {}).get("items", [])[:4],
                    "chain_steps": len(profile.get("dsqp_chain", [])),
                }
            )
        return jsonify(
            {
                "success": True,
                "query": query,
                "profiles": compact_profiles,
                "partial": result.get("partial", False),
                "failures": result.get("failures", {}),
            }
        )
    except Exception as exc:
        logger.warning("DSQP persona profile construction failed: %s", exc)
        return jsonify({"success": False, "profiles": [], "error": "DSQP profile construction failed"}), 503


@gateway_bp.route('/sessions/<session_id>/messages', methods=['GET'])
@api_key_required
def get_session_messages(session_id):
    """Retrieve message history for a session."""
    import uuid
    try:
        session_uuid = uuid.UUID(session_id)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid session_id'}), 400

    session = ChatSession.query.filter_by(id=session_uuid, user_id=g.user_id).first()
    if session is None:
        return jsonify({'error': 'Session not found'}), 404

    messages = ChatMessage.query.filter_by(session_id=session.id)\
        .order_by(ChatMessage.created_at.asc()).all()
    
    return jsonify({
        'messages': [
            {
                'id': str(m.id),
                'role': m.role,
                'content': m.content,
                'timestamp': m.created_at.strftime('%H:%M') if m.created_at else '',
                'is_enhanced': m.is_enhanced,
                'run_id': str(m.run_id) if m.run_id else None
            } 
            for m in messages
        ]
    })


@gateway_bp.route('/sessions', methods=['GET'])
@api_key_required
def list_user_sessions():
    """List chat sessions for the current user."""
    sessions = ChatSession.query.filter_by(user_id=g.user_id)\
        .order_by(ChatSession.updated_at.desc()).all()
    
    return jsonify({
        'sessions': [s.to_dict() for s in sessions]
    })


# ============== Admin Endpoints ==============

def admin_required(f):
    """Require admin access."""
    @wraps(f)
    @api_session_login_required
    def decorated(*args, **kwargs):
        if not current_user_is_owner():
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/providers', methods=['GET'])
@api_session_login_required
def list_providers():
    """List all providers (admin view)."""
    providers = LLMProvider.query.order_by(LLMProvider.priority).all()
    return jsonify({
        'providers': [p.to_dict(include_key=False) for p in providers]
    })


@admin_bp.route('/providers', methods=['POST'])
@admin_required
def create_provider():
    """Create a new provider."""
    data = request.get_json() or {}
    actor = get_authenticated_principal()
    
    required = ['name', 'provider_type']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} required'}), 400
    
    try:
        provider_type = normalize_provider_type(data['provider_type'])
        model_id = validate_provider_model(provider_type, data.get('model_id'))
    except ValueError:
        return jsonify({
            'error': 'Unsupported provider or model selection',
            'code': 'INVALID_PROVIDER_MODEL',
        }), 400

    provider = LLMProvider(
        name=data['name'],
        provider_type=provider_type,
        endpoint=data.get('endpoint'),
        model_id=model_id,
        deployment_name=data.get('deployment_name'),
        api_version=data.get('api_version'),
        is_active=data.get('is_active', True),
        is_default=data.get('is_default', False),
        priority=data.get('priority', 100),
        rate_limit_rpm=data.get('rate_limit_rpm'),
        rate_limit_tpm=data.get('rate_limit_tpm'),
        timeout_seconds=data.get('timeout_seconds', 30),
        max_retries=min(2, max(1, int(data.get('max_retries', 2)))),
        config={
            **(data.get('config') if isinstance(data.get('config'), dict) else {}),
            'availability_status': 'stored' if data.get('api_key') else 'not_configured',
        },
        created_by=actor.id,
    )
    
    # Set API key if provided
    if data.get('api_key'):
        provider.set_api_key(data['api_key'])
    
    # If setting as default, unset other defaults
    if provider.is_default:
        LLMProvider.query.filter_by(is_default=True).update({'is_default': False})
    
    db.session.add(provider)
    db.session.commit()
    
    return jsonify(provider.to_dict()), 201


@admin_bp.route('/providers/<provider_id>', methods=['GET'])
@api_session_login_required
def get_provider(provider_id):
    """Get provider details."""
    parsed = _parse_uuid_or_404(provider_id, 'provider_id')
    if isinstance(parsed, tuple):
        return parsed
    provider = LLMProvider.query.get_or_404(parsed)
    return jsonify(provider.to_dict(include_key=False))


@admin_bp.route('/providers/<provider_id>', methods=['PATCH'])
@admin_required
def update_provider(provider_id):
    """Update a provider."""
    parsed = _parse_uuid_or_404(provider_id, 'provider_id')
    if isinstance(parsed, tuple):
        return parsed
    provider = LLMProvider.query.get_or_404(parsed)
    data = request.get_json() or {}
    
    # Update fields
    if 'name' in data:
        provider.name = data['name']
    if 'endpoint' in data:
        provider.endpoint = data['endpoint']
    if 'model_id' in data:
        try:
            provider.model_id = validate_provider_model(provider.provider_type, data['model_id'])
        except ValueError:
            return jsonify({
                'error': 'Unsupported provider or model selection',
                'code': 'INVALID_PROVIDER_MODEL',
            }), 400
    if 'deployment_name' in data:
        provider.deployment_name = data['deployment_name']
    if 'api_version' in data:
        provider.api_version = data['api_version']
    if 'is_active' in data:
        provider.is_active = data['is_active']
    if 'priority' in data:
        provider.priority = data['priority']
    if 'rate_limit_rpm' in data:
        provider.rate_limit_rpm = data['rate_limit_rpm']
    if 'rate_limit_tpm' in data:
        provider.rate_limit_tpm = data['rate_limit_tpm']
    if 'timeout_seconds' in data:
        provider.timeout_seconds = data['timeout_seconds']
    if 'max_retries' in data:
        provider.max_retries = min(2, max(1, int(data['max_retries'])))
    if 'config' in data:
        provider.config = data['config']
    
    # Update API key if provided
    if 'api_key' in data and data['api_key']:
        provider.set_api_key(data['api_key'])
        provider.config = {
            **(provider.config or {}),
            'availability_status': 'stored',
            'availability_checked_at': None,
        }
    
    # Handle default setting
    if data.get('is_default'):
        LLMProvider.query.filter(LLMProvider.id != provider.id).update({'is_default': False})
        provider.is_default = True
    
    db.session.commit()
    return jsonify(provider.to_dict())


@admin_bp.route('/providers/<provider_id>', methods=['DELETE'])
@admin_required
def delete_provider(provider_id):
    """Delete a provider."""
    parsed = _parse_uuid_or_404(provider_id, 'provider_id')
    if isinstance(parsed, tuple):
        return parsed
    provider = LLMProvider.query.get_or_404(parsed)
    db.session.delete(provider)
    db.session.commit()
    return jsonify({'message': 'Provider deleted'}), 200


@gateway_bp.route('/providers/<provider_id>/test', methods=['POST'])
@api_session_login_required
def test_provider(provider_id):
    """Run a bounded live provider/model availability classification."""
    parsed = _parse_uuid_or_404(provider_id, 'provider_id')
    if isinstance(parsed, tuple):
        return parsed
    provider = LLMProvider.query.get_or_404(parsed)
    
    adapter = None
    provider.config = {
        **(provider.config or {}),
        'availability_status': 'validating',
        'availability_checked_at': datetime.now(UTC).isoformat(),
    }
    db.session.commit()
    try:
        gateway = LLMGateway()
        adapter = gateway._create_sdk_provider(provider)
        if adapter is None:
            raise ConnectionError("Failed to create provider adapter")
        start_time = datetime.now(UTC)
        response = asyncio.run(asyncio.wait_for(
            adapter.complete(
                messages=[{"role": "user", "content": "Hello, are you online?"}],
                model=validate_provider_model(provider.provider_type, provider.model_id),
                max_tokens=16
            ),
            timeout=min(30, max(1, int(provider.timeout_seconds or 30))),
        ))
        duration = (datetime.now(UTC) - start_time).total_seconds() * 1000
        provider.config = {
            **(provider.config or {}),
            'availability_status': 'available',
            'availability_checked_at': datetime.now(UTC).isoformat(),
            'availability_failure_class': None,
        }
        db.session.commit()
        return jsonify({
            'success': True,
            'status': 'available',
            'model': response.model or provider.model_id,
            'latency_ms': round(duration, 2),
            'message': 'Provider and model are available'
        })

    except Exception as exc:
        logger.error("Provider test failed for %s (%s)", provider_id, type(exc).__name__)
        classified = classify_provider_failure(exc)
        limited = classified.failure_class in {
            ProviderFailureClass.RATE_LIMITED,
            ProviderFailureClass.QUOTA_EXHAUSTED,
            ProviderFailureClass.BILLING_SUSPENDED,
        }
        invalid = classified.failure_class in {
            ProviderFailureClass.INVALID_KEY,
            ProviderFailureClass.INVALID_MODEL,
            ProviderFailureClass.UNAUTHORIZED_MODEL,
        }
        provider.config = {
            **(provider.config or {}),
            'availability_status': 'limited' if limited else ('invalid' if invalid else 'unavailable'),
            'availability_checked_at': datetime.now(UTC).isoformat(),
            'availability_failure_class': classified.failure_class.value,
        }
        db.session.commit()
        if classified.failure_class is ProviderFailureClass.INVALID_KEY:
            return jsonify({
                'success': False,
                'status': 'invalid',
                'error': 'Invalid API key',
                'detail': 'The saved API key was rejected by the provider. Update the key and try again.',
                'code': 'INVALID_API_KEY',
            }), 401
        if limited:
            return jsonify({
                'success': False,
                'status': 'limited',
                'error': 'Rate limited or quota exceeded',
                'detail': 'The provider rejected the request due to rate limits or quota. Check your plan/billing.',
                'code': 'RATE_LIMITED',
            }), 429
        if classified.failure_class in {ProviderFailureClass.INVALID_MODEL, ProviderFailureClass.UNAUTHORIZED_MODEL}:
            return jsonify({
                'success': False,
                'status': 'invalid',
                'error': 'Model unavailable',
                'detail': 'The configured model is not available for this key/provider.',
                'code': 'INVALID_MODEL',
            }), 422
        if classified.failure_class in {
            ProviderFailureClass.TIMEOUT,
            ProviderFailureClass.NETWORK,
            ProviderFailureClass.PROVIDER_OUTAGE,
        }:
            return jsonify({
                'success': False,
                'status': 'unavailable',
                'error': 'Provider request timed out' if classified.failure_class is ProviderFailureClass.TIMEOUT else 'Network error reaching provider',
                'detail': 'The provider did not respond before the deadline.' if classified.failure_class is ProviderFailureClass.TIMEOUT else 'Could not reach the provider endpoint. Check your internet connection.',
                'code': 'TIMEOUT' if classified.failure_class is ProviderFailureClass.TIMEOUT else 'NETWORK_ERROR',
            }), 504 if classified.failure_class is ProviderFailureClass.TIMEOUT else 503
        return jsonify({
            'success': False,
            'status': 'unavailable',
            'error': 'Provider connectivity check failed',
            'detail': 'The provider test failed for an unexpected reason. See logs for details.',
            'code': 'PROVIDER_TEST_FAILED',
        }), 502
    finally:
        if adapter is not None:
            try:
                close_result = adapter.close()
                if asyncio.iscoroutine(close_result):
                    asyncio.run(close_result)
            except Exception:
                logger.debug("Provider test client close failed", exc_info=True)


# ============== AI Governance Registry ==============

@admin_bp.route('/prompt-templates', methods=['GET'])
@api_session_login_required
def list_prompt_templates():
    """List registered prompt templates."""
    query = PromptTemplate.query.order_by(PromptTemplate.template_key.asc(), PromptTemplate.created_at.desc())
    if not current_user_is_owner():
        query = query.filter(PromptTemplate.is_active)
    templates = query.all()
    return jsonify({'prompt_templates': [template.to_dict() for template in templates]})


@admin_bp.route('/prompt-templates', methods=['POST'])
@admin_required
def create_prompt_template():
    """Create a versioned prompt template."""
    data = request.get_json() or {}
    actor = get_authenticated_principal()
    template_key = str(data.get('template_key') or '').strip()
    version = str(data.get('version') or '1.0.0').strip()
    template_body = str(data.get('template_body') or '').strip()

    if not template_key or not template_body:
        return jsonify({'error': 'template_key and template_body required'}), 400

    existing = PromptTemplate.query.filter_by(template_key=template_key, version=version).first()
    if existing:
        return jsonify({'error': 'Prompt template version already exists'}), 409

    template = PromptTemplate(
        template_key=template_key,
        version=version,
        template_body=template_body,
        description=data.get('description'),
        template_metadata=data.get('metadata') if isinstance(data.get('metadata'), dict) else {},
        is_active=bool(data.get('is_active', True)),
        created_by=actor.id,
    )
    db.session.add(template)
    db.session.commit()
    return jsonify(template.to_dict()), 201


@admin_bp.route('/prompt-templates/<string:template_id>', methods=['PATCH'])
@admin_required
def update_prompt_template(template_id: str):
    """Update fields on an existing prompt template."""
    template = PromptTemplate.query.get(template_id)
    if not template:
        return jsonify({'error': 'Not found'}), 404

    data = request.get_json() or {}
    editable = ('template_body', 'description', 'is_active')
    for field in editable:
        if field in data:
            setattr(template, field, data[field])

    # Allow submitting for review via PATCH.
    if data.get('submit_for_review') and template.approval_state == 'draft':
        template.approval_state = 'pending_review'
        template.submitted_for_review_at = datetime.now(UTC)

    db.session.commit()
    return jsonify(template.to_dict())


@admin_bp.route('/prompt-templates/<string:template_id>/approve', methods=['POST'])
@admin_required
def approve_prompt_template(template_id: str):
    """Approve a prompt template so it can be used by the governance engine."""
    actor = get_authenticated_principal()
    template = PromptTemplate.query.get(template_id)
    if not template:
        return jsonify({'error': 'Not found'}), 404

    template.approval_state = 'approved'
    template.approved_by = actor.id
    template.approved_at = datetime.now(UTC)
    template.rejected_reason = None
    db.session.commit()
    return jsonify(template.to_dict())


@admin_bp.route('/prompt-templates/<string:template_id>/reject', methods=['POST'])
@admin_required
def reject_prompt_template(template_id: str):
    """Reject a prompt template with an optional reason."""
    template = PromptTemplate.query.get(template_id)
    if not template:
        return jsonify({'error': 'Not found'}), 404

    data = request.get_json() or {}
    template.approval_state = 'rejected'
    template.rejected_reason = str(data.get('reason', '')).strip() or None
    template.is_active = False
    db.session.commit()
    return jsonify(template.to_dict())


@admin_bp.route('/prompt-templates/<string:template_id>', methods=['DELETE'])
@admin_required
def delete_prompt_template(template_id: str):
    """Permanently delete a prompt template."""
    template = PromptTemplate.query.get(template_id)
    if not template:
        return jsonify({'error': 'Not found'}), 404

    db.session.delete(template)
    db.session.commit()
    return jsonify({'success': True, 'deleted_id': template_id})


@admin_bp.route('/routing-policies', methods=['GET'])
@api_session_login_required
def list_routing_policies():
    """List registered model routing policies."""
    query = ModelRoutingPolicy.query.order_by(
        ModelRoutingPolicy.policy_name.asc(),
        ModelRoutingPolicy.created_at.desc(),
    )
    if not current_user_is_owner():
        query = query.filter(ModelRoutingPolicy.is_active)
    policies = query.all()
    return jsonify({'routing_policies': [policy.to_dict() for policy in policies]})


@admin_bp.route('/routing-policies', methods=['POST'])
@admin_required
def create_routing_policy():
    """Create a versioned model routing policy."""
    data = request.get_json() or {}
    actor = get_authenticated_principal()
    policy_name = str(data.get('policy_name') or '').strip()
    version = str(data.get('version') or '1.0.0').strip()
    rules = data.get('rules')

    if not policy_name or not isinstance(rules, dict):
        return jsonify({'error': 'policy_name and rules object required'}), 400

    existing = ModelRoutingPolicy.query.filter_by(policy_name=policy_name, version=version).first()
    if existing:
        return jsonify({'error': 'Routing policy version already exists'}), 409

    policy = ModelRoutingPolicy(
        policy_name=policy_name,
        version=version,
        rules=rules,
        is_active=bool(data.get('is_active', True)),
        created_by=actor.id,
    )
    db.session.add(policy)
    db.session.commit()
    return jsonify(policy.to_dict()), 201


@admin_bp.route('/ai-audit', methods=['GET'])
@api_session_login_required
def list_ai_audit_events():
    """List AI audit trail events with model/version/policy metadata."""
    actor = get_authenticated_principal()
    limit = request.args.get('limit', 100, type=int)
    limit = max(1, min(limit, 500))
    query = AIAuditEvent.query.order_by(AIAuditEvent.created_at.desc())
    if not current_user_is_owner():
        query = query.filter_by(user_id=actor.id)
    events = query.limit(limit).all()
    return jsonify({'events': [event.to_dict() for event in events]})


# ============== API Key Management ==============

@admin_bp.route('/api-keys', methods=['GET'])
@api_session_login_required
def list_api_keys():
    """List API keys (admin sees all, users see their own)."""
    actor = get_authenticated_principal()
    if current_user_is_owner():
        keys = ExternalAPIKey.query.order_by(ExternalAPIKey.created_at.desc()).all()
    else:
        keys = ExternalAPIKey.query.filter_by(user_id=actor.id).order_by(
            ExternalAPIKey.created_at.desc()
        ).all()
    
    return jsonify({
        'api_keys': [k.to_dict() for k in keys]
    })


@admin_bp.route('/api-keys', methods=['POST'])
@api_session_login_required
def create_api_key():
    """Create a new API key."""
    data = request.get_json() or {}
    actor = get_authenticated_principal()
    
    if not data.get('name'):
        return jsonify({'error': 'name required'}), 400
    
    # Generate key
    full_key, prefix, key_hash = ExternalAPIKey.generate_key()
    
    api_key = ExternalAPIKey(
        name=data['name'],
        key_prefix=prefix,
        key_hash=key_hash,
        user_id=actor.id,
        permissions=data.get('permissions', {'read': True, 'write': True, 'admin': False}),
        allowed_providers=data.get('allowed_providers'),
        allowed_models=data.get('allowed_models'),
        rate_limit_rpm=data.get('rate_limit_rpm', 60),
        rate_limit_daily=data.get('rate_limit_daily'),
        max_tokens_per_request=data.get('max_tokens_per_request'),
    )
    
    # Handle expiration
    if data.get('expires_in_days'):
        from datetime import timedelta
        api_key.expires_at = datetime.now(UTC) + timedelta(days=data['expires_in_days'])
    
    db.session.add(api_key)
    db.session.commit()
    
    # Return the full key ONLY on creation
    result = api_key.to_dict()
    result['api_key'] = full_key  # Only time the full key is returned
    result['warning'] = 'Save this API key - it will not be shown again'
    
    return jsonify(result), 201


@admin_bp.route('/api-keys/<key_id>', methods=['DELETE'])
@api_session_login_required
def revoke_api_key(key_id):
    """Revoke an API key."""
    actor = get_authenticated_principal()
    parsed = _parse_uuid_or_404(key_id, 'key_id')
    if isinstance(parsed, tuple):
        return parsed
    api_key = ExternalAPIKey.query.get_or_404(parsed)
    
    # Only owner or admin can revoke
    if api_key.user_id != actor.id:
        if not current_user_is_owner():
            return jsonify({'error': 'Access denied'}), 403
    
    api_key.is_active = False
    db.session.commit()
    
    return jsonify({'message': 'API key revoked'})


# ============== Usage Analytics ==============

def _usage_ledger_entry(record: LLMProviderUsage) -> dict:
    """Serialize only the secret-free/content-free local ledger contract."""
    return {
        'id': str(record.id),
        'run_id': str(record.run_id) if record.run_id else None,
        'session_id': record.session_id,
        'provider': record.provider_type,
        'model': record.model,
        'purpose': record.purpose,
        'request_stage': record.request_stage,
        'attempt_number': record.attempt_number,
        'retry_index': record.retry_index,
        'tokens_in': int(record.tokens_in or 0),
        'tokens_out': int(record.tokens_out or 0),
        'latency_ms': record.latency_ms,
        'estimated_cost_usd': record.estimated_cost_usd,
        'pricing_status': record.pricing_status,
        'status': record.status,
        'error_class': record.error_class,
        'disclosed_categories': list(record.disclosed_categories or []),
        'started_at': record.started_at.isoformat() if record.started_at else None,
        'ended_at': record.ended_at.isoformat() if record.ended_at else None,
        'created_at': record.created_at.isoformat() if record.created_at else None,
    }


def _usage_ledger_summary(days: int = 30, session_id: str | None = None) -> dict:
    """Build an owner-visible snapshot from the durable provider usage ledger."""
    from sqlalchemy import func

    bounded_days = max(1, min(int(days or 30), 366))
    now = datetime.now(UTC)
    since = now - timedelta(days=bounded_days)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = day_start.replace(day=1)

    def filtered_query(start: datetime):
        query = LLMProviderUsage.query.filter(LLMProviderUsage.created_at >= start)
        if session_id:
            query = query.filter(LLMProviderUsage.session_id == str(session_id))
        return query

    def totals(start: datetime) -> dict:
        query = filtered_query(start)
        total_calls = query.count()
        successful = query.filter(LLMProviderUsage.success.is_(True)).count()
        tokens_in = query.with_entities(func.coalesce(func.sum(LLMProviderUsage.tokens_in), 0)).scalar() or 0
        tokens_out = query.with_entities(func.coalesce(func.sum(LLMProviderUsage.tokens_out), 0)).scalar() or 0
        known_cost_calls = query.filter(LLMProviderUsage.estimated_cost_usd.is_not(None)).count()
        unknown_cost_calls = query.filter(LLMProviderUsage.estimated_cost_usd.is_(None)).count()
        known_cost = query.with_entities(
            func.coalesce(func.sum(LLMProviderUsage.estimated_cost_usd), 0.0)
        ).scalar() or 0.0
        return {
            'calls': int(total_calls),
            'successful_calls': int(successful),
            'tokens_in': int(tokens_in),
            'tokens_out': int(tokens_out),
            'tokens_total': int(tokens_in) + int(tokens_out),
            'known_estimated_cost_usd': float(known_cost) if known_cost_calls else None,
            'known_price_calls': int(known_cost_calls),
            'unknown_price_calls': int(unknown_cost_calls),
        }

    period = totals(since)
    daily = totals(day_start)
    monthly = totals(month_start)
    limits = ProviderBudgetPolicy.configured_limits()
    remaining = {
        'daily_calls': max(0, int(limits['daily_calls'] or 0) - daily['calls']),
        'monthly_calls': max(0, int(limits['monthly_calls'] or 0) - monthly['calls']),
        'daily_tokens': max(0, int(limits['daily_tokens'] or 0) - daily['tokens_total']),
        'monthly_tokens': max(0, int(limits['monthly_tokens'] or 0) - monthly['tokens_total']),
        'monthly_spend_usd': (
            None
            if limits['monthly_spend_usd'] is None or monthly['known_estimated_cost_usd'] is None
            else max(0.0, float(limits['monthly_spend_usd']) - float(monthly['known_estimated_cost_usd']))
        ),
    }
    recent = filtered_query(since).order_by(LLMProviderUsage.created_at.desc()).limit(100).all()
    by_provider_query = db.session.query(
        LLMProviderUsage.provider_type,
        func.count(LLMProviderUsage.id),
        func.coalesce(func.sum(LLMProviderUsage.tokens_in), 0),
        func.coalesce(func.sum(LLMProviderUsage.tokens_out), 0),
        func.sum(LLMProviderUsage.estimated_cost_usd),
    ).filter(LLMProviderUsage.created_at >= since)
    if session_id:
        by_provider_query = by_provider_query.filter(
            LLMProviderUsage.session_id == str(session_id)
        )
    by_provider_rows = by_provider_query.group_by(LLMProviderUsage.provider_type).all()

    return {
        'schema_version': 'provider-usage-ledger.v1',
        'generated_at': now.isoformat(),
        'period_days': bounded_days,
        'session_id': session_id,
        'limits': limits,
        'remaining': remaining,
        'period': period,
        'daily': daily,
        'monthly': monthly,
        'pricing_status': (
            'unknown'
            if monthly['unknown_price_calls'] or not monthly['known_price_calls']
            else 'available'
        ),
        'by_provider': [
            {
                'provider': row[0],
                'calls': int(row[1] or 0),
                'tokens_in': int(row[2] or 0),
                'tokens_out': int(row[3] or 0),
                'known_estimated_cost_usd': float(row[4]) if row[4] is not None else None,
            }
            for row in by_provider_rows
        ],
        'entries': [_usage_ledger_entry(record) for record in recent],
    }


@gateway_bp.route('/usage-ledger', methods=['GET'])
@api_session_login_required
def get_usage_ledger():
    """Review current budgets and the content-free provider egress ledger."""
    return jsonify(_usage_ledger_summary(
        request.args.get('days', 30, type=int),
        request.args.get('session_id'),
    ))


@gateway_bp.route('/usage-ledger/export', methods=['GET'])
@api_session_login_required
def export_usage_ledger():
    """Export a redacted JSON ledger for local owner review."""
    payload = _usage_ledger_summary(request.args.get('days', 366, type=int))
    payload['export_notice'] = (
        'This export excludes provider credentials, prompt/response content, and prohibited data.'
    )
    return jsonify(payload)


@gateway_bp.route('/usage-ledger', methods=['DELETE'])
@admin_required
def reset_usage_ledger():
    """Reset the local ledger after an explicit owner confirmation phrase."""
    data = request.get_json(silent=True) or {}
    if data.get('confirmation') != 'RESET_PROVIDER_USAGE_LEDGER':
        return jsonify({
            'error': 'Exact confirmation phrase required',
            'required_confirmation': 'RESET_PROVIDER_USAGE_LEDGER',
        }), 400
    deleted = LLMProviderUsage.query.delete(synchronize_session=False)
    db.session.commit()
    return jsonify({'success': True, 'deleted_records': int(deleted or 0)})

@admin_bp.route('/usage', methods=['GET'])
@api_session_login_required
def get_usage():
    """Compatibility view backed by the Phase 7 ledger contract."""
    return jsonify(_usage_ledger_summary(request.args.get('days', 7, type=int)))


def register_gateway_routes(app):
    """Register gateway blueprints with the app."""
    app.register_blueprint(gateway_bp)
    app.register_blueprint(admin_bp)
