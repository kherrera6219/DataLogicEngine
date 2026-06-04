"""
Truth Engine API Blueprints

Provides REST API endpoints for Truth Engine v7.3 modules.
"""

import logging
from typing import Optional, TYPE_CHECKING
from flask import Blueprint, request, jsonify, Response, stream_with_context
from functools import wraps

if TYPE_CHECKING:
    from backend.truth_engine.truth_core.engine import TruthCoreEngine
    from backend.truth_engine.truth_gate.gateway import TruthGateGateway
    from backend.truth_engine.truth_memory.manager import TruthMemoryManager
    from backend.truth_engine.truth_link.bus import TruthLinkBus

logger = logging.getLogger(__name__)

truth_api = Blueprint('truth_api', __name__)

_truth_core: Optional['TruthCoreEngine'] = None  # type: ignore
_truth_gate: Optional['TruthGateGateway'] = None  # type: ignore
_truth_memory: Optional['TruthMemoryManager'] = None  # type: ignore
_truth_link: Optional['TruthLinkBus'] = None  # type: ignore

def get_truth_core_engine() -> 'TruthCoreEngine': # type: ignore
    """Access the TruthCoreEngine singleton."""
    _lazy_init_truth_engine()
    return _truth_core # type: ignore

def get_truth_gate() -> 'TruthGateGateway': # type: ignore
    """Access the TruthGateGateway singleton."""
    _lazy_init_truth_engine()
    return _truth_gate # type: ignore

def get_truth_memory() -> 'TruthMemoryManager': # type: ignore
    """Access the TruthMemoryManager singleton."""
    _lazy_init_truth_engine()
    return _truth_memory # type: ignore

def get_truth_link() -> 'TruthLinkBus': # type: ignore
    """Access the TruthLinkBus singleton."""
    _lazy_init_truth_engine()
    return _truth_link # type: ignore


def init_truth_engine(db_session):
    """Initialize Truth Engine components with database session."""
    global _truth_core, _truth_gate, _truth_memory, _truth_link
    
    from backend.truth_engine.truth_core.engine import TruthCoreEngine
    from backend.truth_engine.truth_gate.gateway import TruthGateGateway
    from backend.truth_engine.truth_memory.manager import TruthMemoryManager
    from backend.truth_engine.truth_link.bus import TruthLinkBus
    
    simulation_engine = None
    try:
        from core.simulation.legacy_simulation_engine import create_simulation_engine
        simulation_engine = create_simulation_engine()
        logger.info("SimulationEngine created for TruthCore integration")
    except Exception as e:
        logger.warning(f"Could not create SimulationEngine: {e}")
    
    from backend.knowledge_algorithms.ka_master_controller import get_controller
    ka_controller = get_controller()
    
    _truth_core = TruthCoreEngine(
        db_session=db_session,
        simulation_engine=simulation_engine,
        ka_controller=ka_controller
    )
    _truth_gate = TruthGateGateway(db_session=db_session)
    _truth_memory = TruthMemoryManager(db_session=db_session)
    _truth_link = TruthLinkBus(db_session=db_session)
    
    logger.info("Truth Engine components initialized")


def _lazy_init_truth_engine():
    """Lazy initialization of Truth Engine on first use."""
    global _truth_core, _truth_gate, _truth_memory, _truth_link
    
    if _truth_core is not None:
        return  # Already initialized
    
    from flask import current_app
    from extensions import db
    
    with current_app.app_context():
        init_truth_engine(db.session)


def require_truth_engine(f):
    """Decorator to ensure Truth Engine is initialized (lazy loading)."""
    import inspect
    @wraps(f)
    async def decorated(*args, **kwargs):
        # Lazy initialize on first request
        _lazy_init_truth_engine()
        if not all([_truth_core, _truth_gate, _truth_memory, _truth_link]):
            return jsonify({'error': 'Truth Engine initialization failed'}), 503
        
        if inspect.iscoroutinefunction(f):
            return await f(*args, **kwargs)
        return f(*args, **kwargs)
    return decorated


