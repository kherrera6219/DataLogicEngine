"""
LLM Gateway API Endpoints

Provides the public API for external clients to access UKG-enhanced LLM.
Also includes admin endpoints for provider and API key management.
"""

import asyncio
from datetime import datetime
from functools import wraps
from flask import Blueprint, request, jsonify, Response, stream_with_context, g
from flask_login import login_required, current_user
import json
import logging
import os

from models import LLMProvider, LLMProviderUsage, ExternalAPIKey, ChatSession, ChatMessage
from backend.llm_gateway.gateway import LLMGateway, GatewayRequest
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


# ============== API Key Authentication ==============

def api_key_required(f):
    """Decorator for endpoints that accept API key or session auth."""
    import inspect
    @wraps(f)
    async def decorated(*args, **kwargs):
        # Check for API key in header
        api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if api_key and api_key.startswith('ukg_'):
            # Validate API key
            key_record = ExternalAPIKey.verify_key(api_key)
            if not key_record:
                return jsonify({'error': 'Invalid API key'}), 401
            
            # Rate Limiting (Redis-backed)
            if cache and key_record.rate_limit_rpm:
                limit_key = f"rl:{key_record.id}:{int(datetime.now().timestamp() // 60)}"
                # Use current minute bucket
                current_usage = cache.get(limit_key) or 0
                if current_usage >= key_record.rate_limit_rpm:
                    return jsonify({'error': 'Rate limit exceeded', 'limit': f'{key_record.rate_limit_rpm}/min'}), 429
                
                cache.set(limit_key, current_usage + 1, timeout=60)
            
            # Update usage stats
            key_record.total_requests += 1
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

@gateway_bp.route('/chat', methods=['POST'])
@api_key_required
@api_response
async def gateway_chat():

    """
    Main gateway endpoint for chat completions.
    Validates request using Pydantic schema.
    """
    # Build request from validated model
    gateway_request = GatewayRequest(
        messages=[m.model_dump() for m in req_model.messages],
        provider=req_model.provider,
        model=req_model.model,
        mode=req_model.mode,
        constraints=req_model.constraints,
        run_ukg_pipeline=req_model.run_ukg_pipeline,
        temperature=req_model.temperature,
        max_tokens=req_model.max_tokens,
        user_id=g.user_id,
        api_key_id=str(g.api_key.id) if g.api_key else None,
        meta=req_model.meta,
    )
    
    # Process request
    gateway = LLMGateway()
    response = await gateway.process(gateway_request)
    
    if not response:
        return {'error': 'No response generated from any provider'}, 503

    return {
        'response': response.content,
        'run_id': response.run_id,
        'provider_used': response.provider_used,
        'model_used': response.model_used,
        'usage': response.usage,
        'trace_summary': response.trace_summary,
        'coordinates': response.coordinates,
        'confidence_score': response.confidence_score,
        'claims': response.claims,
        'evidence_count': response.evidence_count,
        'warnings': response.warnings,
    }


@gateway_bp.route('/chat/stream', methods=['POST'])
@api_key_required
def gateway_chat_stream():
    """
    Streaming gateway endpoint.
    
    Returns Server-Sent Events (SSE) stream.
    """
    data = request.get_json() or {}
    
    messages = data.get('messages', [])
    if not messages:
        return jsonify({'error': 'messages required'}), 400
    
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
        api_key_id=str(g.api_key.id) if g.api_key else None,
    )
    
    def generate():
        gateway = LLMGateway()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            async def stream():
                async for chunk in gateway.process_stream(gateway_request):
                    yield f"data: {json.dumps(chunk)}\n\n"
            
            # Run async generator
            gen = stream()
            while True:
                try:
                    chunk = loop.run_until_complete(gen.__anext__())
                    yield chunk
                except StopAsyncIteration:
                    break
                    
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
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
    
    return jsonify({
        'providers': [
            {
                'name': p.name,
                'type': p.provider_type,
                'model': p.model_id,
                'is_default': p.is_default,
            }
            for p in providers
        ]
    })


@gateway_bp.route('/keys', methods=['POST'])
@login_required
def save_provider_key():
    """Create or update an LLM provider API key (basic UI helper)."""
    data = request.get_json() or {}
    provider_type = data.get('provider')
    api_key = data.get('key')
    
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
            created_by=current_user.id,
        )
        db.session.add(provider)
    
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


@gateway_bp.route('/sessions/<session_id>/messages', methods=['GET'])
@api_key_required
def get_session_messages(session_id):
    """Retrieve message history for a session."""
    import uuid
    messages = ChatMessage.query.filter_by(session_id=uuid.UUID(session_id))\
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
    provider = LLMProvider.query.get_or_404(provider_id)
    return jsonify(provider.to_dict(include_key=True))


@admin_bp.route('/providers/<provider_id>', methods=['PATCH'])
@admin_required
def update_provider(provider_id):
    """Update a provider."""
    provider = LLMProvider.query.get_or_404(provider_id)
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
    provider = LLMProvider.query.get_or_404(provider_id)
    db.session.delete(provider)
    db.session.commit()
    return jsonify({'message': 'Provider deleted'}), 200


@gateway_bp.route('/providers/<provider_id>/test', methods=['POST'])
@login_required
def test_provider(provider_id):
    """Test provider connection using the Gateway SDK adapter."""
    provider = LLMProvider.query.get_or_404(provider_id)
    
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
            })

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

    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'error',
            'error': str(e),
        })


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
        api_key.expires_at = db.func.now() + timedelta(days=data['expires_in_days'])
    
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
    api_key = ExternalAPIKey.query.get_or_404(key_id)
    
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
        LLMProviderUsage.created_at >= since, LLMProviderUsage.success == True
    ).scalar() or 0
    
    # Usage by provider
    by_provider = db.session.query(
        LLMProvider.name,
        func.count(LLMProviderUsage.id),
        func.sum(LLMProviderUsage.tokens_in),
        func.sum(LLMProviderUsage.tokens_out),
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
        'avg_latency_ms': round(avg_latency, 2),
        'by_provider': [
            {
                'provider': name,
                'requests': count,
                'tokens_in': tokens_in or 0,
                'tokens_out': tokens_out or 0,
            }
            for name, count, tokens_in, tokens_out in by_provider
        ]
    })


def register_gateway_routes(app):
    """Register gateway blueprints with the app."""
    app.register_blueprint(gateway_bp)
    app.register_blueprint(admin_bp)
