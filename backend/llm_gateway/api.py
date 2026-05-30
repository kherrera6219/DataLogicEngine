# ruff: noqa: E402
"""
LLM Gateway API Endpoints

Provides the public API for external clients to access UKG-enhanced LLM.
Also includes admin endpoints for provider and API key management.
"""

import asyncio
from datetime import datetime, UTC
from functools import wraps
from flask import Blueprint, request, jsonify, Response, stream_with_context, g
from flask_login import login_required, current_user
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
from backend.llm_gateway.gateway import LLMGateway, GatewayRequest, NetworkState
from backend.llm_gateway.model_defaults import default_model_for_provider
from backend.llm_gateway.schemas import GatewayChatRequest
from backend.auth.api_decorators import api_session_login_required
from backend.desktop.offline_queue import enqueue_chat_request, list_queue, mark_item
from backend.storage.runtime_settings import get_local_slm_audit_mode, get_offline_queue_enabled
from backend.utils.request_validation import validate_pydantic_payload
from backend.utils.error_normalization import normalize_public_error_message
try:
    from extensions import db, cache
except ImportError:
    # Final fallback for unusual packaging contexts
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from extensions import db, cache

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


def _audit_trail_for_run(run_id: Optional[str]) -> Optional[dict]:
    """Build the frontend trace contract for a gateway run."""
    if not run_id:
        return None
    return {
        "decision_path": f"/api/v1/trace/runs/{run_id}",
        "complete_trace_url": f"/api/v1/trace/runs/{run_id}/bundle",
        "download_url": f"/api/v1/trace/runs/{run_id}/export",
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
        
    # Build GatewayRequest
    gateway_request = GatewayRequest(
        messages=messages,
        provider=data.get('provider'),
        model=data.get('model'),
        mode=data.get('mode', 'chat'),
        constraints=data.get('constraints', {}),
        run_ukg_pipeline=data.get('run_ukg_pipeline', True),
        temperature=data.get('temperature', 0.7),
        max_tokens=data.get('max_tokens'),
        user_id=g.user_id,
        session_id=data.get('session_id'),
        api_key_id=str(g.api_key.id) if g.api_key else None,
        meta=data.get('meta', {}),
    )
    
    # Process request
    gateway = LLMGateway()
    response = await gateway.process(gateway_request)
    
    if not response:
        if get_offline_queue_enabled():
            queued = enqueue_chat_request(data, reason="gateway_no_response")
            return jsonify({
                'error': 'No response generated from any provider',
                'code': 'GATEWAY_QUEUED_OFFLINE',
                'queued': True,
                'queue_item': queued,
            }), 202
        return jsonify({'error': 'No response generated from any provider'}), 503
    if not getattr(response, "ok", True):
        if get_offline_queue_enabled():
            queued = enqueue_chat_request(data, reason=_public_gateway_error(response.error, fallback='gateway_failed'))
            return jsonify({
                'error': _public_gateway_error(
                    response.error,
                    fallback='Gateway failed to generate a response',
                ),
                'code': 'GATEWAY_QUEUED_OFFLINE',
                'run_id': response.run_id,
                'provider_used': response.provider_used,
                'model_used': response.model_used,
                'queued': True,
                'queue_item': queued,
            }), 202
        return jsonify({
            'error': _public_gateway_error(
                response.error,
                fallback='Gateway failed to generate a response',
            ),
            'code': 'GATEWAY_REQUEST_FAILED',
            'run_id': response.run_id,
            'provider_used': response.provider_used,
            'model_used': response.model_used,
        }), 503

    output_classification = None
    if isinstance(response.explainability, dict):
        output_classification = response.explainability.get('output_classification')

    provider_used = response.provider_used or ""
    local_slm_audit = None
    if get_local_slm_audit_mode() and provider_used.lower() in {"local_slm", "ollama", "vllm"}:
        local_slm_audit = {
            "mode": "LOCAL_MODEL",
            "provider": provider_used,
            "model": response.model_used,
            "offline_cap_applied": bool(response.meta.get("offline_guard")) if hasattr(response, "meta") else False,
            "recorded_at": datetime.now(UTC).isoformat(),
        }

    return api_response({
        'response': response.content,
        'run_id': response.run_id,
        'audit_trail': _audit_trail_for_run(response.run_id),
        'provider_used': response.provider_used,
        'model_used': response.model_used,
        'usage': response.usage,
        'trace_summary': None, # Adjust if response object has this
        'coordinates': response.coordinate,
        'confidence_score': 0.85, # Default or from response logic
        'claims': [], 
        'evidence_count': 0,
        'output_classification': output_classification,
        'local_slm_audit': local_slm_audit,
        'warnings': response.warnings,
    })


@gateway_bp.route('/offline-queue', methods=['GET'])
@api_session_login_required
def get_offline_queue():
    """Return locally persisted desktop chat requests waiting for replay."""
    return api_response(list_queue())


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

    queued = enqueue_chat_request(payload, reason=str(raw_data.get("reason") or "renderer_offline"))
    return api_response({"queued": True, "queue_item": queued}, status_code=202)


@gateway_bp.route('/offline-queue/replay', methods=['POST'])
@api_session_login_required
async def replay_offline_queue():
    """Replay pending desktop chat requests through the normal gateway path."""
    queue = list_queue()
    pending = [item for item in queue["items"] if item.get("status") == "pending"]
    results = []
    gateway = LLMGateway()

    for item in pending:
        payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
        mark_item(str(item.get("id")), "pending")
        gateway_request = GatewayRequest(
            messages=payload.get("messages", []),
            provider=payload.get("provider"),
            model=payload.get("model"),
            mode=payload.get("mode", "chat"),
            constraints=payload.get("constraints", {}),
            run_ukg_pipeline=payload.get("run_ukg_pipeline", True),
            temperature=payload.get("temperature", 0.7),
            max_tokens=payload.get("max_tokens"),
            user_id=getattr(g.auth_user, "id", None),
            session_id=payload.get("session_id"),
            api_key_id=None,
            meta={**payload.get("meta", {}), "offline_replay": True},
        )
        response = await gateway.process(gateway_request)
        if response and getattr(response, "ok", True):
            replay_response = {
                "run_id": response.run_id,
                "provider_used": response.provider_used,
                "model_used": response.model_used,
            }
            mark_item(str(item.get("id")), "completed", response=replay_response)
            results.append({"id": item.get("id"), "status": "completed", **replay_response})
        else:
            error = getattr(response, "error", None) if response else "No response generated"
            mark_item(str(item.get("id")), "failed", error=_public_gateway_error(error, fallback="Replay failed"))
            results.append({"id": item.get("id"), "status": "failed", "error": _public_gateway_error(error, fallback="Replay failed")})

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
    
    gateway_request = GatewayRequest(
        messages=messages,
        provider=data.get('provider'),
        model=data.get('model'),
        mode=data.get('mode', 'chat'),
        constraints=data.get('constraints', {}),
        run_ukg_pipeline=data.get('run_ukg_pipeline', True),
        temperature=data.get('temperature', 0.7),
        max_tokens=data.get('max_tokens'),
        user_id=g.user_id,
        session_id=data.get('session_id'),
        api_key_id=str(g.api_key.id) if g.api_key else None,
        meta=data.get('meta', {}),
    )
    
    def generate():
        gateway = LLMGateway()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            async def stream():
                async for chunk in gateway.process_stream(gateway_request):
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
    providers = LLMProvider.query.filter_by(is_active=True).order_by(LLMProvider.priority).all()
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
            }
            for p in providers
        ]
    })


