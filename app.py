import os
import re
import uuid
import logging
from datetime import UTC, datetime, timedelta
from dotenv import load_dotenv

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix

# Load environment variables from .env file
load_dotenv()

# Configure logging - use INFO in production, DEBUG in development
log_level = logging.DEBUG if os.environ.get("FLASK_ENV") == "development" else logging.INFO
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

# Server configuration
DEFAULT_PORT = int(os.environ.get("PORT", os.environ.get("BACKEND_PORT", 8080)))

# Create Flask app
app = Flask(__name__)
# Security: Get secret key from environment (SESSION_SECRET as mandated)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Session hardening
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = os.environ.get("SESSION_COOKIE_SAMESITE", "Lax")
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("SESSION_COOKIE_SECURE", "False").lower() == "true"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(
    minutes=int(os.environ.get("SESSION_LIFETIME_MINUTES", 30))
)

# Configure database
database_url = os.environ.get("DATABASE_URL", "sqlite:///ukg_database.db")
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

# Rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[os.environ.get("GLOBAL_RATE_LIMIT", "200 per hour")],
    storage_uri=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"),
)

# Initialize extensions with app
from extensions import db, login_manager
db.init_app(app)
login_manager.init_app(app)

# Initialize security headers (Phase 1 security hardening)
from backend.security.security_headers import configure_security_headers
configure_security_headers(app, {'ENV': os.environ.get('FLASK_ENV', 'production')})

# Initialize request limits (Phase 1 security hardening)
from backend.middleware.request_limits import configure_request_limits
configure_request_limits(app, {
    'MAX_CONTENT_LENGTH': int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
})

# Import models (after extensions initialization)
# Note: Importing models ensures SQLAlchemy creates their tables during db.create_all()
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from models import (
    User,
    SimulationSession,
    KnowledgeGraphNode,
    KnowledgeGraphEdge,
    MCPServer,
    MCPResource,
    MCPTool,
    MCPPrompt,
    PasswordHistory,
)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def password_meets_policy(password: str) -> bool:
    """Enforce a basic password policy for initial hardening."""
    if not password or len(password) < 12:
        return False
    has_upper = re.search(r"[A-Z]", password)
    has_lower = re.search(r"[a-z]", password)
    has_digit = re.search(r"\d", password)
    has_symbol = re.search(r"[^A-Za-z0-9]", password)
    return all([has_upper, has_lower, has_digit, has_symbol])

# Create tables
with app.app_context():
    db.create_all()
    logger.info("Database tables created")

# Register MCP blueprint
from backend.mcp_api import mcp_bp
app.register_blueprint(mcp_bp)
logger.info("MCP blueprint registered")

# Register AI Chat blueprint
from backend.ai_chat import ai_chat_bp
app.register_blueprint(ai_chat_bp)
logger.info("AI Chat blueprint registered")

# Register Knowledge Algorithm API blueprint
from backend.ka_api import ka_bp
app.register_blueprint(ka_bp)
logger.info("KA API blueprint registered")

# Register Truth Engine API blueprint
from backend.truth_engine.api import truth_api, init_truth_engine
app.register_blueprint(truth_api)
with app.app_context():
    init_truth_engine(db.session)
logger.info("Truth Engine API blueprint registered")

# Register Persona API blueprint
try:
    from backend.persona_api import persona_api
    app.register_blueprint(persona_api)
    logger.info("Persona API blueprint registered")
except ImportError as e:
    logger.warning(f"Could not register Persona API blueprint: {e}")

# Register Pillar API blueprint
try:
    from backend.pillar_api import pillar_api
    app.register_blueprint(pillar_api)
    logger.info("Pillar API blueprint registered")
except ImportError as e:
    logger.warning(f"Could not register Pillar API blueprint: {e}")

# Register Compliance API blueprint
try:
    from backend.compliance_api import compliance_api
    app.register_blueprint(compliance_api)
    logger.info("Compliance API blueprint registered")
except ImportError as e:
    logger.warning(f"Could not register Compliance API blueprint: {e}")

# Register Swagger UI for API documentation
from flask_swagger_ui import get_swaggerui_blueprint
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "Universal Knowledge Graph API"}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
logger.info("Swagger UI registered at /api/docs")

