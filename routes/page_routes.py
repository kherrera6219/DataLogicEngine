"""
Page Routes Blueprint

Handles all page rendering routes for authenticated and public pages.
"""

import datetime
from datetime import UTC
import logging
import secrets

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_login import current_user, login_required
import os

from extensions import db
from models import APIKey, User, SimulationSession
from models import Node, Edge, KnowledgeNode, KnowledgeAlgorithm, Sector, Domain, PillarLevel

logger = logging.getLogger(__name__)

pages_bp = Blueprint('pages', __name__)


@pages_bp.route('/')
def index():
    """Render the homepage."""
    return render_template('index.html')


@pages_bp.route('/favicon.ico')
def favicon():
    """Serve the favicon."""
    static_dir = os.path.join(pages_bp.root_path, '..', 'static')
    if os.path.exists(os.path.join(static_dir, 'favicon.ico')):
        return send_from_directory(static_dir, 'favicon.ico', mimetype='image/vnd.microsoft.icon')
    elif os.path.exists(os.path.join(static_dir, 'favicon.svg')):
        return send_from_directory(static_dir, 'favicon.svg', mimetype='image/svg+xml')
    return '', 204


@pages_bp.route('/dashboard')
@login_required
def dashboard():
    """Render the dashboard."""
    stats = {
        'knowledge_count': KnowledgeNode.query.count(),
        'sector_count': Sector.query.count(),
        'domain_count': Domain.query.count(),
        'simulation_count': SimulationSession.query.filter_by(user_id=current_user.id).count(),
        'algorithm_count': KnowledgeAlgorithm.query.count()
    }
    
    recent_simulations = SimulationSession.query.filter_by(
        user_id=current_user.id
    ).order_by(SimulationSession.started_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                          stats=stats, 
                          recent_simulations=recent_simulations)


@pages_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Render the user profile page and manage API keys."""
    new_api_key = None

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'create':
            label = request.form.get('label', 'New API Key').strip() or 'New API Key'
            new_api_key = APIKey(
                user_id=current_user.id,
                name=label,
                key=secrets.token_hex(32)
            )
            db.session.add(new_api_key)
            db.session.commit()
            session['generated_api_key'] = new_api_key.key
            session['generated_api_key_name'] = new_api_key.name
            flash('New API key created. Copy it now; it will only be shown once.', 'success')

        elif action == 'revoke':
            key_id = request.form.get('key_id', type=int)
            api_key = APIKey.query.filter_by(id=key_id, user_id=current_user.id, is_active=True).first()
            if api_key:
                api_key.is_active = False
                api_key.revoked_at = datetime.datetime.now(UTC)
                db.session.commit()
                flash('API key revoked successfully.', 'info')
            else:
                flash('API key not found or already revoked.', 'warning')

        return redirect(url_for('pages.profile'))

    new_api_key_value = session.pop('generated_api_key', None)
    new_api_key_name = session.pop('generated_api_key_name', None)
    api_keys = APIKey.query.filter_by(user_id=current_user.id).order_by(APIKey.created_at.desc()).all()

    simulation_count = SimulationSession.query.filter_by(user_id=current_user.id).count()
    completed_simulations = SimulationSession.query.filter_by(
        user_id=current_user.id,
        status='completed'
    ).count()

    return render_template(
        'profile.html',
        api_keys=api_keys,
        new_api_key=new_api_key_value,
        new_api_key_name=new_api_key_name,
        simulation_count=simulation_count,
        completed_simulations=completed_simulations,
    )


@pages_bp.route('/knowledge')
@login_required
def knowledge():
    """Render the knowledge page."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    knowledge_nodes = KnowledgeNode.query.order_by(
        KnowledgeNode.created_at.desc()
    ).paginate(page=page, per_page=per_page)
    
    pillars = PillarLevel.query.order_by(PillarLevel.pillar_id).all()
    sectors = Sector.query.order_by(Sector.sector_code).all()
    domains = Domain.query.order_by(Domain.domain_code).all()
    
    graph_nodes = Node.query.filter_by(node_type='axis').order_by(Node.axis_number).all()
    
    return render_template('knowledge.html', 
                           knowledge_nodes=knowledge_nodes,
                           pillars=pillars,
                           sectors=sectors,
                           domains=domains,
                           graph_nodes=graph_nodes)


