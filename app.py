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

# Initialize Sentry for error tracking (production only)
sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    
    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[
            FlaskIntegration(),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        profiles_sample_rate=float(os.environ.get("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
        environment=os.environ.get("FLASK_ENV", "production"),
        release=os.environ.get("APP_VERSION", "1.2.0"),
    )

# Configure logging - use INFO in production, DEBUG in development
log_level = logging.DEBUG if os.environ.get("FLASK_ENV") == "development" else logging.INFO
logging.basicConfig(level=log_level)
logger = logging.getLogger(__name__)

# Security: Warn about default credentials in production
def validate_production_security():
    """Validate that no default/insecure credentials are in use in production."""
    is_production = os.environ.get("FLASK_ENV") != "development"
    
    # Check for default admin credentials
    admin_user = os.environ.get("ADMIN_USERNAME", "")
    admin_pass = os.environ.get("ADMIN_PASSWORD", "")
    
    insecure_usernames = {"admin", "administrator", "root", "test", "user"}
    insecure_passwords = {"admin", "admin123", "password", "password123", "123456", "test", "root"}
    
    if is_production:
        issues = []
        if admin_user and admin_user.lower() in insecure_usernames:
            issues.append("Default admin username detected")
        if admin_pass and (admin_pass in insecure_passwords or len(admin_pass) < 12):
            issues.append("Insecure admin password (use min 12 chars)")
        if not os.environ.get("SESSION_SECRET"):
            issues.append("SESSION_SECRET not set")
        
        if issues:
            logger.error(f"SECURITY: Production security issues: {', '.join(issues)}")
            logger.error("SECURITY: Please fix these issues before deploying to production!")
    else:
        # Development warnings only
        if admin_user and admin_user.lower() in insecure_usernames:
            logger.warning("SECURITY WARNING: Using default admin username. Change before deployment!")
        if admin_pass and admin_pass in insecure_passwords:
            logger.warning("SECURITY WARNING: Using default admin password. Change before deployment!")

# Run security validation (non-blocking)
validate_production_security()

# Server configuration - bind to 5000 for Replit
DEFAULT_PORT = int(os.environ.get("PORT", 5000))

# Create Flask app
app = Flask(__name__)
# Security: Get secret key from environment (SESSION_SECRET as mandated)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Session hardening
app.config["SESSION_COOKIE_HTTPONLY"] = True
# In production, enforce Strict SameSite and Secure cookies
is_production = os.environ.get("FLASK_ENV") != "development"
app.config["SESSION_COOKIE_SAMESITE"] = os.environ.get("SESSION_COOKIE_SAMESITE", "Strict" if is_production else "Lax")
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("SESSION_COOKIE_SECURE", "True" if is_production else "False").lower() == "true"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(
    minutes=int(os.environ.get("SESSION_LIFETIME_MINUTES", 30))
)

# Configure database with production-ready connection pooling
database_url = os.environ.get("DATABASE_URL", "sqlite:///ukg_database.db")
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,  # Verify connections before use
    "pool_recycle": int(os.environ.get("DB_POOL_RECYCLE", 300)),  # Recycle every 5 min
    "pool_size": int(os.environ.get("DB_POOL_SIZE", 20)),  # Production pool size
    "max_overflow": int(os.environ.get("DB_MAX_OVERFLOW", 40)),  # Allow up to 60 total
    "pool_timeout": int(os.environ.get("DB_POOL_TIMEOUT", 30)),  # Connection timeout
}

# Rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[os.environ.get("GLOBAL_RATE_LIMIT", "200 per hour")],
    storage_uri=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"),
)

# Configure Caching and Celery
redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
# Check if Redis is likely available (naive check, real check happens on connect)
use_redis = "localhost" not in redis_url or os.environ.get("USE_REDIS", "False").lower() == "true"

if use_redis:
    app.config["CACHE_TYPE"] = "RedisCache"
    app.config["CACHE_REDIS_URL"] = redis_url
    app.config["CELERY_BROKER_URL"] = redis_url
    app.config["CELERY_RESULT_BACKEND"] = redis_url
else:
    # Fallback for development/tests without Redis
    app.config["CACHE_TYPE"] = "SimpleCache"
    app.config["CELERY_BROKER_URL"] = "memory://"
    app.config["CELERY_RESULT_BACKEND"] = "db+sqlite:///results.db" 
    app.config["CELERY_TASK_ALWAYS_EAGER"] = True # Run synchronously

# Initialize extensions with app
from extensions import db, login_manager, csrf, migrate, cache, compress
from models import User, APIKey, SimulationSession
db.init_app(app)
login_manager.init_app(app)
csrf.init_app(app)
migrate.init_app(app, db)
cache.init_app(app)
compress.init_app(app)

# Initialize Celery
from backend.celery_app import make_celery
celery = make_celery(app)

# Exempt JSON API endpoints from CSRF (they use session auth or API keys)
# CSRF is still enforced on all HTML form submissions
from flask_wtf.csrf import CSRFError

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    """Handle CSRF errors gracefully."""
    from flask import request
    if request.is_json or request.headers.get('Content-Type', '').startswith('application/json'):
        return jsonify({'error': 'CSRF token missing or invalid', 'success': False}), 400
    flash('Security token expired. Please try again.', 'danger')
    return redirect(request.url)

