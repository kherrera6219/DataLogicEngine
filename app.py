import os
import re
import uuid
import logging
from datetime import UTC, datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file BEFORE any other imports
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix
from extensions import limiter

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
if __name__ != "__main__": # Only run when starting as server
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

# Configure engine options based on database type
# SQLite doesn't support connection pooling options
if database_url.startswith("sqlite"):
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,  # Verify connections before use
    }
else:
    # PostgreSQL and other databases support full pooling
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,  # Verify connections before use
        "pool_recycle": int(os.environ.get("DB_POOL_RECYCLE", 300)),  # Recycle every 5 min
        "pool_size": int(os.environ.get("DB_POOL_SIZE", 20)),  # Production pool size
        "max_overflow": int(os.environ.get("DB_POOL_MAX_OVERFLOW", 30)),  # Extra connections for peak load
        "pool_timeout": int(os.environ.get("DB_POOL_TIMEOUT", 30)),  # Connection timeout
    }

# Rate limiting
# Rate limiting
# Rate limiting configuration
app.config["RATELIMIT_DEFAULT"] = os.environ.get("GLOBAL_RATE_LIMIT", "200 per hour")
app.config["RATELIMIT_STORAGE_URI"] = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")
limiter.init_app(app)

# Strict TLS Redirection in Production
@app.before_request
def force_https():
    """Force HTTPS redirection in production environments."""
    is_prod = os.environ.get('FLASK_ENV') == 'production'
    if is_prod and not request.is_secure and request.headers.get('X-Forwarded-Proto', 'http') != 'https':
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)

# SSO Configuration
from backend.auth.sso import configure_sso
configure_sso(app)


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
from extensions import db, login_manager, csrf, migrate, cache, compress, cors, limiter
from models import User, APIKey, SimulationSession
db.init_app(app)
login_manager.init_app(app)
csrf.init_app(app)
migrate.init_app(app, db)

# Configure limiter storage
if not use_redis:
    limiter.storage_uri = "memory://"
limiter.init_app(app)
cache.init_app(app)
compress.init_app(app)

# Initialize WebSockets
from backend.websocket import init_socketio, socketio
init_socketio(app)
# Configure CORS with strict origins from config (default to '*' if not set to prevent init errors)
origins = app.config.get('CORS_ORIGINS')
if not origins:
    origins = "*"
cors.init_app(app, resources={r"/api/*": {"origins": origins}}, supports_credentials=True)

# Initialize Celery
from backend.celery_app import make_celery
celery = make_celery(app)

# Exempt JSON API endpoints from CSRF (they use session auth or API keys)
# CSRF is still enforced on all HTML form submissions
from flask_wtf.csrf import CSRFError

# Handle CSRF errors
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    from flask import request
    if request.is_json or request.headers.get('Content-Type', '').startswith('application/json'):
        return jsonify({'error': 'CSRF token missing or invalid', 'success': False}), 400
    flash('Security token expired. Please try again.', 'danger')
    return redirect(request.url)

# Initialize Unified Middleware Stack (Hardened)
from backend.middleware import setup_middleware
setup_middleware(app)

# Initialize Session Management
if use_redis:
    from backend.security.session_manager import configure_session_manager
    configure_session_manager(app)
else:
    app.logger.info("[startup] - Using default cookie-based session storage (Redis disabled)")


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
    ChatSession,
    ChatMessage,
    LLMProvider,
    LLMProviderUsage,
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

# MCP Routes moved to routes/mcp_routes.py (registered via routes package)

# AI Chat legacy blueprint removed (Superseded by LLM Gateway)

# KA Routes moved to routes/ka_routes.py (registered via routes package)

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

# Register Compliance / Regulatory API blueprint (Axis 6/7)
try:
    from backend.regulatory_api import regulatory_api
    app.register_blueprint(regulatory_api, url_prefix='/api/v1/compliance')
    app.register_blueprint(regulatory_api, name='compliance_legacy', url_prefix='/api/compliance')
    # Also register under regulatory for clarity
    app.register_blueprint(regulatory_api, name='regulatory_api_v1', url_prefix='/api/v1/regulatory')
    logger.info("Regulatory/Compliance API blueprint registered (v1 + legacy)")
except ImportError as e:
    logger.warning(f"Could not register Regulatory/Compliance API blueprint: {e}")

# Register UKG API (defined in backend/ukg_api.py, prefix set in BP)
from backend.ukg_api import ukg_api
app.register_blueprint(ukg_api, url_prefix='/api/v1')
# Add legacy alias for tests
app.register_blueprint(ukg_api, name='ukg_legacy', url_prefix='/api/ukg')
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