@gateway_bp.route('/keys', methods=['POST'])
@api_session_login_required
def save_provider_key():
    """Create or update an LLM provider API key (basic UI helper)."""
    data = request.get_json() or {}
    provider_type = data.get('provider')
    api_key = data.get('key')
    model_id = data.get('model')
    auth_user = getattr(g, 'auth_user', None) or current_user
    
    if not provider_type or not api_key:
        return jsonify({'error': 'provider and key required'}), 400
    
    provider = LLMProvider.query.filter_by(provider_type=provider_type).order_by(
        LLMProvider.created_at.desc()
    ).first()
    
    if provider is None:
        provider = LLMProvider(
            name=str(provider_type).title(),
            provider_type=provider_type,
            is_active=True,
            created_by=auth_user.id,
        )
        db.session.add(provider)

    provider.model_id = str(model_id or provider.model_id or default_model_for_provider(provider_type))

    provider.is_active = True
    provider.is_default = True
    provider.priority = 1
    LLMProvider.query.filter(
        LLMProvider.id != provider.id,
        LLMProvider.is_default.is_(True),
    ).update({'is_default': False}, synchronize_session=False)

    provider.set_api_key(api_key)
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
def network_status():
    """Cached local-first provider/network status for desktop IPC."""
    force = str(request.args.get("force") or "").lower() in {"1", "true", "yes", "on"}
    return jsonify(NetworkState.check(force=force))