# Note: Core routes (/, /login, /register, /logout, /dashboard, /profile, /settings, 
# /knowledge, /simulation, /graph, /chatbot, /analytics, /admin) are defined in routes.py
# to avoid duplicate route definitions.

def _config_health() -> dict:
    """Summarize configuration readiness for lightweight health checks."""

    secret_key_status = "set" if app.secret_key else "missing"
    environment = os.environ.get("FLASK_ENV", "production")
    return {
        "environment": environment,
        "secret_key": secret_key_status,
    }


def _database_health() -> dict:
    """Confirm database connectivity with a trivial query."""

    try:
        with db.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        db.session.rollback()
        logger.error("Database connectivity check failed", exc_info=exc)
        return {"status": "error", "detail": str(exc)}

    return {"status": "ok"}


@app.route("/health", methods=["GET"])
def health() -> tuple:
    """Lightweight health endpoint for runtime monitoring."""

    config_state = _config_health()
    database_state = _database_health()

    overall_status = "ok"
    http_status = 200

    if database_state.get("status") != "ok":
        overall_status = "error"
        http_status = 503
    elif config_state.get("secret_key") == "missing":
        overall_status = "degraded"

    payload = {
        "status": overall_status,
        "config": config_state,
        "database": database_state,
        "timestamp": datetime.now(UTC).isoformat(),
    }

    return jsonify(payload), http_status

# Note: /login, /register, /logout, /dashboard are defined in routes.py with more complete implementations

