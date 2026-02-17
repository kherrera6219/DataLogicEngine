# ruff: noqa: E402
import os
import re
import json
import logging
import time
from threading import Lock
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables from .env file BEFORE any other imports
load_dotenv()

from flask import Flask, render_template, request, redirect, flash, jsonify, current_app, Response
from flask_login import login_required, current_user
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.exceptions import HTTPException
from extensions import limiter
from backend.llm_gateway.latency_metrics import ai_latency_metrics_prometheus_lines
from backend.logging_config import configure_structured_logging
from backend.mcp_server.connector_metrics import connector_metrics_prometheus_lines
from backend.observability.crash_reporting import (
    capture_exception_with_fallback,
    crash_reporting_prometheus_lines,
    initialize_crash_reporting,
)
from backend.observability.latency_slo import latency_slo_prometheus_lines
from backend.security.secret_resolver import (
    is_secure_secret_source,
    resolve_runtime_secret,
)
from backend.security.tenant_rls import (
    configure_tenant_rls,
    tenant_rls_prometheus_lines,
)

# Initialize crash reporting provider (Sentry if configured) with fallback mode.
initialize_crash_reporting(
    dsn=os.environ.get("SENTRY_DSN"),
    environment=os.environ.get("FLASK_ENV", "production"),
    release=os.environ.get("APP_VERSION", "1.2.0"),
    traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
    profiles_sample_rate=float(os.environ.get("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
)

# Configure logging - use INFO in production, DEBUG in development
log_level = logging.DEBUG if os.environ.get("FLASK_ENV") == "development" else logging.INFO
logger = logging.getLogger(__name__)
IS_PRODUCTION_MODE = os.environ.get("FLASK_ENV") == "production"
RESOLVED_SESSION_SECRET = None
SESSION_SECRET_SOURCE = "missing"

# Security: Warn about default credentials in production
def validate_production_security():
    """Validate that no default/insecure credentials are in use in production."""
    is_production = IS_PRODUCTION_MODE
    
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
        if not RESOLVED_SESSION_SECRET:
            issues.append("SESSION_SECRET not set")
        elif not is_secure_secret_source(SESSION_SECRET_SOURCE):
            issues.append(f"SESSION_SECRET is not vault-backed (source={SESSION_SECRET_SOURCE})")
        
        if issues:
            logger.error(f"SECURITY: Production security issues: {', '.join(issues)}")
            logger.error("SECURITY: Please fix these issues before deploying to production!")
    else:
        # Development warnings only
        if admin_user and admin_user.lower() in insecure_usernames:
            logger.warning("SECURITY WARNING: Using default admin username. Change before deployment!")
        if admin_pass and admin_pass in insecure_passwords:
            logger.warning("SECURITY WARNING: Using default admin password. Change before deployment!")

# Server configuration - bind to 5000 for Replit
DEFAULT_PORT = int(os.environ.get("PORT", 5000))

# Create Flask app
app = Flask(__name__)

# Resolve SESSION_SECRET through vault-aware resolution pipeline.
RESOLVED_SESSION_SECRET, SESSION_SECRET_SOURCE = resolve_runtime_secret(
    "SESSION_SECRET",
    required=False,
    production_mode=IS_PRODUCTION_MODE and not app.config.get("TESTING", False),
)

try:
    configure_structured_logging(app)
except Exception as exc:
    logging.basicConfig(level=log_level)
    logger.warning("Structured logging setup failed, using basic logging fallback", exc_info=exc)

# Run security validation (non-blocking)
if __name__ != "__main__":  # Only run when starting as server
    validate_production_security()

# Security: Session secret from vault-aware resolver.
app.secret_key = RESOLVED_SESSION_SECRET
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Process-level observability counters for /metrics endpoint.
APP_START_TIME = time.time()
REQUEST_METRICS = {"total": 0, "inflight": 0}
REQUEST_METRICS_LOCK = Lock()

# Session hardening
app.config["SESSION_COOKIE_HTTPONLY"] = True
# In production, enforce Strict SameSite and Secure cookies
is_production = os.environ.get("FLASK_ENV") == "production"
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


@app.before_request
def track_request_metrics_start():
    """Track aggregate request counts for lightweight operational metrics."""
    with REQUEST_METRICS_LOCK:
        REQUEST_METRICS["total"] += 1
        REQUEST_METRICS["inflight"] += 1


@app.after_request
def track_request_metrics_end(response):
    """Ensure in-flight counter is decremented for all completed responses."""
    with REQUEST_METRICS_LOCK:
        REQUEST_METRICS["inflight"] = max(0, REQUEST_METRICS["inflight"] - 1)
    return response


def _sanitize_server_error_payload(payload: dict) -> tuple[dict, bool]:
    fallback = "An internal error occurred. Please try again later."
    changed = False

    if isinstance(payload.get("error"), str):
        original = payload["error"]
        sanitized = normalize_public_error_message(original, fallback)
        if sanitized != original:
            payload["error"] = sanitized
            changed = True

    error_obj = payload.get("error")
    if isinstance(error_obj, dict):
        message = error_obj.get("message")
        if isinstance(message, str):
            sanitized = normalize_public_error_message(message, fallback)
            if sanitized != message:
                error_obj["message"] = sanitized
                changed = True

    if isinstance(payload.get("message"), str):
        original = payload["message"]
        sanitized = normalize_public_error_message(original, fallback)
        if sanitized != original:
            payload["message"] = sanitized
            changed = True

    return payload, changed


@app.after_request
def normalize_server_error_payload(response):
    """Sanitize 5xx JSON payloads to block raw exception/provider leaks."""
    if response.status_code < 500 or not response.is_json:
        return response

    payload = response.get_json(silent=True)
    if not isinstance(payload, dict):
        return response

    sanitized_payload, changed = _sanitize_server_error_payload(payload)
    if not changed:
        return response

    response.set_data(json.dumps(sanitized_payload))
    response.headers["Content-Type"] = "application/json"
    return response


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
from models import User
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
from backend.websocket import init_socketio
init_socketio(app)


def _normalize_origin(raw_origin: str) -> str:
    origin = (raw_origin or "").strip()
    if not origin:
        return ""
    parsed = urlparse(origin)
    if not parsed.scheme or not parsed.netloc:
        return ""
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}"


def _parse_cors_origins(raw_origins):
    if raw_origins is None:
        return []
    if isinstance(raw_origins, str):
        return [item.strip() for item in raw_origins.split(",") if item.strip()]
    if isinstance(raw_origins, (list, tuple, set)):
        return [str(item).strip() for item in raw_origins if str(item).strip()]
    return []


# Configure CORS with explicit allowlist defaults.
cors_origins = _parse_cors_origins(app.config.get("CORS_ORIGINS") or os.environ.get("CORS_ORIGINS"))
if is_production and not app.config.get("TESTING") and (not cors_origins or "*" in cors_origins):
    raise RuntimeError("CORS_ORIGINS must be explicitly configured in production (wildcard is disallowed)")

if not cors_origins:
    cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000", "app://-"]

cors_allow_credentials = "*" not in cors_origins
cors.init_app(
    app,
    resources={r"/api/*": {"origins": cors_origins}},
    supports_credentials=cors_allow_credentials,
)

# Trusted origins used for same-origin CSRF checks on session-authenticated API requests.
TRUSTED_CSRF_ORIGINS = {
    normalized
    for normalized in (_normalize_origin(origin) for origin in cors_origins)
    if normalized
}
TRUSTED_CSRF_ORIGINS.update(
    {
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "app://-",
        "app://dashboard",
    }
)

# Initialize Celery
from backend.celery_app import make_celery
celery = make_celery(app)

# Exempt JSON API endpoints from CSRF (they use session auth or API keys)
# CSRF is still enforced on all HTML form submissions
from flask_wtf.csrf import CSRFError
from backend.security.api_csrf import is_api_csrf_enforced, validate_api_csrf_request
from backend.utils.error_normalization import normalize_public_error_message

# Keep CSRF protection for forms and enforce strict same-origin checks on
# session-authenticated API/GraphQL requests.
app.config["WTF_CSRF_CHECK_DEFAULT"] = False

CSRF_API_EXEMPT_PATH_PREFIXES = (
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/mfa/verify",
    "/api/v1/auth/desktop/challenge",
    "/api/v1/auth/desktop/auto-login",
    "/api/v1/auth/callback/sso",
)


def _request_uses_session_cookie() -> bool:
    return any(
        request.cookies.get(cookie_name)
        for cookie_name in ("session", "session_id", "remember_token")
    )


def _request_uses_stateless_auth() -> bool:
    auth_header = request.headers.get("Authorization", "")
    return bool(request.headers.get("X-API-Key") or auth_header.lower().startswith("bearer "))


def _is_trusted_origin_request() -> bool:
    origin_header = request.headers.get("Origin", "")
    if origin_header:
        return _normalize_origin(origin_header) in TRUSTED_CSRF_ORIGINS

    referer_header = request.headers.get("Referer", "")
    if referer_header:
        return _normalize_origin(referer_header) in TRUSTED_CSRF_ORIGINS

    return False


@app.before_request
def csrf_for_forms_only():
    if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
        return None

    if current_app.config.get("TESTING") or os.environ.get("FLASK_ENV") == "testing":
        return None

    is_api_like_request = request.path.startswith("/api/") or request.path.startswith("/graphql")
    if is_api_like_request:
        if _request_uses_session_cookie() and not _request_uses_stateless_auth():
            if not _is_trusted_origin_request():
                return jsonify(
                    {
                        "error": "Cross-site state-changing request blocked",
                        "success": False,
                        "code": "CSRF_ORIGIN_CHECK_FAILED",
                    }
                ), 403
            is_exempt = any(request.path.startswith(prefix) for prefix in CSRF_API_EXEMPT_PATH_PREFIXES)
            if is_api_csrf_enforced() and not is_exempt:
                csrf_ok, csrf_error = validate_api_csrf_request()
                if not csrf_ok:
                    return jsonify(
                        {
                            "error": csrf_error or "CSRF request token invalid",
                            "success": False,
                            "code": "CSRF_TOKEN_CHECK_FAILED",
                        }
                    ), 403
        return None

    csrf.protect()
    return None

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

# Configure optional Postgres tenant RLS policy bootstrap + request context binding.
TENANT_RLS_STATUS = configure_tenant_rls(app, db)
if TENANT_RLS_STATUS.get("enabled"):
    logger.info(
        "Tenant RLS enabled (policy=%s, bootstrap=%s)",
        TENANT_RLS_STATUS.get("policy_name"),
        TENANT_RLS_STATUS.get("bootstrap", {}).get("status"),
    )
else:
    logger.info(
        "Tenant RLS disabled or skipped (dialect=%s, reason=%s)",
        TENANT_RLS_STATUS.get("dialect"),
        TENANT_RLS_STATUS.get("bootstrap", {}).get("reason"),
    )

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
        "secret_source": SESSION_SECRET_SOURCE,
    }