@gateway_bp.route('/quad-analysis-status', methods=['GET'])
def quad_analysis_status():
    """Latest compact quad analysis status for desktop IPC."""
    return jsonify(LLMGateway.get_quad_analysis_status())


@gateway_bp.route('/dmrf-status', methods=['GET'])
def dmrf_status():
    """Latest compact DMRF status for desktop IPC."""
    try:
        from backend.dmrf import DMRFOrchestrator

        return jsonify(DMRFOrchestrator.status())
    except Exception as exc:
        logger.warning("DMRF status unavailable: %s", exc)
        return jsonify({"status": "unavailable"}), 503


@gateway_bp.route('/dsqp-persona-profiles', methods=['GET'])
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
    @login_required
    def decorated(*args, **kwargs):
        if not (hasattr(current_user, 'is_admin') and current_user.is_admin):
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/providers', methods=['GET'])
@login_required
def list_providers():
    """List all providers (admin view)."""
    providers = LLMProvider.query.order_by(LLMProvider.priority).all()
    return jsonify({
        'providers': [p.to_dict(include_key=True) for p in providers]
    })


@admin_bp.route('/providers', methods=['POST'])
@admin_required
def create_provider():
    """Create a new provider."""
    data = request.get_json() or {}
    
    required = ['name', 'provider_type']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} required'}), 400
    
    provider = LLMProvider(
        name=data['name'],
        provider_type=data['provider_type'],
        endpoint=data.get('endpoint'),
        model_id=data.get('model_id'),
        deployment_name=data.get('deployment_name'),
        api_version=data.get('api_version'),
        is_active=data.get('is_active', True),
        is_default=data.get('is_default', False),
        priority=data.get('priority', 100),
        rate_limit_rpm=data.get('rate_limit_rpm'),
        rate_limit_tpm=data.get('rate_limit_tpm'),
        timeout_seconds=data.get('timeout_seconds', 30),
        max_retries=data.get('max_retries', 3),
        config=data.get('config'),
        created_by=current_user.id,
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
@login_required
def get_provider(provider_id):
    """Get provider details."""
    parsed = _parse_uuid_or_404(provider_id, 'provider_id')
    if isinstance(parsed, tuple):
        return parsed
    provider = LLMProvider.query.get_or_404(parsed)
    return jsonify(provider.to_dict(include_key=True))


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
        provider.model_id = data['model_id']
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
        provider.max_retries = data['max_retries']
    if 'config' in data:
        provider.config = data['config']
    
    # Update API key if provided
    if 'api_key' in data and data['api_key']:
        provider.set_api_key(data['api_key'])
    
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
    """Test provider connection using the Gateway SDK adapter."""
    parsed = _parse_uuid_or_404(provider_id, 'provider_id')
    if isinstance(parsed, tuple):
        return parsed
    provider = LLMProvider.query.get_or_404(parsed)
    
    try:
        # Use the Gateway's internal factory to create the provider instance
        # This ensures we test exactly what the Gateway uses
        gateway = LLMGateway()
        
        # We need to manually construct the EnvProvider-like object or use the DB provider directly
        # The gateway._create_sdk_provider expects an object with specific attributes
        
        # Use the internal helper to instantiate the adapter
        adapter = gateway._create_sdk_provider(provider)
        
        if not adapter:
             return jsonify({
                'success': False,
                'status': 'error',
                'error': 'Failed to create provider adapter (configuration invalid?)',
            }), 503

        # Run a simple completion check
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Simple "Hello" test
        try:
            start_time = datetime.now()
            # Most providers support a simple prompt
            response = loop.run_until_complete(adapter.complete(
                messages=[{"role": "user", "content": "Hello, are you online?"}],
                model=provider.model_id or "default",
                max_tokens=5
            ))
            duration = (datetime.now() - start_time).total_seconds() * 1000
            loop.close()
            
            return jsonify({
                'success': True,
                'status': 'healthy',
                'model': response.model or provider.model_id,
                'latency_ms': round(duration, 2),
                'message': 'Provider connection successful'
            })
            
        except Exception as exc:
            loop.close()
            raise exc

    except Exception as exc:
        logger.error("Provider test failed for %s", provider_id, exc_info=True)
        # Classify the failure so the UI can show an actionable message
        # (e.g. "invalid API key") instead of a generic error.
        raw = str(exc).lower()
        if any(m in raw for m in ("401", "invalid api key", "invalid_api_key",
                                  "incorrect api key", "unauthorized", "authentication",
                                  "api key not valid", "permission denied", "403", "forbidden")):
            return jsonify({
                'success': False,
                'status': 'invalid_api_key',
                'error': 'Invalid API key',
                'detail': 'The saved API key was rejected by the provider. Update the key and try again.',
                'code': 'INVALID_API_KEY',
            }), 401
        if any(m in raw for m in ("429", "rate limit", "quota", "insufficient_quota", "billing")):
            return jsonify({
                'success': False,
                'status': 'rate_limited',
                'error': 'Rate limited or quota exceeded',
                'detail': 'The provider rejected the request due to rate limits or quota. Check your plan/billing.',
                'code': 'RATE_LIMITED',
            }), 429
        if any(m in raw for m in ("model", "not found", "does not exist", "unsupported")):
            return jsonify({
                'success': False,
                'status': 'invalid_model',
                'error': 'Model unavailable',
                'detail': 'The configured model is not available for this key/provider.',
                'code': 'INVALID_MODEL',
            }), 422
        if any(m in raw for m in ("timeout", "timed out", "connection", "network",
                                  "unreachable", "getaddrinfo", "ssl")):
            return jsonify({
                'success': False,
                'status': 'network_error',
                'error': 'Network error reaching provider',
                'detail': 'Could not reach the provider endpoint. Check your internet connection.',
                'code': 'NETWORK_ERROR',
            }), 504
        return jsonify({
            'success': False,
            'status': 'error',
            'error': 'Provider connectivity check failed',
            'detail': 'The provider test failed for an unexpected reason. See logs for details.',
            'code': 'PROVIDER_TEST_FAILED',
        }), 502


# ============== AI Governance Registry ==============

@admin_bp.route('/prompt-templates', methods=['GET'])
@login_required
def list_prompt_templates():
    """List registered prompt templates."""
    query = PromptTemplate.query.order_by(PromptTemplate.template_key.asc(), PromptTemplate.created_at.desc())
    if not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        query = query.filter(PromptTemplate.is_active)
    templates = query.all()
    return jsonify({'prompt_templates': [template.to_dict() for template in templates]})


@admin_bp.route('/prompt-templates', methods=['POST'])
@admin_required
def create_prompt_template():
    """Create a versioned prompt template."""
    data = request.get_json() or {}
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
        created_by=current_user.id,
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
    template = PromptTemplate.query.get(template_id)
    if not template:
        return jsonify({'error': 'Not found'}), 404

    template.approval_state = 'approved'
    template.approved_by = current_user.id
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
@login_required
def list_routing_policies():
    """List registered model routing policies."""
    query = ModelRoutingPolicy.query.order_by(
        ModelRoutingPolicy.policy_name.asc(),
        ModelRoutingPolicy.created_at.desc(),
    )
    if not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        query = query.filter(ModelRoutingPolicy.is_active)
    policies = query.all()
    return jsonify({'routing_policies': [policy.to_dict() for policy in policies]})


@admin_bp.route('/routing-policies', methods=['POST'])
@admin_required
def create_routing_policy():
    """Create a versioned model routing policy."""
    data = request.get_json() or {}
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
        created_by=current_user.id,
    )
    db.session.add(policy)
    db.session.commit()
    return jsonify(policy.to_dict()), 201