# Initialize security headers (Phase 1 security hardening)
from backend.security.security_headers import configure_security_headers
configure_security_headers(app, {'ENV': os.environ.get('FLASK_ENV', 'production')})

# Initialize request limits (Phase 1 security hardening)
from backend.middleware.request_limits import configure_request_limits
configure_request_limits(app, {
    'MAX_CONTENT_LENGTH': int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
})

# Initialize correlation ID middleware for request tracing
from backend.middleware.correlation_id import configure_correlation_id, setup_correlation_logging
configure_correlation_id(app)
setup_correlation_logging()

# Initialize Request Timeout
from backend.middleware.timeout import RequestTimeout
RequestTimeout(app)

# Initialize Audit Logging for API requests
from extensions import audit_logger

@app.after_request
def log_api_request(response):
    """Log API requests to audit log."""
    if request.path.startswith('/api/') and request.endpoint != 'api.api_health':
        user_id = str(current_user.id) if current_user.is_authenticated else None
        audit_logger.log_api_request(
            request_id=request.headers.get('X-Request-ID', ''),
            user_id=user_id,
            endpoint=request.path,
            method=request.method,
            status_code=response.status_code,
            ip_address=request.remote_addr
        )
    return response

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
app.register_blueprint(mcp_bp, url_prefix='/api/v1/mcp')
# Legacy alias
app.register_blueprint(mcp_bp, name='mcp_legacy', url_prefix='/api/mcp')
logger.info("MCP blueprint registered (v1 + legacy)")

# Register AI Chat blueprint
from backend.ai_chat import ai_chat_bp
app.register_blueprint(ai_chat_bp, url_prefix='/api/v1/chat')
# Legacy (note: chat bp might have hardcoded paths, double check if needed)
app.register_blueprint(ai_chat_bp, name='ai_chat_legacy', url_prefix='/api/chat')
logger.info("AI Chat blueprint registered (v1 + legacy)")

# Register Knowledge Algorithm API blueprint
from backend.ka_api import ka_bp
app.register_blueprint(ka_bp, url_prefix='/api/v1/ka')
app.register_blueprint(ka_bp, name='ka_legacy', url_prefix='/api/ka')
logger.info("KA API blueprint registered (v1 + legacy)")

# Register Truth Engine API blueprint (lazy initialization - components load on first use)
from backend.truth_engine.api import truth_api
app.register_blueprint(truth_api, url_prefix='/api/v1/truth')
app.register_blueprint(truth_api, name='truth_legacy', url_prefix='/api/truth')
logger.info("Truth Engine API blueprint registered (v1 + legacy)")

# Register Persona API blueprint
try:
    from backend.persona_api import persona_api
    app.register_blueprint(persona_api, url_prefix='/api/v1/persona')
    app.register_blueprint(persona_api, name='persona_legacy', url_prefix='/api/persona')
    logger.info("Persona API blueprint registered (v1 + legacy)")
except ImportError as e:
    logger.warning(f"Could not register Persona API blueprint: {e}")

# Register Pillar API blueprint
try:
    from backend.pillar_api import pillar_api
    app.register_blueprint(pillar_api, url_prefix='/api/v1/pillar')
    app.register_blueprint(pillar_api, name='pillar_legacy', url_prefix='/api/pillar')
    logger.info("Pillar API blueprint registered (v1 + legacy)")
except ImportError as e:
    logger.warning(f"Could not register Pillar API blueprint: {e}")

# Register Compliance API blueprint
try:
    from backend.compliance_api import compliance_api
    app.register_blueprint(compliance_api, url_prefix='/api/v1/compliance')
    app.register_blueprint(compliance_api, name='compliance_legacy', url_prefix='/api/compliance')
    logger.info("Compliance API blueprint registered (v1 + legacy)")
except ImportError as e:
    logger.warning(f"Could not register Compliance API blueprint: {e}")

# Register UKG API (defined in backend/ukg_api.py, prefix set in BP)
from backend.ukg_api import ukg_api
# ukg_api defines url_prefix='/api', so we need to override or re-register carefully
# Ideally, we change ukg_api definition, but here we can re-register with new prefix
app.register_blueprint(ukg_api, url_prefix='/api/v1') 
# Legacy '/api' is covered by original BP definition if imported/registered
# Check how it was imported before. It was via 'routes' maybe? 
# Wait, ukg_api was not explicitly registered in the previous file content I saw?
# Checking lines 258-260: 'from routes import register_routes; register_routes(app)'
# Need to check `routes/__init__.py` to see what it registers.
# But I see I missed `backend/ukg_api.py` registration in previous view of app.py?
# Ah, I see `app.register_blueprint(ukg_api)` was NOT in the previous `app.py`...
# Wait, let me check `app.py` again.
# I see `app.register_blueprint(mcp_bp)` etc.
# I DON'T see `app.register_blueprint(ukg_api)` in the original `app.py` provided.
# It seems `ukg_api` might be registered via `routes` package or I missed it.
# Let's check `routes/__init__.py` first to be safe.


