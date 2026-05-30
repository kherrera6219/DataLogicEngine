# ruff: noqa: E402
import os
import re
import json
import logging
import time
from threading import Lock, Thread
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse
from dotenv import load_dotenv

from backend.bootstrap_compat import apply_runtime_compatibility_patches

# Load environment variables from .env file BEFORE any other imports
load_dotenv(override=False)  # override=False: Electron env vars take priority; .env fills only missing vars
apply_runtime_compatibility_patches()

from flask import Flask, render_template, request, redirect, flash, jsonify, current_app, Response, g
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
IS_DESKTOP_MODE = os.environ.get("IS_DESKTOP_APP", "False").lower() == "true"
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
# Fail fast if no secret is available in production; generate an ephemeral one for development.
if not RESOLVED_SESSION_SECRET:
    if IS_PRODUCTION_MODE:
        raise RuntimeError(
            "SESSION_SECRET must be configured before starting in production. "
            "Run: python scripts/generate_secrets.py"
        )
    import secrets as _secrets  # noqa: PLC0415
    RESOLVED_SESSION_SECRET = _secrets.token_hex(32)
    SESSION_SECRET_SOURCE = "ephemeral"
    logger.warning(
        "SESSION_SECRET not set — using an ephemeral secret for this process. "
        "Sessions will be invalidated on restart. Set SESSION_SECRET in .env for persistent sessions."
    )
app.secret_key = RESOLVED_SESSION_SECRET
if os.environ.get("TRUST_PROXY_HEADERS", "false").lower() == "true":
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Process-level observability counters for /metrics endpoint.
APP_START_TIME = time.time()
REQUEST_METRICS = {
    "total": 0,
    "inflight": 0,
    "route_status_totals": {},
    "route_latency_ms": {},
}
REQUEST_METRICS_LOCK = Lock()
LEGACY_API_PREFIXES = {
    "/api/compliance": "/api/v1/compliance",
    "/api/ka": "/api/v1/ka",
    "/api/mcp": "/api/v1/mcp",
    "/api/persona": "/api/v1/persona",
    "/api/pillar": "/api/v1/pillar",
    "/api/simulations": "/api/v1/simulations",
    "/api/truth": "/api/v1/truth",
    "/api/ukg": "/api/v1",
}
LEGACY_API_SUNSET = "Wed, 30 Sep 2026 00:00:00 GMT"

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


def _metric_route_label() -> str:
    """Return a low-cardinality route label for request metrics."""
    if request.url_rule and request.url_rule.rule:
        return request.url_rule.rule
    return "unmatched"


def _prometheus_label_value(value: str) -> str:
    """Escape Prometheus label values safely."""
    return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


@app.before_request
def track_request_metrics_start():
    """Track aggregate request counts for lightweight operational metrics."""
    g.request_started_at = time.perf_counter()
    with REQUEST_METRICS_LOCK:
        REQUEST_METRICS["total"] += 1
        REQUEST_METRICS["inflight"] += 1


@app.after_request
def track_request_metrics_end(response):
    """Ensure in-flight counter is decremented for all completed responses."""
    route_label = _metric_route_label()
    status_family = f"{response.status_code // 100}xx"
    method = request.method.upper()
    duration_ms = max(
        0.0,
        (time.perf_counter() - getattr(g, "request_started_at", time.perf_counter())) * 1000.0,
    )

    with REQUEST_METRICS_LOCK:
        REQUEST_METRICS["inflight"] = max(0, REQUEST_METRICS["inflight"] - 1)
        route_status_key = (method, route_label, status_family)
        route_status_totals = REQUEST_METRICS["route_status_totals"]
        route_status_totals[route_status_key] = route_status_totals.get(route_status_key, 0) + 1

        latency_key = (method, route_label)
        route_latency = REQUEST_METRICS["route_latency_ms"]
        latency_stats = route_latency.setdefault(
            latency_key,
            {"count": 0, "sum_ms": 0.0, "max_ms": 0.0},
        )
        latency_stats["count"] += 1
        latency_stats["sum_ms"] += duration_ms
        latency_stats["max_ms"] = max(latency_stats["max_ms"], duration_ms)
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


def _legacy_api_successor_path(path: str) -> str | None:
    for legacy_prefix, canonical_prefix in LEGACY_API_PREFIXES.items():
        if path == legacy_prefix or path.startswith(f"{legacy_prefix}/"):
            return f"{canonical_prefix}{path[len(legacy_prefix):]}"
    return None