@admin_bp.route('/ai-audit', methods=['GET'])
@login_required
def list_ai_audit_events():
    """List AI audit trail events with model/version/policy metadata."""
    limit = request.args.get('limit', 100, type=int)
    limit = max(1, min(limit, 500))
    query = AIAuditEvent.query.order_by(AIAuditEvent.created_at.desc())
    if not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        query = query.filter_by(user_id=current_user.id)
    events = query.limit(limit).all()
    return jsonify({'events': [event.to_dict() for event in events]})


# ============== API Key Management ==============

@admin_bp.route('/api-keys', methods=['GET'])
@login_required
def list_api_keys():
    """List API keys (admin sees all, users see their own)."""
    if hasattr(current_user, 'is_admin') and current_user.is_admin:
        keys = ExternalAPIKey.query.order_by(ExternalAPIKey.created_at.desc()).all()
    else:
        keys = ExternalAPIKey.query.filter_by(user_id=current_user.id).order_by(
            ExternalAPIKey.created_at.desc()
        ).all()
    
    return jsonify({
        'api_keys': [k.to_dict() for k in keys]
    })


@admin_bp.route('/api-keys', methods=['POST'])
@login_required
def create_api_key():
    """Create a new API key."""
    data = request.get_json() or {}
    
    if not data.get('name'):
        return jsonify({'error': 'name required'}), 400
    
    # Generate key
    full_key, prefix, key_hash = ExternalAPIKey.generate_key()
    
    api_key = ExternalAPIKey(
        name=data['name'],
        key_prefix=prefix,
        key_hash=key_hash,
        user_id=current_user.id,
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
@login_required
def revoke_api_key(key_id):
    """Revoke an API key."""
    parsed = _parse_uuid_or_404(key_id, 'key_id')
    if isinstance(parsed, tuple):
        return parsed
    api_key = ExternalAPIKey.query.get_or_404(parsed)
    
    # Only owner or admin can revoke
    if api_key.user_id != current_user.id:
        if not (hasattr(current_user, 'is_admin') and current_user.is_admin):
            return jsonify({'error': 'Access denied'}), 403
    
    api_key.is_active = False
    db.session.commit()
    
    return jsonify({'message': 'API key revoked'})


# ============== Usage Analytics ==============

@admin_bp.route('/usage', methods=['GET'])
@login_required
def get_usage():
    """Get usage analytics."""
    from sqlalchemy import func
    from datetime import timedelta
    
    # Filter by time range
    days = request.args.get('days', 7, type=int)
    since = db.func.now() - timedelta(days=days)
    
    query = LLMProviderUsage.query.filter(LLMProviderUsage.created_at >= since)
    
    # Non-admins only see their own usage
    if not (hasattr(current_user, 'is_admin') and current_user.is_admin):
        query = query.filter_by(user_id=current_user.id)
    
    # Aggregate stats
    total_requests = query.count()
    successful = query.filter_by(success=True).count()
    total_tokens_in = db.session.query(func.sum(LLMProviderUsage.tokens_in)).filter(
        LLMProviderUsage.created_at >= since
    ).scalar() or 0
    total_tokens_out = db.session.query(func.sum(LLMProviderUsage.tokens_out)).filter(
        LLMProviderUsage.created_at >= since
    ).scalar() or 0
    avg_latency = db.session.query(func.avg(LLMProviderUsage.latency_ms)).filter(
        LLMProviderUsage.created_at >= since, LLMProviderUsage.success
    ).scalar() or 0
    try:
        total_estimated_cost = db.session.query(func.sum(LLMProviderUsage.estimated_cost_usd)).filter(
            LLMProviderUsage.created_at >= since
        ).scalar() or 0
    except Exception:
        total_estimated_cost = 0
    
    # Usage by provider
    by_provider = db.session.query(
        LLMProvider.name,
        func.count(LLMProviderUsage.id),
        func.sum(LLMProviderUsage.tokens_in),
        func.sum(LLMProviderUsage.tokens_out),
        func.sum(LLMProviderUsage.estimated_cost_usd),
    ).join(LLMProvider).filter(
        LLMProviderUsage.created_at >= since
    ).group_by(LLMProvider.name).all()
    
    return jsonify({
        'period_days': days,
        'total_requests': total_requests,
        'successful_requests': successful,
        'success_rate': successful / total_requests if total_requests > 0 else 0,
        'total_tokens_in': total_tokens_in,
        'total_tokens_out': total_tokens_out,
        'total_estimated_cost_usd': float(total_estimated_cost),
        'avg_latency_ms': round(avg_latency, 2),
        'by_provider': [
            {
                'provider': row[0],
                'requests': row[1],
                'tokens_in': row[2] or 0,
                'tokens_out': row[3] or 0,
                'estimated_cost_usd': float(row[4] or 0) if len(row) > 4 else 0.0,
            }
            for row in by_provider
        ]
    })


def register_gateway_routes(app):
    """Register gateway blueprints with the app."""
    app.register_blueprint(gateway_bp)
    app.register_blueprint(admin_bp)
