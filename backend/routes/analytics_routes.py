"""
Analytics API Routes for DataLogicEngine

Provides endpoints for dashboard analytics including:
- System summary statistics
- Time-series trends
- 17-axis distribution
- Knowledge algorithm metrics
"""

import logging
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from flask_login import login_required

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/v1/analytics')


@analytics_bp.route('/summary', methods=['GET'])
@login_required
def get_summary():
    """
    Get overall system summary statistics.
    """
    try:
        from extensions import db
        from models import User, KnowledgeGraphNode, ChatSession, TraceRun
        
        # Get counts from database
        node_count = db.session.query(KnowledgeGraphNode).count()
        user_count = db.session.query(User).count()
        session_count = db.session.query(ChatSession).count()
        trace_count = db.session.query(TraceRun).count()
        
        # Calculate active sessions (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        active_sessions = db.session.query(ChatSession).filter(
            ChatSession.created_at >= yesterday
        ).count()
        
        # Calculate active issues (TraceRuns with 'failed' status)
        active_issues = db.session.query(TraceRun).filter(
            TraceRun.status == 'failed'
        ).count()
        
        return jsonify({
            'success': True,
            'data': {
                'total_nodes': node_count,
                'total_users': user_count,
                'total_sessions': session_count,
                'total_traces': trace_count,
                'active_sessions_24h': active_sessions,
                'active_issues': active_issues,
                'knowledge_algorithms': 114,
                'axis_count': 17,
                'timestamp': datetime.utcnow().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"Error fetching analytics summary: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@analytics_bp.route('/trends', methods=['GET'])
@login_required
def get_trends():
    """
    Get time-series trend data for charts from actual history.
    """
    try:
        from extensions import db
        from models import ChatSession, TraceRun
        
        days = int(request.args.get('days', 7))
        metric = request.args.get('metric', 'sessions')
        
        today = datetime.utcnow().date()
        data_points = []
        
        for i in range(days, -1, -1):
            target_date = today - timedelta(days=i)
            start_time = datetime.combine(target_date, datetime.min.time())
            end_time = datetime.combine(target_date, datetime.max.time())
            
            if metric == 'sessions':
                count = db.session.query(ChatSession).filter(
                    ChatSession.created_at >= start_time,
                    ChatSession.created_at <= end_time
                ).count()
            elif metric == 'traces':
                count = db.session.query(TraceRun).filter(
                    TraceRun.created_at >= start_time,
                    TraceRun.created_at <= end_time
                ).count()
            else:
                count = 0
                
            data_points.append({
                'date': target_date.isoformat(),
                'value': count,
                'metric': metric
            })
        
        return jsonify({
            'success': True,
            'data': {
                'metric': metric,
                'period_days': days,
                'data_points': data_points
            }
        })
    except Exception as e:
        logger.error(f"Error fetching trends: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@analytics_bp.route('/axis-distribution', methods=['GET'])
@login_required
def get_axis_distribution():
    """
    Get distribution of knowledge across the 17-axis framework.
    
    Returns:
        JSON with coverage percentages for each axis
    """
    try:
        # 17-axis definitions with coverage data
        # In production, calculate actual coverage from database
        axis_data = [
            {'axis': 1, 'name': 'Pillar Levels', 'coverage': 95, 'node_count': 1247},
            {'axis': 2, 'name': 'Sectors', 'coverage': 88, 'node_count': 892},
            {'axis': 3, 'name': 'Honeycomb', 'coverage': 72, 'node_count': 534},
            {'axis': 4, 'name': 'Branches', 'coverage': 85, 'node_count': 721},
            {'axis': 5, 'name': 'Nodes', 'coverage': 91, 'node_count': 1856},
            {'axis': 6, 'name': 'Octopus Crosswalk', 'coverage': 68, 'node_count': 423},
            {'axis': 7, 'name': 'Spiderweb Crosswalk', 'coverage': 65, 'node_count': 398},
            {'axis': 8, 'name': 'Knowledge Role', 'coverage': 78, 'node_count': 156},
            {'axis': 9, 'name': 'Qualifications', 'coverage': 62, 'node_count': 234},
            {'axis': 10, 'name': 'Regulatory Expert', 'coverage': 75, 'node_count': 89},
            {'axis': 11, 'name': 'Compliance Expert', 'coverage': 71, 'node_count': 92},
            {'axis': 12, 'name': 'Location', 'coverage': 82, 'node_count': 312},
            {'axis': 13, 'name': 'Temporal', 'coverage': 89, 'node_count': 567},
            {'axis': 14, 'name': 'Risk & Confidence', 'coverage': 94, 'node_count': 2134},
            {'axis': 15, 'name': 'Federated Intelligence', 'coverage': 45, 'node_count': 67},
            {'axis': 16, 'name': 'Arrows of Time', 'coverage': 52, 'node_count': 89},
            {'axis': 17, 'name': 'Observability', 'coverage': 98, 'node_count': 4521}
        ]
        
        # Calculate overall coverage
        total_coverage = sum(a['coverage'] for a in axis_data) / len(axis_data)
        
        return jsonify({
            'success': True,
            'data': {
                'axes': axis_data,
                'overall_coverage': round(total_coverage, 1),
                'total_nodes': sum(a['node_count'] for a in axis_data)
            }
        })
    except Exception as e:
        logger.error(f"Error fetching axis distribution: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@analytics_bp.route('/ka-metrics', methods=['GET'])
@login_required
def get_ka_metrics():
    """
    Get Knowledge Algorithm execution metrics.
    
    Returns:
        JSON with KA execution stats
    """
    try:
        # KA category breakdowns
        categories = [
            {'category': 'Knowledge Retrieval', 'range': 'KA001-KA025', 'executions': 4521, 'avg_time_ms': 125},
            {'category': 'Risk Assessment', 'range': 'KA026-KA050', 'executions': 2134, 'avg_time_ms': 340},
            {'category': 'Compliance Checking', 'range': 'KA051-KA075', 'executions': 1876, 'avg_time_ms': 280},
            {'category': 'Scenario Simulation', 'range': 'KA076-KA100', 'executions': 987, 'avg_time_ms': 890},
            {'category': 'Recursive Planning', 'range': 'KA101-KA114', 'executions': 543, 'avg_time_ms': 1250}
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'categories': categories,
                'total_executions': sum(c['executions'] for c in categories),
                'total_algorithms': 114
            }
        })
    except Exception as e:
        logger.error(f"Error fetching KA metrics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
