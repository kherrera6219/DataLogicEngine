"""
Knowledge Algorithm API Endpoints

Provides REST API endpoints for managing and executing Knowledge Algorithms (KA-001 to KA-114).
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, UTC
import logging

from flask import Blueprint, request, jsonify

from backend.auth.api_decorators import api_login_required, get_authenticated_principal
from backend.knowledge_algorithms.ka_master_controller import get_controller

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
    """Return recent KA execution records for the audit log page."""
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


@ka_bp.route('/algorithms', methods=['GET'])
@api_login_required
def list_algorithms():
    """List all available Knowledge Algorithms"""
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
    """Get details of a specific Knowledge Algorithm by ID (e.g., KA-001, KA-114)"""
    try:
        ka_id_norm, err = _parse_ka_id_param(ka_id)
        if err:
            return err

        if ka_id_norm not in _get_controller().algorithms:
            return _error_response('Algorithm not found', 404)

        ka_data = _get_controller().algorithms[ka_id_norm].get("metadata", {})
        return jsonify({'success': True, 'algorithm': format_algorithm(ka_data)}), 200
    except Exception:
        logger.exception("Error getting algorithm")
        return _error_response('Algorithm details are unavailable', 500)


@ka_bp.route('/algorithms/<ka_id>/execute', methods=['POST'])
@api_login_required
def execute_algorithm(ka_id):
    """Execute a Knowledge Algorithm"""
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

        ka_result = _get_controller().execute_algorithm(ka_id_norm, input_data)

        result = {
            'algorithm_id': ka_id_norm,
            'executed_at': datetime.now(UTC).isoformat(),
            'status': 'completed' if ka_result.get('success', True) else 'failed',
            'output': ka_result.get('output', ka_result),
            'log': ka_result.get('log', ''),
            'execution_time_ms': int(ka_result.get('execution_time', 0) * 1000)
        }

        logger.info("Executed %s for user %s", ka_id_norm, _current_user_id())

        return jsonify({'success': ka_result.get('success', True), 'result': result}), 200
    except Exception:
        logger.exception("Error executing algorithm")
        return _error_response('Algorithm execution failed', 500)


@ka_bp.route('/categories', methods=['GET'])
@api_login_required
def list_categories():
    """List all KA categories with their algorithms"""
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
                ka_result = _get_controller().execute_algorithm(ka_id_norm, input_data)
                results.append({
                    'ka_id': ka_meta.get('KA_ID', ka_id_norm),
                    'name': ka_meta.get('KA_Name') or ka_meta.get('KA_ID') or ka_id_norm,
                    'short_name': ka_meta.get('Short_Name'),
                    'category': ka_meta.get('Category'),
                    'status': 'completed' if ka_result.get('success', True) else 'failed',
                    'output': ka_result.get('output', {}),
                    'execution_time_ms': int(ka_result.get('execution_time', 0) * 1000),
                    'layers_used': parse_list_field(ka_meta.get('Primary_Layers'))
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
        'version': '2.0.0',
        'registry_source': 'ka_registry.json'
    }), 200
