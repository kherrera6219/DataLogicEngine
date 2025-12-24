"""
Admin Routes Blueprint

Handles all admin-only routes with proper access control using @admin_required decorator.
"""

import datetime
from datetime import UTC
import logging

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from extensions import db
from models import User, SimulationSession
from db_models import Node, Edge, KnowledgeAlgorithm
from backend.decorators import admin_required

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('')
@login_required
@admin_required
def admin_dashboard():
    """Render the admin dashboard."""
    stats = {
        'user_count': User.query.count(),
        'active_users': User.query.filter_by(active=True).count(),
        'node_count': Node.query.count(),
        'edge_count': Edge.query.count(),
        'simulation_count': SimulationSession.query.count(),
        'algorithm_count': KnowledgeAlgorithm.query.count()
    }
    
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    recent_simulations = SimulationSession.query.order_by(
        SimulationSession.started_at.desc()
    ).limit(5).all()
    
    return render_template('admin/dashboard.html',
                          stats=stats,
                          recent_users=recent_users,
                          recent_simulations=recent_simulations)


@admin_bp.route('/users')
@login_required
@admin_required
def admin_users():
    """Render the user management page."""
    users = User.query.order_by(User.created_at.desc()).all()
    
    admin_count = User.query.filter((User.role == 'admin') | (User.is_admin == True)).count()
    analyst_count = User.query.filter_by(role='analyst').count()
    user_count = User.query.filter_by(role='user').count()
    viewer_count = User.query.filter_by(role='viewer').count()
    
    return render_template('admin/users.html',
                          users=users,
                          admin_count=admin_count,
                          user_count=user_count,
                          analyst_count=analyst_count,
                          viewer_count=viewer_count)


@admin_bp.route('/audit')
@login_required
@admin_required
def admin_audit():
    """Render the audit log page."""
    stats = {'info': 3, 'warning': 0, 'error': 0, 'critical': 0}
    type_counts = {'auth': 1, 'access': 1, 'data': 0, 'admin': 0, 'system': 1}
    
    return render_template('admin/audit_log.html',
                          logs=[],
                          stats=stats,
                          type_counts=type_counts,
                          now=datetime.datetime.now(UTC))


@admin_bp.route('/settings')
@login_required
@admin_required
def admin_settings():
    """Render the system settings page."""
    return render_template('admin/settings.html')