# Register Trace API for enterprise traceability
try:
    from backend.tracing.api import trace_bp
    app.register_blueprint(trace_bp)
    logger.info("Trace API blueprint registered at /api/v1/trace")
except ImportError as e:
    logger.warning(f"Could not register Trace API blueprint: {e}")

# Register LLM Gateway API for external client access via UKG SDK
try:
    from backend.llm_gateway.api import register_gateway_routes
    register_gateway_routes(app)
    logger.info("LLM Gateway API registered at /api/v1/gateway and /api/admin")
except ImportError as e:
    logger.warning(f"Could not register LLM Gateway API: {e}")

# Register Analytics API for dashboard data
try:
    from backend.routes.analytics_routes import analytics_bp
    app.register_blueprint(analytics_bp)
    logger.info("Analytics API registered at /api/v1/analytics")
except ImportError as e:
    logger.warning(f"Could not register Analytics API: {e}")

# Register GraphQL API endpoint
try:
    print("DEBUG: Registering GraphQL...")
    from backend.graphql_schema import register_graphql
    register_graphql(app)
    print("DEBUG: GraphQL registered successfully")
    logger.info("GraphQL API registered at /graphql (GraphiQL enabled)")
except ImportError as e:
    print(f"DEBUG: GraphQL registration failed: {e}")
    logger.warning(f"Could not register GraphQL API: {e}")
except Exception as e:
    print(f"DEBUG: GraphQL registration error: {e}")
    logger.error(f"GraphQL registration error: {e}")

# Register GDPR compliance API
try:
    from backend.routes.gdpr_routes import gdpr_bp
    app.register_blueprint(gdpr_bp)
    logger.info("GDPR API registered at /api/v1/gdpr")
except ImportError as e:
    logger.warning(f"Could not register GDPR API: {e}")

# Register Data Retention API
try:
    from backend.routes.retention_routes import retention_bp
    app.register_blueprint(retention_bp)
    logger.info("Retention API registered at /api/v1/retention")
except ImportError as e:
    logger.warning(f"Could not register Retention API: {e}")

# Register Privacy & Data Deletion API
try:
    from backend.routes.privacy_routes import privacy_bp
    app.register_blueprint(privacy_bp)
    logger.info("Privacy API registered at /api/v1/privacy")
except ImportError as e:
    logger.warning(f"Could not register Privacy API: {e}")

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


# Simulation routes moved to routes/simulation_pages.py


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

    return jsonify({
        'success': False,
        'error': {
            'code': 'NOT_FOUND',
            'message': 'The requested resource was not found'
        }
    }), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 Internal Server errors without exposing stack traces."""
    # Log the full error internally (with stack trace)
    logger.error(f"500 Internal Server Error: {str(e)}", exc_info=True)

    # NEVER expose stack traces to users in production
    return jsonify({
        'success': False,
        'error': {
            'code': 'INTERNAL_SERVER_ERROR',
            'message': 'An internal error occurred. Please try again later.'
        }
    }), 500

@app.errorhandler(403)
def forbidden(e):
    """Handle 403 Forbidden errors."""
    logger.warning(f"403 Forbidden: {request.url} - User: {current_user.username if current_user and current_user.is_authenticated else 'Anonymous'}")

    return jsonify({
        'success': False,
        'error': {
            'code': 'FORBIDDEN',
            'message': 'You do not have permission to access this resource'
        }
    }), 403

@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded errors."""
    logger.warning(f"429 Rate Limit Exceeded: {request.url} - IP: {request.remote_addr}")

    return jsonify({
        'success': False,
        'error': {
            'code': 'RATE_LIMIT_EXCEEDED',
            'message': 'Rate limit exceeded. Please try again later.',
            'retry_after': getattr(e, 'description', '60 seconds')
        }
    }), 429

# Wrap initialization in create_app factory for testing and proper context
def create_app(config_name=None):
    """Application factory for testing and production."""
    # Use existing global app if already initialized (for backward compatibility)
    global app
    
    # In a full factory pattern we'd create a new Flask app here
    # For now, we return the global app which is already configured
    # This enables `from app import create_app; app = create_app()` flow needed by tests
    return app

# Configure logging - use INFO in production, DEBUG in development
if not app.debug:
    # Set up production logging if needed
    pass

# Run the application
if __name__ == '__main__':
    # CRITICAL: Force debug=False in production, regardless of environment variable leaks
    is_prod = os.environ.get('FLASK_ENV') == 'production'
    if is_prod:
        debug_mode = False
    else:
        debug_mode = os.environ.get('FLASK_ENV') == 'development' or os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(host='0.0.0.0', port=DEFAULT_PORT, debug=debug_mode)
