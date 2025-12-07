"""
KA Management API

This module provides REST API endpoints for managing Knowledge Algorithms.
"""

import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

# Import KA Master Controller
from knowledge_algorithms.ka_master_controller import get_controller

logger = logging.getLogger(__name__)

# Create Blueprint
ka_management_bp = Blueprint('ka_management', __name__, url_prefix='/api/ka')


@ka_management_bp.route('/algorithms', methods=['GET'])
@login_required
def list_algorithms():
    """
    List all registered Knowledge Algorithms.

    Returns:
        200: List of algorithms
        500: Server error
    """
    try:
        controller = get_controller()
        algorithms = controller.get_available_algorithms()

        return jsonify({
            "success": True,
            "count": len(algorithms),
            "algorithms": algorithms
        }), 200

    except Exception as e:
        logger.error(f"Error listing algorithms: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to list algorithms"
        }), 500


@ka_management_bp.route('/algorithms/<ka_id>', methods=['GET'])
@login_required
def get_algorithm(ka_id):
    """
    Get details for a specific algorithm.

    Args:
        ka_id: Algorithm identifier

    Returns:
        200: Algorithm details
        404: Algorithm not found
        500: Server error
    """
    try:
        controller = get_controller()
        algorithms = controller.get_available_algorithms()

        if ka_id not in algorithms:
            return jsonify({
                "success": False,
                "error": f"Algorithm {ka_id} not found"
            }), 404

        algorithm = algorithms[ka_id]

        # Add version and dependencies
        version = controller.get_version(ka_id)
        dependencies = list(controller.get_dependencies(ka_id))

        return jsonify({
            "success": True,
            "algorithm": {
                **algorithm,
                "version": version,
                "dependencies": dependencies
            }
        }), 200

    except Exception as e:
        logger.error(f"Error getting algorithm {ka_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to get algorithm details"
        }), 500


@ka_management_bp.route('/execute', methods=['POST'])
@login_required
def execute_algorithm():
    """
    Execute a Knowledge Algorithm.

    Request Body:
        {
            "algorithm": "KA-01",
            "data": {...},
            "use_cache": true
        }

    Returns:
        200: Execution result
        400: Bad request
        500: Server error
    """
    try:
        request_data = request.get_json()

        if not request_data or 'algorithm' not in request_data:
            return jsonify({
                "success": False,
                "error": "Missing algorithm parameter"
            }), 400

        controller = get_controller()

        ka_id = request_data['algorithm']
        data = request_data.get('data', {})
        use_cache = request_data.get('use_cache', True)

        # Execute algorithm
        result = controller.execute_algorithm(ka_id, data, use_cache=use_cache)

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error executing algorithm: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to execute algorithm"
        }), 500


@ka_management_bp.route('/execute/sequence', methods=['POST'])
@login_required
def execute_sequence():
    """
    Execute a sequence of Knowledge Algorithms.

    Request Body:
        {
            "sequence": [
                {"algorithm": "KA-01", "parameters": {...}},
                {"algorithm": "KA-02", "parameters": {...}}
            ],
            "initial_data": {...},
            "return_all_results": false
        }

    Returns:
        200: Execution result(s)
        400: Bad request
        500: Server error
    """
    try:
        request_data = request.get_json()

        if not request_data or 'sequence' not in request_data:
            return jsonify({
                "success": False,
                "error": "Missing sequence parameter"
            }), 400

        controller = get_controller()

        sequence = request_data['sequence']
        initial_data = request_data.get('initial_data')
        return_all = request_data.get('return_all_results', False)

        # Execute sequence
        result = controller.execute_sequence(sequence, initial_data, return_all)

        return jsonify({
            "success": True,
            "result": result
        }), 200

    except Exception as e:
        logger.error(f"Error executing sequence: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to execute sequence"
        }), 500


@ka_management_bp.route('/metrics', methods=['GET'])
@login_required
def get_metrics():
    """
    Get KA Controller metrics.

    Returns:
        200: Metrics data
        500: Server error
    """
    try:
        controller = get_controller()
        metrics = controller.get_metrics()

        return jsonify({
            "success": True,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to get metrics"
        }), 500


@ka_management_bp.route('/cache', methods=['GET', 'DELETE'])
@login_required
def manage_cache():
    """
    Manage KA result cache.

    GET: Get cache status
    DELETE: Clear cache (optional ?algorithm=KA-ID parameter)

    Returns:
        200: Cache status or clear result
        500: Server error
    """
    try:
        controller = get_controller()

        if request.method == 'GET':
            # Get cache status
            return jsonify({
                "success": True,
                "enabled": controller.enable_caching,
                "ttl": controller.cache_ttl,
                "size": len(controller.cache),
                "hits": controller.cache_hits,
                "misses": controller.cache_misses,
                "hit_rate": controller.cache_hits / (controller.cache_hits + controller.cache_misses)
                    if (controller.cache_hits + controller.cache_misses) > 0 else 0
            }), 200

        elif request.method == 'DELETE':
            # Clear cache
            ka_id = request.args.get('algorithm')
            count = controller.clear_cache(ka_id)

            return jsonify({
                "success": True,
                "cleared": count,
                "algorithm": ka_id
            }), 200

    except Exception as e:
        logger.error(f"Error managing cache: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to manage cache"
        }), 500