def get_truth_engine_status():
    """Get the current status of all Truth Engine components.
    
    Returns:
        dict: Status information for TruthCore, TruthGate, TruthMemory, TruthLink
    """
    status = {
        'truthcore': {
            'active_workflows': 0,
            'initialized': _truth_core is not None
        },
        'truthgate': {
            'requests_processed': 0,
            'initialized': _truth_gate is not None
        },
        'truthmemory': {
            'cached_items': 0,
            'hash_entries': 0,
            'cache_hit_rate': '0%',
            'initialized': _truth_memory is not None
        },
        'truthlink': {
            'events_today': 0,
            'subscribers': 0,
            'dlq_items': 0,
            'initialized': _truth_link is not None
        }
    }
    
    if _truth_core:
        try:
            core_stats = _truth_core.get_stats() if hasattr(_truth_core, 'get_stats') else {}
            status['truthcore'].update(core_stats)
        except Exception as e:
            logger.warning(f"Error getting TruthCore stats: {e}")
    
    if _truth_gate:
        try:
            gate_stats = _truth_gate.get_stats() if hasattr(_truth_gate, 'get_stats') else {}
            status['truthgate'].update(gate_stats)
        except Exception as e:
            logger.warning(f"Error getting TruthGate stats: {e}")
    
    if _truth_memory:
        try:
            memory_stats = _truth_memory.get_stats() if hasattr(_truth_memory, 'get_stats') else {}
            status['truthmemory'].update(memory_stats)
        except Exception as e:
            logger.warning(f"Error getting TruthMemory stats: {e}")
    
    if _truth_link:
        try:
            link_stats = _truth_link.get_stats() if hasattr(_truth_link, 'get_stats') else {}
            status['truthlink'].update(link_stats)
        except Exception as e:
            logger.warning(f"Error getting TruthLink stats: {e}")
    
    return status


@truth_api.route('/health', methods=['GET'])
def health():
    """Health check for Truth Engine."""
    return jsonify({
        'status': 'healthy',
        'version': '7.3',
        'components': {
            'truth_core': _truth_core is not None,
            'truth_gate': _truth_gate is not None,
            'truth_memory': _truth_memory is not None,
            'truth_link': _truth_link is not None
        }
    })


@truth_api.route('/core/session', methods=['POST'])
@require_truth_engine
async def create_session():

    """Create a new TruthCore processing session."""
    data = request.get_json() or {}
    
    query = data.get('query')
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    user_id = data.get('user_id')
    tenant_id = data.get('tenant_id')
    context = data.get('context', {})
    
    gate_result = _truth_gate.evaluate({
        'query': query,
        'tenant_id': tenant_id,
        'user_context': context
    })
    if not gate_result.get('passed'):
        return jsonify({
            'error': gate_result.get('block_reason', 'Request blocked'),
            'security_flags': gate_result.get('security_flags', [])
        }), 403
    
    session = await _truth_core.create_session(
        query=gate_result.get('sanitized_query', query),
        user_id=user_id,
        tenant_id=tenant_id,
        context=context
    )
    
    _truth_link.publish(
        source_module='truth_core',
        message_type='session_created',
        payload={'session_id': session['session_id'], 'tier': session['tier']},
        session_id=session['session_id']
    )
    
    return jsonify(session), 201



@truth_api.route('/core/session/<session_id>/process', methods=['POST'])
@require_truth_engine
async def process_session(session_id):

    """Process a TruthCore session."""
    try:
        result = await _truth_core.process(session_id)
        
        _truth_memory.record_session(result)
        
        _truth_link.publish(
            source_module='truth_core',
            message_type='session_completed',
            payload={'session_id': session_id, 'status': result['status']},
            session_id=session_id
        )
        
        return jsonify(result)


    except ValueError as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        return jsonify({'error': 'Processing failed'}), 500


@truth_api.route('/core/session/<session_id>', methods=['GET'])
@require_truth_engine
def get_session(session_id):
    """Get session status."""
    session = _truth_core.get_session_status(session_id)
    if 'error' in session:
        return jsonify(session), 404
    return jsonify(session)


@truth_api.route('/core/tiers', methods=['GET'])
@require_truth_engine
def get_tiers():
    """Get tier information."""
    tier = request.args.get('tier')
    return jsonify(_truth_core.get_tier_info(tier))


@truth_api.route('/gate/evaluate', methods=['POST'])
@require_truth_engine
def evaluate_request():
    """Evaluate a request through TruthGate."""
    data = request.get_json() or {}
    result = _truth_gate.evaluate(data)
    return jsonify(result)


@truth_api.route('/gate/stats', methods=['GET'])
@require_truth_engine
def gate_stats():
    """Get TruthGate statistics."""
    return jsonify(_truth_gate.get_stats())


@truth_api.route('/gate/budget/<tenant_id>', methods=['GET'])
@require_truth_engine
def get_budget(tenant_id):
    """Get budget status for tenant."""
    try:
        budget = _truth_gate.budget_manager.get_budget(tenant_id)
        return jsonify(budget)
    except Exception as e:
        logger.error(f"Failed to get budget: {e}")
        return jsonify({'error': 'Failed to retrieve budget'}), 500


@truth_api.route('/gate/budget/<tenant_id>/reset', methods=['POST'])
@require_truth_engine
def reset_budget(tenant_id):
    """Reset budget for tenant."""
    try:
        data = request.get_json() or {}
        new_limit = data.get('budget_limit')
        result = _truth_gate.budget_manager.reset_budget(tenant_id, new_limit)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Failed to reset budget: {e}")
        return jsonify({'error': 'Failed to reset budget'}), 500