def _split_config_values(raw_value) -> list[str]:
    if not raw_value:
        return []
    if isinstance(raw_value, str):
        return [item.strip() for item in raw_value.split(",") if item.strip()]
    if isinstance(raw_value, (list, tuple, set)):
        return [str(item).strip() for item in raw_value if str(item).strip()]
    return []


def _hostname_from_value(raw_value: str) -> str:
    value = (raw_value or "").strip().lower()
    if not value:
        return ""
    if "://" in value:
        return (urlparse(value).hostname or "").lower().rstrip(".")
    return (urlparse(f"//{value}").hostname or value.split(":", 1)[0]).lower().rstrip(".")


def _trusted_hosts() -> set[str]:
    raw_hosts = current_app.config.get("TRUSTED_HOSTS") or os.environ.get("TRUSTED_HOSTS")
    hosts = {_hostname_from_value(host) for host in _split_config_values(raw_hosts)}

    server_name = current_app.config.get("SERVER_NAME")
    if server_name:
        hosts.add(_hostname_from_value(server_name))

    canonical_origin = current_app.config.get("CANONICAL_EXTERNAL_ORIGIN") or os.environ.get("CANONICAL_EXTERNAL_ORIGIN")
    if canonical_origin:
        hosts.add(_hostname_from_value(canonical_origin))

    return {host for host in hosts if host}


def _request_hostname() -> str:
    raw_host = request.environ.get("HTTP_HOST") or request.environ.get("SERVER_NAME") or ""
    return _hostname_from_value(raw_host)


@app.before_request
def validate_trusted_host():
    """Reject untrusted Host values when a host policy is configured."""
    if IS_DESKTOP_MODE:
        return None

    trusted_hosts = _trusted_hosts()
    if not trusted_hosts:
        if os.environ.get("FLASK_ENV") == "production" and not current_app.config.get("TESTING"):
            return jsonify(
                {
                    "error": "Trusted host policy is not configured",
                    "success": False,
                    "code": "TRUSTED_HOSTS_NOT_CONFIGURED",
                }
            ), 500
        return None

    if _request_hostname() not in trusted_hosts:
        return jsonify(
            {
                "error": "Untrusted host",
                "success": False,
                "code": "UNTRUSTED_HOST",
            }
        ), 400
    return None


def _redirect_target_url() -> str:
    canonical_origin = current_app.config.get("CANONICAL_EXTERNAL_ORIGIN") or os.environ.get("CANONICAL_EXTERNAL_ORIGIN")
    path = request.full_path if request.query_string else request.path
    if canonical_origin:
        return f"{canonical_origin.rstrip('/')}{path}"
    return request.url.replace("http://", "https://", 1)


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


@app.after_request
def add_legacy_api_deprecation_headers(response):
    successor_path = _legacy_api_successor_path(request.path)
    if successor_path is None:
        return response

    response.headers.setdefault("Deprecation", "true")
    response.headers.setdefault("Sunset", LEGACY_API_SUNSET)
    response.headers.setdefault("X-DataLogicEngine-Route-Status", "legacy")
    response.headers.add("Link", f'<{successor_path}>; rel="successor-version"')
    return response


# Strict TLS Redirection in Production
@app.before_request
def force_https():
    """Force HTTPS redirection in production environments."""
    is_prod = os.environ.get('FLASK_ENV') == 'production'
    if IS_DESKTOP_MODE:
        return None
    if is_prod and not current_app.config.get("TESTING") and not request.is_secure:
        return redirect(_redirect_target_url(), code=301)

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
from extensions import db, login_manager, csrf, migrate, cache, compress, cors
from models import User
db.init_app(app)
login_manager.init_app(app)
csrf.init_app(app)
migrate.init_app(app, db)

# Configure limiter storage — auto-wire to Redis when available so rate limit
# counters are shared across all Gunicorn workers (prevents bypass via multi-process).
_explicit_rate_storage = os.environ.get("RATELIMIT_STORAGE_URI")
if _explicit_rate_storage:
    app.config["RATELIMIT_STORAGE_URI"] = _explicit_rate_storage
elif use_redis:
    app.config["RATELIMIT_STORAGE_URI"] = redis_url
