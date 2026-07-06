"""
Search API Routes for DataLogicEngine

Provides search endpoints for knowledge graph and algorithms.
"""

import logging
from flask import Blueprint, request, jsonify

from backend.auth.api_decorators import api_session_login_required
from backend.search_service import (
    search_knowledge_nodes,
    search_ukg_nodes,
    search_algorithms,
    global_search
)

logger = logging.getLogger(__name__)

search_api = Blueprint('search_api', __name__)


def _bounded_int_arg(name, default, *, minimum, maximum):
    raw_value = request.args.get(name)
    if raw_value in (None, ""):
        return default
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(value, maximum))


def _search_unavailable(message="Search is unavailable"):
    return jsonify({
        'success': False,
        'error': message,
    }), 500


@search_api.route('/nodes', methods=['GET'])
@api_session_login_required
def search_nodes():
    """
    Search knowledge graph nodes.
    
    Query Parameters:
        q: Search query (required)
        limit: Max results (default: 20)
        offset: Pagination offset (default: 0)
        type: Filter by node type
        axis: Filter by axis number
    
    Returns:
        JSON with search results
    """
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Search query is required'
        }), 400
    
    if len(query) < 2:
        return jsonify({
            'success': False,
            'error': 'Query must be at least 2 characters'
        }), 400
    
    try:
        limit = _bounded_int_arg('limit', 20, minimum=1, maximum=100)
        offset = _bounded_int_arg('offset', 0, minimum=0, maximum=100000)
        node_type = request.args.get('type')
        axis_number = request.args.get('axis', type=int)

        results = search_knowledge_nodes(
            query=query,
            limit=limit,
            offset=offset,
            node_type=node_type,
            axis_number=axis_number
        )

        return jsonify(results)
    except Exception:
        logger.exception("Search nodes failed")
        return _search_unavailable()


@search_api.route('/ukg', methods=['GET'])
@api_session_login_required
def search_ukg():
    """
    Search UKG nodes.
    
    Query Parameters:
        q: Search query (required)
        limit: Max results (default: 20)
        offset: Pagination offset (default: 0)
    """
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Search query is required'
        }), 400
    
    try:
        limit = _bounded_int_arg('limit', 20, minimum=1, maximum=100)
        offset = _bounded_int_arg('offset', 0, minimum=0, maximum=100000)

        results = search_ukg_nodes(query=query, limit=limit, offset=offset)
        return jsonify(results)
    except Exception:
        logger.exception("UKG search failed")
        return _search_unavailable()


@search_api.route('/algorithms', methods=['GET'])
@api_session_login_required
def search_ka():
    """
    Search knowledge algorithms.
    
    Query Parameters:
        q: Search query (required)
        limit: Max results (default: 20)
    """
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Search query is required'
        }), 400
    
    try:
        limit = _bounded_int_arg('limit', 20, minimum=1, maximum=50)

        results = search_algorithms(query=query, limit=limit)
        return jsonify(results)
    except Exception:
        logger.exception("Algorithm search failed")
        return _search_unavailable()


@search_api.route('/global', methods=['GET'])
@api_session_login_required
def search_global():
    """
    Global search across all entities.
    
    Query Parameters:
        q: Search query (required)
        limit: Max results per category (default: 10)
    """
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Search query is required'
        }), 400
    
    try:
        limit = _bounded_int_arg('limit', 10, minimum=1, maximum=20)

        results = global_search(query=query, limit=limit)
        return jsonify(results)
    except Exception:
        logger.exception("Global search failed")
        return _search_unavailable()


@search_api.route('/suggest', methods=['GET'])
@api_session_login_required
def search_suggest():
    """
    Get search suggestions (autocomplete).
    
    Query Parameters:
        q: Partial search query (required)
        limit: Max suggestions (default: 5)
    """
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify({'suggestions': []})
    
    try:
        # Return top matches as suggestions
        limit = _bounded_int_arg('limit', 5, minimum=1, maximum=10)

        results = search_knowledge_nodes(query=query, limit=limit)

        suggestions = [
            {'label': r['label'], 'type': r['node_type']}
            for r in results.get('results', [])
        ]

        return jsonify({'suggestions': suggestions})
    except Exception:
        logger.exception("Search suggestions failed")
        return jsonify({
            'suggestions': [],
            'error': 'Search suggestions are unavailable',
        }), 500
