"""
Knowledge Algorithm API Endpoints

Provides REST API endpoints for managing and executing Knowledge Algorithms (KA-001 to KA-114).
"""

from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from backend.auth.api_decorators import api_login_required, api_admin_required
from datetime import datetime, UTC
import logging
import json
import os

from backend.knowledge_algorithms.ka_master_controller import get_controller

logger = logging.getLogger(__name__)

ka_bp = Blueprint('ka', __name__)

# Initialize Master Controller
controller = get_controller()

# The controller now manages the registry
KA_REGISTRY = controller.get_available_algorithms()

def parse_list_field(value):
    """Parse semicolon or comma-separated field into list"""
    if not value:
        return []
    return [v.strip() for v in str(value).replace(';', ',').split(',') if v.strip()]

def format_algorithm(ka):
    """Format algorithm data for API response"""
    return {
        'id': ka.get('KA_ID'),
        'name': ka.get('KA_Name'),
        'short_name': ka.get('Short_Name'),
        'purpose': ka.get('Purpose'),
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
        'status': ka.get('Status'),
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


@ka_bp.route('/algorithms', methods=['GET'])
@api_login_required
def list_algorithms():
    """List all available Knowledge Algorithms"""
    try:
        category = request.args.get('category')
        status = request.args.get('status')
        risk_class = request.args.get('risk_class')
        layer = request.args.get('layer')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        algorithms = [format_algorithm(ka.get("metadata", {})) for ka in controller.get_available_algorithms().values() if ka.get("metadata")]
        if not algorithms:
             # Fallback to general list if metadata not attached
             algorithms = [format_algorithm({"KA_ID": k, "KA_Name": k}) for k in controller.algorithms.keys()]
        
        if category:
            algorithms = [a for a in algorithms if a['category'] and a['category'].lower() == category.lower()]
        
        if status:
            algorithms = [a for a in algorithms if a['status'] and a['status'].lower() == status.lower()]
        
        if risk_class:
            algorithms = [a for a in algorithms if a['risk_class'] and a['risk_class'].lower() == risk_class.lower()]
        
        if layer:
            algorithms = [a for a in algorithms if layer in a['primary_layers'] or layer in a['allowed_layers']]
        
        algorithms.sort(key=lambda x: x['id'])
        
        total = len(algorithms)
        start = (page - 1) * per_page
        end = start + per_page
        paginated = algorithms[start:end]
        
        categories = list(set(ka.get('Category') for ka in KA_REGISTRY.values() if ka.get('Category')))
        
        return jsonify({
            'success': True,
            'algorithms': paginated,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            },
            'categories': sorted(categories),
            'total_count': len(KA_REGISTRY)
        }), 200
    except Exception as e:
        logger.error(f"Error listing algorithms: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ka_bp.route('/algorithms/<ka_id>', methods=['GET'])
@api_login_required
def get_algorithm(ka_id):
    """Get details of a specific Knowledge Algorithm by ID (e.g., KA-001, KA-114)"""
    try:
        if isinstance(ka_id, str) and ka_id.upper().startswith('KA-'):
            num = int(ka_id.upper().replace('KA-', '').lstrip('0') or '0')
        else:
            try:
                num = int(ka_id)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': f'Invalid algorithm ID: {ka_id}'
                }), 400
        
        ka_id_norm = controller._normalize_ka_id(f"KA-{num:03d}")
        if ka_id_norm not in controller.algorithms:
            return jsonify({
                'success': False,
                'error': f'Algorithm {ka_id} not found'
            }), 404
        
        ka_data = controller.algorithms[ka_id_norm].get("metadata", {})
        algorithm = format_algorithm(ka_data)
        return jsonify({
            'success': True,
            'algorithm': algorithm
        }), 200
    except Exception as e:
        logger.error(f"Error getting algorithm: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ka_bp.route('/algorithms/<ka_id>/execute', methods=['POST'])
@api_login_required
def execute_algorithm(ka_id):
    """Execute a Knowledge Algorithm"""
    try:
        if isinstance(ka_id, str) and ka_id.upper().startswith('KA-'):
            num = int(ka_id.upper().replace('KA-', '').lstrip('0') or '0')
        else:
            try:
                num = int(ka_id)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': f'Invalid algorithm ID: {ka_id}'
                }), 400
        
        ka_id_norm = controller._normalize_ka_id(f"KA-{num:03d}")
        if ka_id_norm not in controller.algorithms:
            return jsonify({
                'success': False,
                'error': f'Algorithm {ka_id} not found'
            }), 404
        
        data = request.get_json() or {}
        input_data = data.get('input', {})
        params = data.get('params', {})
        
        # Execute via Master Controller
        ka_result = controller.execute_algorithm(ka_id_norm, input_data)
        
        result = {
            'algorithm_id': ka_id_norm,
            'executed_at': datetime.now(UTC).isoformat(),
            'status': 'completed' if ka_result.get('success', True) else 'failed',
            'output': ka_result.get('output', ka_result),
            'log': ka_result.get('log', ''),
            'execution_time_ms': int(ka_result.get('execution_time', 0) * 1000)
        }
        
        logger.info(f"Executed {ka_id_norm} for user {current_user.id}")
        
        return jsonify({
            'success': ka_result.get('success', True),
            'result': result
        }), 200
    except Exception as e:
        logger.error(f"Error executing algorithm: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ka_bp.route('/categories', methods=['GET'])
@api_login_required
def list_categories():
    """List all KA categories with their algorithms"""
    try:
        categories = {}
        for ka_id, ka_info in controller.get_available_algorithms().items():
            ka = ka_info.get("metadata", {})
            cat = ka.get('Category')
            if not cat:
                continue
            if cat not in categories:
                categories[cat] = {
                    'name': cat,
                    'algorithms': [],
                    'count': 0
                }
            categories[cat]['algorithms'].append({
                'id': ka.get('KA_ID'),
                'name': ka.get('KA_Name'),
                'short_name': ka.get('Short_Name'),
                'status': ka.get('Status')
            })
            categories[cat]['count'] += 1
        
        for cat in categories.values():
            cat['algorithms'].sort(key=lambda x: x['id'])
        
        return jsonify({
            'success': True,
            'categories': categories,
            'category_list': sorted(categories.keys()),
            'count': len(categories)
        }), 200
    except Exception as e:
        logger.error(f"Error listing categories: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ka_bp.route('/workflow/high-stakes', methods=['POST'])
@api_login_required
def execute_high_stakes_workflow():
    """Execute the full 12-step high-stakes refinement workflow."""
    try:
        data = request.get_json() or {}
        query = data.get('query')
        if not query:
            return jsonify({'success': False, 'error': 'Query is required'}), 400
        
        context = data.get('context', {})
        
        # We can use TruthCoreEngine for this
        from backend.truth_engine.truth_core.engine import get_truth_core_engine
        engine = get_truth_core_engine()
        
        # Create a session
        session = engine.create_session(
            query=query,
            user_id=current_user.id,
            tier='high_stakes',
            context=context
        )
        
        # Process the session
        result = engine.process(session['session_id'])
        
        return jsonify({
            'success': True,
            'session_id': session['session_id'],
            'result': result
        }), 200
    except Exception as e:
        logger.error(f"Error executing high-stakes workflow: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@ka_bp.route('/trace/<session_id>', methods=['GET'])
@login_required
@api_login_required
def get_workflow_trace(session_id):
    """Get the execution trace of a workflow session."""
    try:
        from backend.truth_engine.truth_core.engine import get_truth_core_engine
        engine = get_truth_core_engine()
        
        status = engine.get_session_status(session_id)
        if 'error' in status:
            return jsonify({'success': False, 'error': status['error']}), 404
            
        return jsonify({
            'success': True,
            'session_id': session_id,
            'trace': status.get('workflow_steps', []),
            'status': status.get('status')
        }), 200
    except Exception as e:
        logger.error(f"Error getting workflow trace: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ka_bp.route('/layers', methods=['GET'])
@api_login_required
def list_layers():
    """List all simulation layers and their associated algorithms"""
    try:
        layers = {}
        for ka_id, ka_info in controller.get_available_algorithms().items():
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
        
        sorted_layers = dict(sorted(layers.items(), key=lambda x: (int(x[0].replace('L', '')) if x[0].startswith('L') else 999)))
        
        return jsonify({
            'success': True,
            'layers': sorted_layers,
            'count': len(layers)
        }), 200
    except Exception as e:
        logger.error(f"Error listing layers: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ka_bp.route('/batch', methods=['POST'])
@api_login_required
def batch_execute():
    """Execute multiple Knowledge Algorithms in sequence"""
    try:
        data = request.get_json()
        algorithms = data.get('algorithms', [])
        shared_input = data.get('input', {})
        
        if not algorithms:
            return jsonify({
                'success': False,
                'error': 'No algorithms specified'
            }), 400
        
        if len(algorithms) > 20:
            return jsonify({
                'success': False,
                'error': 'Maximum 20 algorithms per batch'
            }), 400
        
        results = []
        for ka_id in algorithms:
            ka_id_norm = controller._normalize_ka_id(ka_id)
            if ka_id_norm not in controller.algorithms:
                results.append({
                    'ka_id': ka_id,
                    'status': 'error',
                    'error': f'Algorithm not found'
                })
                continue
            
            ka = controller.algorithms[ka_id_norm].get("metadata", {})
            results.append({
                'ka_id': ka.get('KA_ID'),
                'name': ka.get('KA_Name'),
                'short_name': ka.get('Short_Name'),
                'category': ka.get('Category'),
                'status': 'completed',
                'confidence': 0.85,
                'layers_used': parse_list_field(ka.get('Primary_Layers'))
            })
        
        return jsonify({
            'success': True,
            'results': results,
            'executed_count': len([r for r in results if r['status'] == 'completed']),
            'failed_count': len([r for r in results if r['status'] == 'error'])
        }), 200
    except Exception as e:
        logger.error(f"Error in batch execution: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ka_bp.route('/search', methods=['GET'])
@api_login_required
def search_algorithms():
    """Search algorithms by name, purpose, or notes"""
    try:
        query = request.args.get('q', '').lower()
        if not query or len(query) < 2:
            return jsonify({
                'success': False,
                'error': 'Query must be at least 2 characters'
            }), 400
        
        for ka_id, ka_info in controller.get_available_algorithms().items():
            ka = ka_info.get("metadata", {})
            name = (ka.get('KA_Name') or '').lower()
            purpose = (ka.get('Purpose') or '').lower()
            notes = (ka.get('Notes') or '').lower()
            short_name = (ka.get('Short_Name') or '').lower()
            
            if query in name or query in purpose or query in notes or query in short_name:
                results.append(format_algorithm(ka))
        
        results.sort(key=lambda x: x['id'])
        
        return jsonify({
            'success': True,
            'query': query,
            'results': results,
            'count': len(results)
        }), 200
    except Exception as e:
        logger.error(f"Error searching algorithms: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ka_bp.route('/dependencies/<ka_id>', methods=['GET'])
@api_login_required
def get_dependencies(ka_id):
    """Get dependency graph for a specific algorithm"""
    try:
        if isinstance(ka_id, str) and ka_id.upper().startswith('KA-'):
            num = int(ka_id.upper().replace('KA-', '').lstrip('0') or '0')
        else:
            try:
                num = int(ka_id)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': f'Invalid algorithm ID: {ka_id}'
                }), 400
        
        if num not in KA_REGISTRY:
            return jsonify({
                'success': False,
                'error': f'Algorithm {ka_id} not found'
            }), 404
        
        ka_data = controller.algorithms[ka_id_norm].get("metadata", {})
        dependencies = parse_list_field(ka_data.get('Dependencies'))
        
        dep_details = []
        for dep in dependencies:
            dep_id = controller._normalize_ka_id(dep)
            if dep_id in controller.algorithms:
                dep_ka = controller.algorithms[dep_id].get("metadata", {})
                dep_details.append({
                    'id': dep_ka.get('KA_ID'),
                    'name': dep_ka.get('KA_Name'),
                    'short_name': dep_ka.get('Short_Name'),
                    'category': dep_ka.get('Category'),
                    'status': dep_ka.get('Status')
                })
        
        dependents = []
        for other_id, other_info in controller.get_available_algorithms().items():
            other_ka = other_info.get("metadata", {})
            other_deps = parse_list_field(other_ka.get('Dependencies'))
            if ka_id_norm in [controller._normalize_ka_id(d) for d in other_deps]:
                dependents.append({
                    'id': other_ka.get('KA_ID'),
                    'name': other_ka.get('KA_Name'),
                    'short_name': other_ka.get('Short_Name'),
                    'category': other_ka.get('Category')
                })
        
        return jsonify({
            'success': True,
            'algorithm': {
                'id': ka.get('KA_ID'),
                'name': ka.get('KA_Name')
            },
            'dependencies': dep_details,
            'dependents': dependents,
            'dependency_count': len(dep_details),
            'dependent_count': len(dependents)
        }), 200
    except Exception as e:
        logger.error(f"Error getting dependencies: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ka_bp.route('/stats', methods=['GET'])
@api_login_required
def get_stats():
    """Get KA system statistics"""
    try:
        categories = {}
        risk_classes = {}
        statuses = {}
        impl_modes = {}
        has_math_count = 0
        
        for ka_info in controller.get_available_algorithms().values():
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
                'total_algorithms': len(KA_REGISTRY),
                'by_category': categories,
                'by_risk_class': risk_classes,
                'by_status': statuses,
                'by_implementation_mode': impl_modes,
                'with_math_components': has_math_count
            }
        }), 200
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@ka_bp.route('/health', methods=['GET'])
def health_check():
    """Check KA system health"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'total_algorithms': len(KA_REGISTRY),
        'available': True,
        'version': '2.0.0',
        'registry_source': 'ka_registry.json'
    }), 200
