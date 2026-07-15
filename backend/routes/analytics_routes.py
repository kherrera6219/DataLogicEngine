from flask import Blueprint, jsonify, request
from backend.auth.api_decorators import api_session_login_required
from backend.services.analytics_service import AnalyticsService

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/v1/analytics')

@analytics_bp.route('/overview', methods=['GET'])
@api_session_login_required
def get_overview():
    """
    Get high-level dashboard metrics from real data.
    """
    stats = AnalyticsService.get_dashboard_overview()
    if stats:
        return jsonify({
            'success': True,
            'data': stats
        })
    return jsonify({
        'success': False,
        'error': "Failed to fetch analytics"
    }), 500

@analytics_bp.route('/activity', methods=['GET'])
@api_session_login_required
def get_activity():
    """
    Get recent system activity.
    """
    limit = request.args.get('limit', 10, type=int)
    activity = AnalyticsService.get_recent_activity(limit=limit)
    if activity is None:
        return jsonify({
            'success': False,
            'error': 'Activity analytics are unavailable',
        }), 503
    return jsonify({
        'success': True,
        'data': activity
    })


@analytics_bp.route('/trends', methods=['GET'])
@api_session_login_required
def get_trends():
    """Get bounded daily activity trends from persisted records."""
    metric = request.args.get('metric', 'sessions')
    days = request.args.get('days', 7, type=int)
    return jsonify({
        'success': True,
        'data': AnalyticsService.get_trends(metric=metric, days=days),
    })

@analytics_bp.route('/mcp', methods=['GET'])
@api_session_login_required
def get_mcp_stats():
    """
    Get MCP-specific statistics.
    """
    stats = AnalyticsService.get_mcp_stats()
    if stats is None:
        return jsonify({
            'success': False,
            'error': 'MCP analytics are unavailable',
        }), 503
    return jsonify({
        'success': True,
        'data': stats
    })