def _database_health() -> dict:
    """Confirm database connectivity with a trivial query."""

    try:
        with db.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        db.session.rollback()
        logger.error("Database connectivity check failed", exc_info=exc)
        return {"status": "error", "detail": "unavailable"}

    return {"status": "ok"}


def _readiness_payload() -> tuple[dict, int]:
    """Build canonical readiness payload and HTTP status."""
    config_state = _config_health()
    database_state = _database_health()

    blockers = []
    if database_state.get("status") != "ok":
        blockers.append("database")
    if config_state.get("secret_key") == "missing":
        blockers.append("secret_key")

    is_ready = not blockers
    status_code = 200 if is_ready else 503
    payload = {
        "status": "ready" if is_ready else "not_ready",
        "checks": {
            "database": database_state.get("status", "error"),
            "secret_key": config_state.get("secret_key", "missing"),
        },
        "blockers": blockers,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    return payload, status_code


def _prometheus_metrics_payload() -> str:
    """Render low-cardinality Prometheus metrics in text exposition format."""
    uptime_seconds = max(0.0, time.time() - APP_START_TIME)
    with REQUEST_METRICS_LOCK:
        total_requests = REQUEST_METRICS["total"]
        inflight_requests = REQUEST_METRICS["inflight"]

    readiness_payload, readiness_code = _readiness_payload()
    readiness_ok = 1 if readiness_code == 200 else 0
    database_ok = 1 if readiness_payload["checks"].get("database") == "ok" else 0

    lines = [
        "# HELP datalogicengine_process_uptime_seconds Process uptime in seconds.",
        "# TYPE datalogicengine_process_uptime_seconds gauge",
        f"datalogicengine_process_uptime_seconds {uptime_seconds:.3f}",
        "# HELP datalogicengine_http_requests_total Total HTTP requests handled by Flask app.",
        "# TYPE datalogicengine_http_requests_total counter",
        f"datalogicengine_http_requests_total {total_requests}",
        "# HELP datalogicengine_http_requests_inflight Current in-flight requests.",
        "# TYPE datalogicengine_http_requests_inflight gauge",
        f"datalogicengine_http_requests_inflight {inflight_requests}",
        "# HELP datalogicengine_ready Ready status (1=ready, 0=not ready).",
        "# TYPE datalogicengine_ready gauge",
        f"datalogicengine_ready {readiness_ok}",
        "# HELP datalogicengine_database_ready Database readiness (1=ok, 0=error).",
        "# TYPE datalogicengine_database_ready gauge",
        f"datalogicengine_database_ready {database_ok}",
    ]
    lines.extend(connector_metrics_prometheus_lines(prefix="datalogicengine"))
    lines.extend(ai_latency_metrics_prometheus_lines(prefix="datalogicengine"))
    lines.extend(latency_slo_prometheus_lines(prefix="datalogicengine"))
    lines.extend(crash_reporting_prometheus_lines(prefix="datalogicengine"))
    lines.extend(tenant_rls_prometheus_lines(TENANT_RLS_STATUS, prefix="datalogicengine"))
    return "\n".join(lines) + "\n"


@app.route("/live", methods=["GET"])
def live() -> tuple:
    """Liveness endpoint: process is running."""
    return jsonify(
        {
            "status": "live",
            "service": "datalogicengine",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    ), 200


@app.route("/ready", methods=["GET"])
def ready() -> tuple:
    """Readiness endpoint: app dependencies are operational."""
    payload, status_code = _readiness_payload()
    return jsonify(payload), status_code


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


@app.route("/metrics", methods=["GET"])
def metrics() -> Response:
    """Canonical metrics endpoint for infrastructure scraping."""
    return Response(
        _prometheus_metrics_payload(),
        mimetype="text/plain; version=0.0.4; charset=utf-8",
    )

# Note: /login, /register, /logout, /dashboard are defined in routes.py with more complete implementations


# Register Simulation API routes
if 'simulation_api' in app.blueprints:
    logger.info("Simulation API routes already registered via routes package; skipping duplicate backend blueprint")
else:
    try:
        from backend.routes.simulation_routes import simulation_bp
        app.register_blueprint(simulation_bp, url_prefix='/api/v1/simulations')
        logger.info("Simulation API routes registered")
    except ImportError as e:
        logger.warning(f"Could not register Simulation API routes: {e}")


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
    crash_id = capture_exception_with_fallback(
        e,
        context={
            "handler": "500",
            "path": request.path,
            "method": request.method,
        },
    )
    # Log the full error internally (with stack trace)
    logger.error("500 Internal Server Error (crash_id=%s): %s", crash_id, str(e), exc_info=True)

    # NEVER expose stack traces to users in production
    response = jsonify({
        'success': False,
        'error': {
            'code': 'INTERNAL_SERVER_ERROR',
            'message': 'An internal error occurred. Please try again later.',
            'crash_id': crash_id,
        }
    })
    response.headers["X-Crash-ID"] = crash_id
    return response, 500


@app.errorhandler(Exception)
def unhandled_exception(e):
    """Fallback handler for non-HTTP uncaught exceptions."""
    if isinstance(e, HTTPException):
        return e
    return server_error(e)

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

    # Local `python app.py` defaults to loopback-only; production should use a WSGI server.
    run_host = os.environ.get('FLASK_RUN_HOST', '127.0.0.1')
    app.run(host=run_host, port=DEFAULT_PORT, debug=debug_mode)