# Register Replit Auth blueprint (optional - only if REPL_ID is set)
try:
    from replit_auth import make_replit_blueprint
    replit_bp = make_replit_blueprint()
    if replit_bp:
        app.register_blueprint(replit_bp, url_prefix="/auth")
        logger.info("Replit Auth blueprint registered")
    else:
        logger.info("Replit Auth disabled (REPL_ID not set)")
except ImportError as e:
    logger.warning(f"Could not register Replit Auth blueprint: {e}")

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

# Register core routes from routes package
from routes import register_routes
register_routes(app)

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
    """Create a new simulation with comprehensive input validation."""
    from backend.schemas.simulation_schemas import validate_simulation_creation

    # Prepare request data
    request_data = {
        'name': request.form.get('name'),
        'description': request.form.get('description', ''),
        'sim_type': request.form.get('sim_type'),
        'refinement_steps': request.form.get('refinement_steps', 12),
        'confidence_threshold': request.form.get('confidence_threshold', 0.85),
        'entropy_sampling': 'entropy_sampling' in request.form,
        'auto_start': 'auto_start' in request.form
    }

    # Validate input with schema
    validated_data, errors = validate_simulation_creation(request_data)
    if errors:
        for field, messages in errors.items():
            for message in messages if isinstance(messages, list) else [messages]:
                flash(f'{field}: {message}', 'error')
        return redirect(url_for('simulations'))

    # Extract validated data
    name = validated_data['name']
    description = validated_data.get('description', '')
    sim_type = validated_data['sim_type']
    refinement_steps = validated_data.get('refinement_steps', 12)
    confidence_threshold = validated_data.get('confidence_threshold', 0.85)
    entropy_sampling = validated_data.get('entropy_sampling', False)
    auto_start = validated_data.get('auto_start', False)
    
    # Create simulation parameters
    parameters = {
        'simulation_type': sim_type,
        'refinement_steps': refinement_steps,
        'confidence_threshold': confidence_threshold,
        'entropy_sampling': entropy_sampling
    }
    
    new_simulation = SimulationSession()
    new_simulation.session_id = str(uuid.uuid4())
    new_simulation.user_id = current_user.id
    new_simulation.name = name
    new_simulation.description = description
    new_simulation.parameters = parameters
    new_simulation.status = 'pending' if not auto_start else 'running'
    new_simulation.current_step = 0
    new_simulation.total_steps = 8
    new_simulation.created_at = datetime.now(UTC)
    new_simulation.started_at = datetime.now(UTC) if auto_start else None
    
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
        simulation.started_at = datetime.now(UTC)
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
    
    session_uid = simulation.session_id or f"sim_{sim_id}"
    sim_type = simulation.parameters.get('simulation_type', 'unknown') if simulation.parameters else 'unknown'
    
    export_data = {
        'id': simulation.id,
        'session_id': session_uid,
        'name': simulation.name,
        'description': simulation.description,
        'sim_type': sim_type,
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
        headers={'Content-Disposition': f'attachment;filename=simulation_{sim_id}_{session_uid}.json'}
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
    """Handle 404 Not Found errors."""
    # Log the error internally
    logger.warning(f"404 Not Found: {request.url}")

    if request.is_json or request.headers.get('Accept', '').startswith('application/json'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'The requested resource was not found'
            }
        }), 404
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 Internal Server errors without exposing stack traces."""
    # Log the full error internally (with stack trace)
    logger.error(f"500 Internal Server Error: {str(e)}", exc_info=True)

    # NEVER expose stack traces to users in production
    if request.is_json or request.headers.get('Accept', '').startswith('application/json'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_SERVER_ERROR',
                'message': 'An internal error occurred. Please try again later.'
            }
        }), 500
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden(e):
    """Handle 403 Forbidden errors."""
    logger.warning(f"403 Forbidden: {request.url} - User: {current_user.username if current_user and current_user.is_authenticated else 'Anonymous'}")

    if request.is_json or request.headers.get('Accept', '').startswith('application/json'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'You do not have permission to access this resource'
            }
        }), 403
    return render_template('errors/403.html'), 403

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded errors."""
    logger.warning(f"429 Rate Limit Exceeded: {request.url} - IP: {request.remote_addr}")

    if request.is_json or request.headers.get('Accept', '').startswith('application/json'):
        return jsonify({
            'success': False,
            'error': {
                'code': 'RATE_LIMIT_EXCEEDED',
                'message': 'Rate limit exceeded. Please try again later.',
                'retry_after': getattr(e, 'description', '60 seconds')
            }
        }), 429
    return render_template('errors/429.html'), 429

# Run the application
if __name__ == '__main__':
    # CRITICAL: Force debug=False in production, regardless of environment variable leaks
    is_prod = os.environ.get('FLASK_ENV') == 'production'
    if is_prod:
        debug_mode = False
    else:
        debug_mode = os.environ.get('FLASK_ENV') == 'development' or os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(host='0.0.0.0', port=DEFAULT_PORT, debug=debug_mode)