@app.route('/simulations')
@login_required
def simulations():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    per_page = min(per_page, 50)  # Cap at 50 items per page
    
    pagination = SimulationSession.query.filter_by(user_id=current_user.id)\
        .order_by(SimulationSession.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('simulations.html', 
                           simulations=pagination.items,
                           pagination=pagination)

@app.route('/create_simulation', methods=['POST'])
@limiter.limit("30 per minute")
@login_required
def create_simulation():
    # Get simulation parameters from form
    name = request.form.get('name')
    description = request.form.get('description', '')
    sim_type = request.form.get('sim_type')
    refinement_steps = int(request.form.get('refinement_steps', 12))
    confidence_threshold = float(request.form.get('confidence_threshold', 0.85))
    entropy_sampling = 'entropy_sampling' in request.form
    auto_start = 'auto_start' in request.form
    
    # Validate input
    if not name or not sim_type:
        flash('Simulation name and type are required', 'error')
        return redirect(url_for('simulations'))
    
    # Create simulation parameters
    parameters = {
        'simulation_type': sim_type,
        'refinement_steps': refinement_steps,
        'confidence_threshold': confidence_threshold,
        'entropy_sampling': entropy_sampling
    }
    
    # Create new simulation session
    new_simulation = SimulationSession(
        session_id=str(uuid.uuid4()),
        user_id=current_user.id,
        name=name,
        description=description,
        parameters=parameters,
        status='pending' if not auto_start else 'running',
        current_step=0,
        total_steps=8,
        created_at=datetime.utcnow(),
        started_at=datetime.utcnow() if auto_start else None
    )
    
    try:
        db.session.add(new_simulation)
        db.session.commit()
        
        if auto_start:
            flash(f'Simulation "{name}" created and started successfully', 'success')
        else:
            flash(f'Simulation "{name}" created successfully', 'success')
        
        return redirect(url_for('simulations'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating simulation: {e}")
        flash('An error occurred while creating the simulation', 'error')
        return redirect(url_for('simulations'))

@app.route('/simulation/<int:sim_id>/start', methods=['POST'])
@limiter.limit("30 per minute")
@login_required
def start_simulation(sim_id):
    """Start a pending simulation"""
    simulation = SimulationSession.query.filter_by(id=sim_id, user_id=current_user.id).first_or_404()
    
    if simulation.status != 'pending':
        flash('Only pending simulations can be started', 'error')
        return redirect(url_for('simulations'))
    
    try:
        simulation.status = 'running'
        simulation.started_at = datetime.utcnow()
        db.session.commit()
        
        flash(f'Simulation "{simulation.name}" started successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error starting simulation: {e}")
        flash('An error occurred while starting the simulation', 'error')
    
    return redirect(url_for('simulations'))

@app.route('/simulation/<int:sim_id>/pause', methods=['POST'])
@limiter.limit("30 per minute")
@login_required
def pause_simulation(sim_id):
    """Pause a running simulation"""
    simulation = SimulationSession.query.filter_by(id=sim_id, user_id=current_user.id).first_or_404()
    
    if simulation.status != 'running':
        flash('Only running simulations can be paused', 'error')
        return redirect(url_for('simulations'))
    
    try:
        simulation.status = 'paused'
        db.session.commit()
        
        flash(f'Simulation "{simulation.name}" paused successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error pausing simulation: {e}")
        flash('An error occurred while pausing the simulation', 'error')
    
    return redirect(url_for('simulations'))

@app.route('/simulation/<int:sim_id>/resume', methods=['POST'])
@limiter.limit("30 per minute")
@login_required
def resume_simulation(sim_id):
    """Resume a paused simulation"""
    simulation = SimulationSession.query.filter_by(id=sim_id, user_id=current_user.id).first_or_404()
    
    if simulation.status != 'paused':
        flash('Only paused simulations can be resumed', 'error')
        return redirect(url_for('simulations'))
    
    try:
        simulation.status = 'running'
        db.session.commit()
        
        flash(f'Simulation "{simulation.name}" resumed successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error resuming simulation: {e}")
        flash('An error occurred while resuming the simulation', 'error')
    
    return redirect(url_for('simulations'))

@app.route('/simulation/<int:sim_id>/delete', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
def delete_simulation(sim_id):
    """Delete a simulation"""
    simulation = SimulationSession.query.filter_by(id=sim_id, user_id=current_user.id).first_or_404()
    
    try:
        db.session.delete(simulation)
        db.session.commit()
        
        flash(f'Simulation "{simulation.name}" deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting simulation: {e}")
        flash('An error occurred while deleting the simulation', 'error')
    
    return redirect(url_for('simulations'))

@app.route('/simulation/<int:sim_id>')
@login_required
def view_simulation(sim_id):
    """View simulation details"""
    simulation = SimulationSession.query.filter_by(id=sim_id, user_id=current_user.id).first_or_404()
    return render_template('simulation_details.html', simulation=simulation)

@app.route('/simulation/<int:sim_id>/results')
@login_required
def simulation_results(sim_id):
    """View simulation results"""
    simulation = SimulationSession.query.filter_by(id=sim_id, user_id=current_user.id).first_or_404()
    
    if simulation.status != 'completed':
        flash('Results are only available for completed simulations', 'warning')
        return redirect(url_for('view_simulation', sim_id=sim_id))
    
    return render_template('simulation_results.html', simulation=simulation)

@app.route('/simulation/<int:sim_id>/export')
@limiter.limit("10 per minute")
@login_required
def export_simulation(sim_id):
    """Export simulation data as JSON"""
    import json
    from flask import Response
    
    simulation = SimulationSession.query.filter_by(id=sim_id, user_id=current_user.id).first_or_404()
    
    uid = simulation.uid or f"sim_{sim_id}"
    
    export_data = {
        'id': simulation.id,
        'uid': uid,
        'name': simulation.name,
        'description': simulation.description,
        'sim_type': simulation.sim_type,
        'status': simulation.status,
        'created_at': simulation.created_at.isoformat() if simulation.created_at else None,
        'started_at': simulation.started_at.isoformat() if simulation.started_at else None,
        'completed_at': simulation.completed_at.isoformat() if simulation.completed_at else None,
        'current_step': simulation.current_step,
        'total_steps': simulation.total_steps,
        'parameters': simulation.parameters,
        'results': simulation.results,
        'exported_at': datetime.now(UTC).isoformat(),
        'exported_by': current_user.username
    }
    
    response = Response(
        json.dumps(export_data, indent=2),
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment;filename=simulation_{sim_id}_{uid}.json'}
    )
    return response

@app.route('/chat')
@login_required
def chat():
    return render_template('chat.html')

@app.route('/knowledge-graph')
@login_required
def knowledge_graph():
    return render_template('knowledge_graph.html')

@app.route('/api-docs')
def api_docs():
    return render_template('api_docs.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

# Note: /profile and /settings are defined in routes.py with more complete implementations

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500

# Run the application
if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_ENV') == 'development' or os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=DEFAULT_PORT, debug=debug_mode)