@truth_api.route('/memory/session/<session_id>', methods=['GET'])
@require_truth_engine
def get_memory_session(session_id):
    """Get session from TruthMemory."""
    session = _truth_memory.get_session(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    return jsonify(session)


@truth_api.route('/memory/artifacts/<session_id>', methods=['GET'])
@require_truth_engine
def get_artifacts(session_id):
    """Get artifacts for a session."""
    artifact_type = request.args.get('type')
    artifacts = _truth_memory.get_artifacts(session_id, artifact_type)
    return jsonify({'session_id': session_id, 'artifacts': artifacts})


@truth_api.route('/memory/artifacts/<session_id>', methods=['POST'])
@require_truth_engine
def store_artifact(session_id):
    """Store an artifact for a session."""
    data = request.get_json() or {}
    
    artifact_type = data.get('type')
    content = data.get('content')
    metadata = data.get('metadata')
    
    if not artifact_type or content is None:
        return jsonify({'error': 'Type and content are required'}), 400
    
    artifact = _truth_memory.store_artifact(session_id, artifact_type, content, metadata)
    return jsonify(artifact), 201


@truth_api.route('/memory/explain/<session_id>', methods=['GET'])
@require_truth_engine
def explain_session(session_id):
    """Get Article 13 explainability data for session."""
    data = _truth_memory.get_explainability_data(session_id)
    return jsonify(data)


@truth_api.route('/memory/stats', methods=['GET'])
@require_truth_engine
def memory_stats():
    """Get TruthMemory statistics."""
    return jsonify(_truth_memory.get_stats())


@truth_api.route('/memory/metrics/<metric_name>', methods=['GET'])
@require_truth_engine
def get_metrics(metric_name):
    """Get metric values."""
    tier = request.args.get('tier')
    metrics = _truth_memory.metrics.get_metric(metric_name, tier=tier)
    aggregate = _truth_memory.metrics.get_aggregate(metric_name)
    
    return jsonify({
        'metric_name': metric_name,
        'values': metrics[:100],
        'aggregate': aggregate
    })


@truth_api.route('/link/publish', methods=['POST'])
@require_truth_engine
def publish_message():
    """Publish a message to the event bus."""
    data = request.get_json() or {}
    
    source_module = data.get('source_module', 'api')
    message_type = data.get('message_type')
    payload = data.get('payload', {})
    target_module = data.get('target_module')
    priority = data.get('priority', 1)
    session_id = data.get('session_id')
    
    if not message_type:
        return jsonify({'error': 'Message type is required'}), 400
    
    message = _truth_link.publish(
        source_module=source_module,
        message_type=message_type,
        payload=payload,
        target_module=target_module,
        priority=priority,
        session_id=session_id
    )
    
    return jsonify(message), 201


@truth_api.route('/link/stats', methods=['GET'])
@require_truth_engine
def link_stats():
    """Get TruthLink statistics."""
    return jsonify(_truth_link.get_stats())


@truth_api.route('/link/pending', methods=['GET'])
@require_truth_engine
def pending_messages():
    """Get pending messages."""
    target_module = request.args.get('module')
    messages = _truth_link.get_pending_messages(target_module)
    return jsonify({'pending': messages, 'count': len(messages)})


@truth_api.route('/link/dead-letter', methods=['GET'])
@require_truth_engine
def dead_letter_queue():
    """Get dead letter queue."""
    messages = _truth_link.get_dead_letter_queue()
    return jsonify({'dead_letter': messages, 'count': len(messages)})


@truth_api.route('/link/stream/<client_id>', methods=['GET'])
@require_truth_engine
def stream_events(client_id):
    """SSE endpoint for real-time events."""
    def generate():
        try:
            for event in _truth_link.sse_transport.stream_events(client_id):
                yield event
        except GeneratorExit:
            _truth_link.sse_transport.unregister_client(client_id)
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            _truth_link.sse_transport.unregister_client(client_id)
    
    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


@truth_api.route('/compliance/report', methods=['GET'])
@require_truth_engine
def compliance_report():
    """Get compliance report."""
    try:
        tenant_id = request.args.get('tenant_id')
        report = _truth_gate.compliance_enforcer.get_compliance_report(tenant_id)
        return jsonify(report)
    except Exception as e:
        logger.error(f"Failed to generate compliance report: {e}")
        return jsonify({'error': 'Failed to generate compliance report'}), 500


@truth_api.route('/compliance/audit/<session_id>', methods=['GET'])
@require_truth_engine
def audit_trail(session_id):
    """Get audit trail for session."""
    try:
        trail = _truth_gate.compliance_enforcer.get_audit_trail(session_id)
        return jsonify({'session_id': session_id, 'audit_trail': trail})
    except Exception as e:
        logger.error(f"Failed to get audit trail: {e}")
        return jsonify({'error': 'Failed to get audit trail'}), 500