@ka_management_bp.route('/algorithms/<ka_id>/dependencies', methods=['GET', 'POST'])
@login_required
def manage_dependencies(ka_id):
    """
    Manage algorithm dependencies.

    GET: Get dependencies for an algorithm
    POST: Add dependencies

    Request Body (POST):
        {
            "depends_on": ["KA-01", "KA-02"]
        }

    Returns:
        200: Dependencies
        400: Bad request
        404: Algorithm not found
        500: Server error
    """
    try:
        controller = get_controller()
        algorithms = controller.get_available_algorithms()

        if ka_id not in algorithms:
            return jsonify({
                "success": False,
                "error": f"Algorithm {ka_id} not found"
            }), 404

        if request.method == 'GET':
            # Get dependencies
            recursive = request.args.get('recursive', 'false').lower() == 'true'
            dependencies = list(controller.get_dependencies(ka_id, recursive))

            return jsonify({
                "success": True,
                "algorithm": ka_id,
                "dependencies": dependencies,
                "recursive": recursive
            }), 200

        elif request.method == 'POST':
            # Add dependencies
            request_data = request.get_json()

            if not request_data or 'depends_on' not in request_data:
                return jsonify({
                    "success": False,
                    "error": "Missing depends_on parameter"
                }), 400

            depends_on = request_data['depends_on']
            success = controller.add_dependency(ka_id, depends_on)

            if not success:
                return jsonify({
                    "success": False,
                    "error": "Failed to add dependencies"
                }), 500

            dependencies = list(controller.get_dependencies(ka_id))

            return jsonify({
                "success": True,
                "algorithm": ka_id,
                "dependencies": dependencies
            }), 200

    except Exception as e:
        logger.error(f"Error managing dependencies for {ka_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to manage dependencies"
        }), 500


@ka_management_bp.route('/resolve-dependencies', methods=['POST'])
@login_required
def resolve_dependencies():
    """
    Resolve execution order for a set of algorithms.

    Request Body:
        {
            "algorithms": ["KA-05", "KA-01", "KA-03"]
        }

    Returns:
        200: Execution order
        400: Bad request (e.g., circular dependency)
        500: Server error
    """
    try:
        request_data = request.get_json()

        if not request_data or 'algorithms' not in request_data:
            return jsonify({
                "success": False,
                "error": "Missing algorithms parameter"
            }), 400

        controller = get_controller()
        algorithms = request_data['algorithms']

        try:
            execution_order = controller.resolve_dependencies(algorithms)

            return jsonify({
                "success": True,
                "requested": algorithms,
                "execution_order": execution_order
            }), 200

        except ValueError as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 400

    except Exception as e:
        logger.error(f"Error resolving dependencies: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to resolve dependencies"
        }), 500


@ka_management_bp.route('/algorithms/<ka_id>/version', methods=['GET', 'PUT'])
@login_required
def manage_version(ka_id):
    """
    Manage algorithm version.

    GET: Get version
    PUT: Set version

    Request Body (PUT):
        {
            "version": "1.2.0"
        }

    Returns:
        200: Version info
        400: Bad request
        404: Algorithm not found
        500: Server error
    """
    try:
        controller = get_controller()
        algorithms = controller.get_available_algorithms()

        if ka_id not in algorithms:
            return jsonify({
                "success": False,
                "error": f"Algorithm {ka_id} not found"
            }), 404

        if request.method == 'GET':
            # Get version
            version = controller.get_version(ka_id)

            return jsonify({
                "success": True,
                "algorithm": ka_id,
                "version": version or "unknown"
            }), 200

        elif request.method == 'PUT':
            # Set version
            request_data = request.get_json()

            if not request_data or 'version' not in request_data:
                return jsonify({
                    "success": False,
                    "error": "Missing version parameter"
                }), 400

            version = request_data['version']
            success = controller.set_version(ka_id, version)

            if not success:
                return jsonify({
                    "success": False,
                    "error": "Failed to set version"
                }), 500

            return jsonify({
                "success": True,
                "algorithm": ka_id,
                "version": version
            }), 200

    except Exception as e:
        logger.error(f"Error managing version for {ka_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to manage version"
        }), 500


@ka_management_bp.route('/history', methods=['GET'])
@login_required
def get_history():
    """
    Get execution history.

    Query Parameters:
        limit: Maximum number of records to return

    Returns:
        200: Execution history
        500: Server error
    """
    try:
        controller = get_controller()
        limit = request.args.get('limit', type=int)

        history = controller.get_execution_history(limit)

        return jsonify({
            "success": True,
            "count": len(history),
            "history": history
        }), 200

    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to get execution history"
        }), 500


@ka_management_bp.route('/plan', methods=['POST'])
@login_required
def create_plan():
    """
    Create an execution plan for a task.

    Request Body:
        {
            "task": "Task description",
            "algorithms": ["KA-01", "KA-02"]  // optional
        }

    Returns:
        200: Execution plan
        400: Bad request
        500: Server error
    """
    try:
        request_data = request.get_json()

        if not request_data or 'task' not in request_data:
            return jsonify({
                "success": False,
                "error": "Missing task parameter"
            }), 400

        controller = get_controller()

        task = request_data['task']
        algorithms = request_data.get('algorithms')

        plan = controller.create_execution_plan(task, algorithms)

        return jsonify({
            "success": True,
            "task": task,
            "plan": plan,
            "step_count": len(plan)
        }), 200

    except Exception as e:
        logger.error(f"Error creating plan: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to create execution plan"
        }), 500
