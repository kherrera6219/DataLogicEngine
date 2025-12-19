"""
Routes Package

This module registers all route blueprints for the UKG application.
"""

import logging
from flask import render_template

from .auth_routes import auth_bp
from .page_routes import pages_bp
from .api_routes import api_bp
from .admin_routes import admin_bp

logger = logging.getLogger(__name__)


def register_routes(app):
    """Register all route blueprints with the Flask app."""
    
    app.register_blueprint(auth_bp)
    logger.info("Auth routes blueprint registered")
    
    app.register_blueprint(pages_bp)
    logger.info("Page routes blueprint registered")
    
    app.register_blueprint(api_bp)
    logger.info("API routes blueprint registered")
    
    app.register_blueprint(admin_bp)
    logger.info("Admin routes blueprint registered")
    
    _register_backward_compatible_endpoints(app)
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        from extensions import db
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    logger.info("All route blueprints registered successfully")


def _register_backward_compatible_endpoints(app):
    """
    Register backward-compatible endpoint aliases so existing templates
    can still use url_for('index') instead of url_for('pages.index').
    """
    from .page_routes import (
        index, dashboard, profile, knowledge, simulation, graph, chatbot,
        analytics, settings, llm_providers, truth_engine, algorithms,
        persona_trace, axis_explorer, simulation_monitor, mcp_server,
        mcp_client, api_overlay
    )
    from .auth_routes import login, logout, register
    from .admin_routes import admin_dashboard, admin_users, admin_audit, admin_settings
    from .api_routes import api_health, api_graph, api_query, api_run_simulation
    
    app.add_url_rule('/', 'index', index)
    app.add_url_rule('/dashboard', 'dashboard', dashboard)
    app.add_url_rule('/profile', 'profile', profile, methods=['GET', 'POST'])
    app.add_url_rule('/knowledge', 'knowledge', knowledge)
    app.add_url_rule('/simulation', 'simulation', simulation)
    app.add_url_rule('/graph', 'graph', graph)
    app.add_url_rule('/chatbot', 'chatbot', chatbot)
    app.add_url_rule('/analytics', 'analytics', analytics)
    app.add_url_rule('/settings', 'settings', settings)
    app.add_url_rule('/llm-providers', 'llm_providers', llm_providers)
    app.add_url_rule('/truth-engine', 'truth_engine', truth_engine)
    app.add_url_rule('/algorithms', 'algorithms', algorithms)
    app.add_url_rule('/persona-trace', 'persona_trace', persona_trace)
    app.add_url_rule('/axis-explorer', 'axis_explorer', axis_explorer)
    app.add_url_rule('/simulation-monitor', 'simulation_monitor', simulation_monitor)
    app.add_url_rule('/mcp-server', 'mcp_server', mcp_server)
    app.add_url_rule('/mcp-client', 'mcp_client', mcp_client)
    app.add_url_rule('/api-overlay', 'api_overlay', api_overlay)
    
    app.add_url_rule('/login', 'login', login, methods=['GET', 'POST'])
    app.add_url_rule('/logout', 'logout', logout)
    app.add_url_rule('/register', 'register', register, methods=['GET', 'POST'])
    
    app.add_url_rule('/admin', 'admin', admin_dashboard)
    app.add_url_rule('/admin/users', 'admin_users', admin_users)
    app.add_url_rule('/admin/audit', 'admin_audit', admin_audit)
    app.add_url_rule('/admin/settings', 'admin_settings', admin_settings)
    
    app.add_url_rule('/api/health', 'api_health', api_health)
    app.add_url_rule('/api/graph', 'api_graph', api_graph)
    app.add_url_rule('/api/query', 'api_query', api_query, methods=['POST'])
    app.add_url_rule('/api/simulation/run', 'api_run_simulation', api_run_simulation, methods=['POST'])
    
    logger.info("Backward-compatible endpoint aliases registered")