@pages_bp.route('/simulation')
@login_required
def simulation():
    """Render the simulation page."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    simulations = SimulationSession.query.filter_by(
        user_id=current_user.id
    ).order_by(SimulationSession.started_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('simulation.html', simulations=simulations)


@pages_bp.route('/graph')
@login_required
def graph():
    """Render the graph visualization page."""
    return render_template('graph.html')


@pages_bp.route('/chatbot')
@login_required
def chatbot():
    """Render the chatbot interface."""
    return render_template('chatbot.html')


@pages_bp.route('/analytics')
@login_required
def analytics():
    """Render the analytics page."""
    user_count = User.query.count()
    node_count = Node.query.count()
    edge_count = Edge.query.count()
    simulation_count = SimulationSession.query.count()
    
    node_distribution = []
    for i in range(1, 14):
        count = Node.query.filter_by(axis_number=i).count()
        node_distribution.append({
            'axis': i,
            'count': count,
            'label': ['Knowledge', 'Sectors', 'Domains', 'Methods', 'Contexts', 
                     'Problems', 'Solutions', 'Roles', 'Experts', 'Regulations', 
                     'Compliance', 'Location', 'Time'][i-1]
        })
    
    simulation_statuses = {}
    status_rows = db.session.query(
        SimulationSession.status, 
        db.func.count(SimulationSession.id)
    ).group_by(SimulationSession.status).all()
    
    for status, count in status_rows:
        simulation_statuses[status] = count
    
    return render_template('analytics.html',
                          user_count=user_count,
                          node_count=node_count,
                          edge_count=edge_count,
                          simulation_count=simulation_count,
                          node_distribution=node_distribution,
                          simulation_statuses=simulation_statuses)


@pages_bp.route('/settings')
@login_required
def settings():
    """Render the settings page."""
    return render_template('settings.html')


@pages_bp.route('/llm-providers')
@login_required
def llm_providers():
    """Render the LLM provider configuration page."""
    import os
    
    providers = {
        'openai': bool(os.environ.get('OPENAI_API_KEY')),
        'azure': bool(os.environ.get('AZURE_OPENAI_API_KEY')),
        'anthropic': bool(os.environ.get('ANTHROPIC_API_KEY')),
        'google': bool(os.environ.get('GOOGLE_API_KEY')),
        'openai_model': os.environ.get('OPENAI_MODEL', 'gpt-4o'),
        'azure_endpoint': os.environ.get('AZURE_OPENAI_ENDPOINT', ''),
        'azure_deployment': os.environ.get('AZURE_OPENAI_DEPLOYMENT', ''),
        'anthropic_model': os.environ.get('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022'),
        'google_model': os.environ.get('GOOGLE_MODEL', 'gemini-1.5-pro'),
    }
    
    mcp_stats = {
        'active_connections': 0,
        'requests_today': 0
    }
    
    return render_template('llm_providers.html', providers=providers, mcp_stats=mcp_stats)


@pages_bp.route('/truth-engine')
@login_required
def truth_engine():
    """Render the Truth Engine monitor dashboard."""
    stats = {
        'truthcore': {
            'active_workflows': 0
        },
        'truthgate': {
            'requests_processed': 0
        },
        'truthmemory': {
            'cached_items': 0,
            'hash_entries': 0,
            'cache_hit_rate': '0%'
        },
        'truthlink': {
            'events_today': 0,
            'subscribers': 0,
            'dlq_items': 0
        },
        'tiers': {
            'tier1': 0,
            'tier2': 0,
            'tier3': 0,
            'tier4': 0,
            'tier5': 0
        }
    }
    
    try:
        from backend.truth_engine.api import get_truth_engine_status
        engine_status = get_truth_engine_status()
        if engine_status:
            if 'truthcore' in engine_status:
                stats['truthcore'].update(engine_status.get('truthcore', {}))
            if 'truthgate' in engine_status:
                stats['truthgate'].update(engine_status.get('truthgate', {}))
            if 'truthmemory' in engine_status:
                stats['truthmemory'].update(engine_status.get('truthmemory', {}))
            if 'truthlink' in engine_status:
                stats['truthlink'].update(engine_status.get('truthlink', {}))
    except Exception as e:
        logger.warning(f"Could not fetch Truth Engine stats: {e}")
    
    return render_template('truth_engine.html', stats=stats)


@pages_bp.route('/algorithms')
@login_required
def algorithms():
    """Render the Knowledge Algorithms browser page."""
    algorithms = KnowledgeAlgorithm.query.order_by(KnowledgeAlgorithm.algorithm_id).all()
    return render_template('algorithms.html', algorithms=algorithms)


@pages_bp.route('/persona-trace')
@login_required
def persona_trace():
    """Render the Quad Persona Tracing Dashboard."""
    sessions = []
    try:
        sessions = SimulationSession.query.filter_by(
            user_id=current_user.id
        ).order_by(SimulationSession.started_at.desc()).limit(10).all()
    except Exception as e:
        logger.warning(f"Could not fetch sessions for persona trace: {e}")
    
    return render_template('persona_trace.html', sessions=sessions)


@pages_bp.route('/axis-explorer')
@login_required
def axis_explorer():
    """Render the 17-Axis Coordinate Explorer."""
    return render_template('axis_explorer.html')


@pages_bp.route('/simulation-monitor')
@login_required
def simulation_monitor():
    """Render the 10-Layer Simulation Monitor."""
    return render_template('simulation_monitor.html')


@pages_bp.route('/mcp-server')
@login_required
def mcp_server():
    """Render the MCP Server Manager page."""
    return render_template('mcp_server.html')


@pages_bp.route('/mcp-client')
@login_required
def mcp_client():
    """Render the MCP Client Console page."""
    return render_template('mcp_client.html')


@pages_bp.route('/api-overlay')
@login_required
def api_overlay():
    """Render the API Overlay Dashboard."""
    return render_template('api_overlay.html')