else:
    app.config["RATELIMIT_STORAGE_URI"] = "memory://"
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
# Electron app:// origins are always allowed — the scheme is not reachable from web browsers.
TRUSTED_CSRF_ORIGINS.update({"app://-", "app://dashboard"})
# Loopback origins are only trusted in non-production to avoid CSRF bypass in deployed environments.
if not IS_PRODUCTION_MODE:
    TRUSTED_CSRF_ORIGINS.update(
        {
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5000",
            "http://127.0.0.1:5000",
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


@login_manager.request_loader
def load_desktop_user_from_request(_request):
    """Authenticate signed Electron loopback requests without relying on cookies."""
    from backend.auth.api_decorators import check_desktop_request_auth

    is_auth, user = check_desktop_request_auth()
    return user if is_auth else None


def password_meets_policy(password: str) -> bool:
    """Enforce a basic password policy for initial hardening."""
    if not password or len(password) < 12:
        return False
    has_upper = re.search(r"[A-Z]", password)
    has_lower = re.search(r"[a-z]", password)
    has_digit = re.search(r"\d", password)
    has_symbol = re.search(r"[^A-Za-z0-9]", password)
    return all([has_upper, has_lower, has_digit, has_symbol])

def _should_auto_create_schema() -> bool:
    """Require explicit opt-in before mutating schema at process startup."""
    return os.environ.get("AUTO_CREATE_SCHEMA", "False").lower() == "true"


def _initialize_database_schema() -> None:
    """Initialize schema only when explicitly requested for disposable environments."""
    if not _should_auto_create_schema():
        logger.info("Startup schema auto-creation disabled; use 'flask db upgrade' or backend/init_db.py.")
        return

    if IS_PRODUCTION_MODE and not IS_DESKTOP_MODE:
        raise RuntimeError(
            "AUTO_CREATE_SCHEMA=true is not allowed in production. "
            "Apply migrations explicitly with 'flask db upgrade' before startup."
        )

    with app.app_context():
        db.create_all()
        logger.warning(
            "Database tables auto-created because AUTO_CREATE_SCHEMA=true. "
            "Do not enable this in managed or production environments."
        )


_initialize_database_schema()

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

def _register_application_routes() -> None:
    """Register canonical application blueprints in one startup location."""
    from backend.truth_engine.api import truth_api

    app.register_blueprint(truth_api, url_prefix='/api/v1/truth')
    app.register_blueprint(truth_api, name='truth_legacy', url_prefix='/api/truth')
    logger.info("Truth Engine API blueprint registered (v1 + legacy)")

    try:
        from backend.persona_api import persona_api
        app.register_blueprint(persona_api, url_prefix='/api/v1/persona')
        app.register_blueprint(persona_api, name='persona_legacy', url_prefix='/api/persona')
        logger.info("Persona API blueprint registered (v1 + legacy)")
    except ImportError as e:
        logger.warning(f"Could not register Persona API blueprint: {e}")

    try:
        from backend.pillar_api import pillar_api
        app.register_blueprint(pillar_api, url_prefix='/api/v1/pillar')
        app.register_blueprint(pillar_api, name='pillar_legacy', url_prefix='/api/pillar')
        logger.info("Pillar API blueprint registered (v1 + legacy)")
    except ImportError as e:
        logger.warning(f"Could not register Pillar API blueprint: {e}")

    try:
        from backend.regulatory_api import regulatory_api
        app.register_blueprint(regulatory_api, url_prefix='/api/v1/compliance')
        app.register_blueprint(regulatory_api, name='compliance_legacy', url_prefix='/api/compliance')
        app.register_blueprint(regulatory_api, name='regulatory_api_v1', url_prefix='/api/v1/regulatory')
        logger.info("Regulatory/Compliance API blueprint registered (v1 + legacy)")
    except ImportError as e:
        logger.warning(f"Could not register Regulatory/Compliance API blueprint: {e}")

    from backend.ukg_api import ukg_api

    app.register_blueprint(ukg_api, url_prefix='/api/v1')
    app.register_blueprint(ukg_api, name='ukg_legacy', url_prefix='/api/ukg')

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

    from flask_swagger_ui import get_swaggerui_blueprint

    swaggerui_blueprint = get_swaggerui_blueprint(
        '/api/docs',
        '/static/swagger.json',
        config={'app_name': "Universal Knowledge Graph API"},
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix='/api/docs')
    logger.info("Swagger UI registered at /api/docs")

    try:
        from backend.tracing.api import trace_bp
        app.register_blueprint(trace_bp)
        logger.info("Trace API blueprint registered at /api/v1/trace")
    except ImportError as e:
        logger.warning(f"Could not register Trace API blueprint: {e}")

    try:
        from backend.llm_gateway.api import register_gateway_routes
        register_gateway_routes(app)
        logger.info("LLM Gateway API registered at /api/v1/gateway and /api/admin")
    except ImportError as e:
        logger.warning(f"Could not register LLM Gateway API: {e}")

    try:
        from backend.routes.analytics_routes import analytics_bp
        app.register_blueprint(analytics_bp)
        logger.info("Analytics API registered at /api/v1/analytics")
    except ImportError as e:
        logger.warning(f"Could not register Analytics API: {e}")

    try:
        logger.debug("Registering GraphQL...")
        from backend.graphql_schema import register_graphql
        register_graphql(app)
        logger.info("GraphQL API registered at /graphql (GraphiQL enabled)")
    except ImportError as e:
        logger.warning(f"Could not register GraphQL API: {e}")
    except Exception as e:
        logger.error(f"GraphQL registration error: {e}")

    try:
        from backend.routes.gdpr_routes import gdpr_bp
        app.register_blueprint(gdpr_bp)
        logger.info("GDPR API registered at /api/v1/gdpr")
    except ImportError as e:
        logger.warning(f"Could not register GDPR API: {e}")

    try:
        from backend.routes.retention_routes import retention_bp
        app.register_blueprint(retention_bp)
        logger.info("Retention API registered at /api/v1/retention")
    except ImportError as e:
        logger.warning(f"Could not register Retention API: {e}")

    try:
        from backend.routes.privacy_routes import privacy_bp
        app.register_blueprint(privacy_bp)
        logger.info("Privacy API registered at /api/v1/privacy")
    except ImportError as e:
        logger.warning(f"Could not register Privacy API: {e}")

    from routes import register_routes

    register_routes(app)


_register_application_routes()


def _initialize_storage_collections() -> None:
    """Ensure ChromaDB named collections and object-storage buckets exist at startup."""
    try:
        from backend.storage.vector_store import initialize_collections
        initialize_collections()
        logger.info("ChromaDB collections initialized")
        _maybe_start_db_c_indexing()
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("ChromaDB collection init skipped: %s", exc)

    try:
        from backend.storage.object_store import get_object_store
        store = get_object_store()
        for bucket in ["audit_logs", "simulation_artifacts", "deliverables", "graphs", "eval_data"]:
            store.create_bucket(bucket)
        logger.info("Object storage buckets initialized")
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Object storage bucket init skipped: %s", exc)

def _chroma_collection_counts() -> dict:
    """Return ChromaDB collection counts for health and desktop IPC."""
    try:
        from backend.storage.vector_store import get_collection_counts

        return get_collection_counts()
    except Exception as exc:  # pylint: disable=broad-except
        logger.debug("ChromaDB collection counts unavailable: %s", exc)
        return {}


def _redis_ping_ms() -> float | None:
    """Return Redis ping latency in milliseconds when Redis is reachable."""
    try:
        import redis

        redis_url = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
        client = redis.Redis.from_url(redis_url, socket_connect_timeout=0.5, socket_timeout=0.5)
        start = time.perf_counter()
        client.ping()
        return round((time.perf_counter() - start) * 1000, 3)
    except Exception as exc:  # pylint: disable=broad-except
        logger.debug("Redis ping unavailable: %s", exc)
        return None


def _object_store_bucket_stats() -> dict:
    """Return object-store bucket counts and byte totals for health and desktop IPC."""
    buckets = ["audit_logs", "simulation_artifacts", "deliverables", "graphs", "eval_data"]
    stats: dict[str, dict[str, int | str]] = {}
    try:
        from backend.storage.object_store import get_object_store

        store = get_object_store()
        for bucket in buckets:
            objects = store.list(bucket)
            stats[bucket] = {
                "object_count": len(objects),
                "total_bytes": sum(int(getattr(obj, "size", 0) or 0) for obj in objects),
            }
        return {"status": "ok", "buckets": stats}
    except Exception as exc:  # pylint: disable=broad-except
        logger.debug("Object-store bucket stats unavailable: %s", exc)
        return {
            "status": "unavailable",
            "buckets": {
                bucket: {"object_count": 0, "total_bytes": 0}
                for bucket in buckets
            },
        }


def _structured_memory_stats() -> dict:
    """Return StructuredMemoryGraph stats for health and desktop IPC."""
    try:
        from backend.memory import get_unified_memory_service

        return get_unified_memory_service().stats()
    except Exception as exc:  # pylint: disable=broad-except
        logger.debug("Structured memory stats unavailable: %s", exc)
        return {
            "status": "unavailable",
            "memory_vertices": 0,
            "memory_edges": 0,
            "last_recall_timestamp": None,
        }


def _db_c_auto_index_enabled() -> bool:
    configured = os.environ.get("DB_C_AUTO_INDEX_ON_STARTUP")
    if configured is not None:
        return configured.lower() in {"1", "true", "yes", "on"}
    if os.environ.get("FLASK_ENV", "").lower() == "testing":
        return False
    return os.environ.get("IS_DESKTOP_APP", "").lower() in {"1", "true", "yes", "on"}


def _run_db_c_indexing_background() -> None:
    """Run DB-C knowledge-node indexing inside an app context."""
    try:
        from scripts.index_knowledge_nodes import index_from_database

        with app.app_context():
            result = index_from_database()
        logger.info("DB-C knowledge_nodes background index complete: %s", result.to_dict())
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("DB-C knowledge_nodes background index failed: %s", exc)


def _maybe_start_db_c_indexing() -> None:
    """Trigger DB-C indexing when local desktop Chroma starts empty."""
    if not _db_c_auto_index_enabled():
        return
    counts = _chroma_collection_counts()
    if counts.get("knowledge_nodes", 0) > 0:
        return
    Thread(target=_run_db_c_indexing_background, name="db-c-index-knowledge-nodes", daemon=True).start()


_initialize_storage_collections()


def _initialize_uskd_memory_graph() -> None:
    """Load the RAM-resident USKD graph from SQL rows, then Neo4j if available."""
    try:
        from backend.storage import get_graph_store, get_uskd_memory_graph

        memory_graph = get_uskd_memory_graph()
        with app.app_context():
            sql_stats = memory_graph.load_from_database(db.session)
        logger.info("USKD memory graph loaded from SQL: %s", sql_stats.to_dict())

        graph_store = get_graph_store()
        if os.environ.get("USKD_SYNC_NEO4J_ON_STARTUP", "false").lower() in {"1", "true", "yes", "on"}:
            try:
                from scripts.sync_nodes_to_neo4j import sync

                sync_result = sync()
                logger.info("USKD SQL→Neo4j startup sync complete: %s", sync_result)
            except Exception as sync_exc:  # pylint: disable=broad-except
                logger.warning("USKD SQL→Neo4j startup sync skipped: %s", sync_exc)

        neo4j_stats = memory_graph.load_from_neo4j(graph_store)
        if neo4j_stats.node_count:
            logger.info("USKD memory graph refreshed from Neo4j: %s", neo4j_stats.to_dict())
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("USKD memory graph init skipped: %s", exc)


_initialize_uskd_memory_graph()


def _start_local_databases() -> None:
    """Auto-start bundled PostgreSQL, Redis, and Neo4j when running in local/desktop mode.

    Mirrors the main.py Electron startup pattern so plain `python app.py` behaves
    identically to the packaged desktop app.  Non-fatal — a missing binary directory
    or an already-running service is silently skipped.
    """
    import atexit

    try:
        from backend.storage.runtime_settings import get_auto_start_databases
        if not get_auto_start_databases():
            logger.info("Local database auto-start disabled by user setting")
            return
    except Exception as exc:
        logger.debug("Could not read auto-start setting, defaulting to enabled: %s", exc)

    try:
        from backend.storage.database_manager import get_db_manager
        db_manager = get_db_manager()
        db_manager.start_all()
        atexit.register(db_manager.stop_all)
        logger.info("Local database auto-start complete")
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Local database auto-start skipped: %s", exc)


_start_local_databases()


@app.route('/api/v1/csp-report', methods=['POST'])
def csp_report():
    """Receive and log Content-Security-Policy violation reports."""
    try:
        payload = request.get_json(force=True, silent=True) or {}
        report = payload.get('csp-report', payload)
        logger.warning("CSP violation: blocked-uri=%s violated-directive=%s document-uri=%s",
                       report.get('blocked-uri', ''),
                       report.get('violated-directive', ''),
                       report.get('document-uri', ''))
    except Exception as exc:  # pylint: disable=broad-except
        logger.debug("Failed to parse CSP report: %s", exc)
    return '', 204


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
    """Confirm database connectivity and local vector-store readiness."""

    try:
        with db.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        db.session.rollback()
        logger.error("Database connectivity check failed", exc_info=exc)
        return {"status": "error", "detail": "unavailable"}

    return {
        "status": "ok",
        "chromadb": {
            "collections": _chroma_collection_counts(),
        },
        "redis": {
            "ping_ms": _redis_ping_ms(),
        },
        "object_store": _object_store_bucket_stats(),
        "memory": _structured_memory_stats(),
    }


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
        route_status_totals = dict(REQUEST_METRICS["route_status_totals"])
        route_latency_ms = {
            key: value.copy()
            for key, value in REQUEST_METRICS["route_latency_ms"].items()
        }

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
        "# HELP datalogicengine_http_requests_by_route_total Total HTTP requests by route, method, and status family.",
        "# TYPE datalogicengine_http_requests_by_route_total counter",
        "# HELP datalogicengine_http_request_latency_ms_avg Average request latency in milliseconds by route and method.",
        "# TYPE datalogicengine_http_request_latency_ms_avg gauge",
        "# HELP datalogicengine_http_request_latency_ms_max Maximum request latency in milliseconds by route and method.",
        "# TYPE datalogicengine_http_request_latency_ms_max gauge",
        "# HELP datalogicengine_ready Ready status (1=ready, 0=not ready).",
        "# TYPE datalogicengine_ready gauge",
        f"datalogicengine_ready {readiness_ok}",
        "# HELP datalogicengine_database_ready Database readiness (1=ok, 0=error).",
        "# TYPE datalogicengine_database_ready gauge",
        f"datalogicengine_database_ready {database_ok}",
    ]
    for (method, route_label, status_family), count in sorted(route_status_totals.items()):
        lines.append(
            'datalogicengine_http_requests_by_route_total'
            f'{{method="{_prometheus_label_value(method)}",route="{_prometheus_label_value(route_label)}",status="{_prometheus_label_value(status_family)}"}} {count}'
        )

    for (method, route_label), stats in sorted(route_latency_ms.items()):
        count = max(1, int(stats.get("count", 0)))
        avg_ms = float(stats.get("sum_ms", 0.0)) / count
        max_ms = float(stats.get("max_ms", 0.0))
        label_fragment = (
            f'method="{_prometheus_label_value(method)}",'
            f'route="{_prometheus_label_value(route_label)}"'
        )
        lines.append(f"datalogicengine_http_request_latency_ms_avg{{{label_fragment}}} {avg_ms:.3f}")
        lines.append(f"datalogicengine_http_request_latency_ms_max{{{label_fragment}}} {max_ms:.3f}")

    lines.extend(connector_metrics_prometheus_lines(prefix="datalogicengine"))
    lines.extend(ai_latency_metrics_prometheus_lines(prefix="datalogicengine"))
    lines.extend(latency_slo_prometheus_lines(prefix="datalogicengine"))
    lines.extend(crash_reporting_prometheus_lines(prefix="datalogicengine"))
    lines.extend(tenant_rls_prometheus_lines(TENANT_RLS_STATUS, prefix="datalogicengine"))
    try:
        from backend.dmrf import DMRFOrchestrator

        lines.extend(DMRFOrchestrator.prometheus_lines(prefix="datalogicengine"))
    except Exception:
        lines.extend(
            [
                "# HELP datalogicengine_dmrf_metrics_available DMRF metrics availability.",
                "# TYPE datalogicengine_dmrf_metrics_available gauge",
                "datalogicengine_dmrf_metrics_available 0",
            ]
        )
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


@app.route("/health/cache", methods=["GET"])
def health_cache() -> tuple:
    """Redis liveness check for QC validation."""
    from backend.storage.connection_manager import get_connection_manager
    ok = get_connection_manager().check_health("redis")
    status = "ok" if ok else "unavailable"
    return jsonify({"redis": status, "timestamp": datetime.now(UTC).isoformat()}), 200 if ok else 503


@app.route("/metrics", methods=["GET"])
def metrics() -> Response:
    """Canonical metrics endpoint for infrastructure scraping."""
    return Response(
        _prometheus_metrics_payload(),
        mimetype="text/plain; version=0.0.4; charset=utf-8",
    )

# Note: /login, /register, /logout, /dashboard are defined in routes.py with more complete implementations


# Simulation API routes are registered via routes.register_routes()


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
def create_app(config_name=None, config_overrides=None):
    """Return the configured application, with lightweight test overrides.

    The application still uses the legacy global app for compatibility with
    existing scripts and tests, but callers can request common runtime profiles
    without mutating config piecemeal at every call site.
    """
    if isinstance(config_name, dict):
        app.config.update(config_name)
    elif config_name in {"test", "testing"}:
        app.config.update(
            TESTING=True,
            WTF_CSRF_ENABLED=False,
            RATELIMIT_ENABLED=False,
        )

    if config_overrides:
        app.config.update(config_overrides)

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
