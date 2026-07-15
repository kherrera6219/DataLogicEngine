# ruff: noqa: E402
import os
import re
import json
import logging
import secrets
import sys
import time
from pathlib import Path
from threading import Lock, Thread
from datetime import UTC, datetime, timedelta
from urllib.parse import urlparse
from dotenv import load_dotenv

from backend.bootstrap_compat import apply_runtime_compatibility_patches

from flask import Blueprint, Flask, has_request_context, render_template, request, redirect, flash, jsonify, current_app, Response, g
from flask_login import current_user
from werkzeug.local import LocalProxy
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.exceptions import HTTPException
from extensions import limiter
from backend.runtime import (
    APP_SERVICE_KEYS,
    ApplicationRuntime,
    InstallationIdentity,
    LifecycleResult,
    PodmanDataPlaneManager,
    RuntimePhase,
    ServiceState,
    get_application_runtime,
)
from backend.runtime.application import default_runtime_root
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
from backend.auth.api_decorators import api_login_required, api_session_login_required

logger = logging.getLogger(__name__)
core_bp = Blueprint("dle_core", __name__)

# Security: Warn about default credentials in production
def validate_production_security(app: Flask) -> None:
    """Validate that no default/insecure credentials are in use in production."""
    is_production = bool(app.config.get("DLE_PRODUCTION_MODE"))
    
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
        if not app.secret_key:
            issues.append("SESSION_SECRET not set")
        elif not is_secure_secret_source(app.config.get("DLE_SESSION_SECRET_SOURCE", "missing")):
            issues.append(
                "SESSION_SECRET is not vault-backed "
                f"(source={app.config.get('DLE_SESSION_SECRET_SOURCE', 'missing')})"
            )
        
        if issues:
            logger.error(f"SECURITY: Production security issues: {', '.join(issues)}")
            logger.error("SECURITY: Please fix these issues before deploying to production!")
    else:
        # Development warnings only
        if admin_user and admin_user.lower() in insecure_usernames:
            logger.warning("SECURITY WARNING: Using default admin username. Change before deployment!")
        if admin_pass and admin_pass in insecure_passwords:
            logger.warning("SECURITY WARNING: Using default admin password. Change before deployment!")

# Server configuration remains a constant default; each entry point resolves its
# final port from the application configuration.
DEFAULT_PORT = int(os.environ.get("PORT", 5000))
LEGACY_API_PREFIXES = {
    "/api/compliance": "/api/v1/compliance",
    "/api/ka": "/api/v1/ka",
    "/api/mcp": "/api/v1/mcp",
    "/api/persona": "/api/v1/persona",
    "/api/pillar": "/api/v1/pillar",
    "/api/simulations": "/api/v1/simulations",
    "/api/truth": "/api/v1/truth",
    "/api/ukg": "/api/v1",
    "/api/v1/ukg": "/api/v1",
}
LEGACY_API_SUNSET = "Wed, 30 Sep 2026 00:00:00 GMT"


def _metric_route_label() -> str:
    """Return a low-cardinality route label for request metrics."""
    if request.url_rule and request.url_rule.rule:
        return request.url_rule.rule
    return "unmatched"


def _prometheus_label_value(value: str) -> str:
    """Escape Prometheus label values safely."""
    return str(value).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _current_correlation_id() -> str | None:
    return getattr(g, "correlation_id", None) if has_request_context() else None


@core_bp.before_app_request
def track_request_metrics_start():
    """Track aggregate request counts for lightweight operational metrics."""
    g.request_started_at = time.perf_counter()
    get_application_runtime().metrics.begin_request()


@core_bp.before_app_request
def enforce_runtime_admission():
    """Reject new mutations while startup, shutdown, or lifecycle work drains."""
    runtime = get_application_runtime()
    if runtime.admits_request(request.method, request.path):
        return None
    return jsonify(
        {
            "success": False,
            "error": "Application runtime is not accepting new work",
            "code": "RUNTIME_NOT_ACCEPTING_WORK",
            "phase": runtime.phase.value,
        }
    ), 503


@core_bp.after_app_request
def track_request_metrics_end(response):
    """Ensure in-flight counter is decremented for all completed responses."""
    route_label = _metric_route_label()
    method = request.method.upper()
    duration_ms = max(
        0.0,
        (time.perf_counter() - getattr(g, "request_started_at", time.perf_counter())) * 1000.0,
    )

    get_application_runtime().metrics.record_request(
        method,
        route_label,
        response.status_code,
        duration_ms,
    )
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


@core_bp.before_app_request
def validate_trusted_host():
    """Reject untrusted Host values when a host policy is configured."""
    if current_app.config.get("DLE_DESKTOP_MODE"):
        if _request_hostname() not in {"localhost", "127.0.0.1", "::1"}:
            return jsonify(
                {
                    "error": "Untrusted desktop host",
                    "success": False,
                    "code": "UNTRUSTED_DESKTOP_HOST",
                }
            ), 400
        return None

    trusted_hosts = _trusted_hosts()
    if not trusted_hosts:
        if current_app.config.get("DLE_PRODUCTION_MODE") and not current_app.config.get("TESTING"):
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


@core_bp.before_app_request
def validate_desktop_origin():
    """Reject browser origins that cannot belong to the packaged/local renderer."""
    if not current_app.config.get("DLE_DESKTOP_MODE"):
        return None

    origin = (request.headers.get("Origin") or "").strip().rstrip("/").lower()
    if not origin:
        return None

    allowed_origins = {
        "app://-",
        "app://dashboard",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    }
    if origin not in allowed_origins:
        return jsonify(
            {
                "error": "Untrusted desktop origin",
                "success": False,
                "code": "UNTRUSTED_DESKTOP_ORIGIN",
            }
        ), 403
    return None


def _redirect_target_url() -> str:
    canonical_origin = current_app.config.get("CANONICAL_EXTERNAL_ORIGIN") or os.environ.get("CANONICAL_EXTERNAL_ORIGIN")
    path = request.full_path if request.query_string else request.path
    if canonical_origin:
        return f"{canonical_origin.rstrip('/')}{path}"
    return request.url.replace("http://", "https://", 1)


@core_bp.after_app_request
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


@core_bp.after_app_request
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
@core_bp.before_app_request
def force_https():
    """Force HTTPS redirection in production environments."""
    is_prod = current_app.config.get("DLE_PRODUCTION_MODE")
    if current_app.config.get("DLE_DESKTOP_MODE"):
        return None
    if is_prod and not current_app.config.get("TESTING") and not request.is_secure:
        return redirect(_redirect_target_url(), code=301)

# SSO Configuration
from backend.auth.sso import configure_sso
from extensions import db, login_manager, csrf, migrate, cache, compress, cors
from models import User

# Initialize WebSockets
from backend.websocket import init_socketio


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


# Initialize Celery
from backend.celery_app import make_celery

# Exempt JSON API endpoints from CSRF (they use session auth or API keys)
# CSRF is still enforced on all HTML form submissions
from flask_wtf.csrf import CSRFError
from backend.security.api_csrf import is_api_csrf_enforced, validate_api_csrf_request
from backend.auth import api_decorators as auth_api_decorators
from backend.utils.error_normalization import normalize_public_error_message

# Single-mode / OS-level auth (auth deprecation Phase C, 2026-06-13): only the
# desktop Windows-identity endpoints remain. The former web-app auth routes
# (login/register/mfa-verify/sso-callback) were removed; their stale CSRF-exempt
# entries are dropped here.
CSRF_API_EXEMPT_PATH_PREFIXES = (
    "/api/v1/auth/desktop/challenge",
    "/api/v1/auth/desktop/auto-login",
)


def _request_uses_session_cookie() -> bool:
    return any(
        request.cookies.get(cookie_name)
        for cookie_name in ("session", "session_id", "remember_token")
    )


def _request_uses_stateless_auth() -> bool:
    auth_header = request.headers.get("Authorization", "")
    return bool(request.headers.get("X-API-Key") or auth_header.lower().startswith("bearer "))


def _request_uses_signed_desktop_auth() -> bool:
    desktop_auth, _ = auth_api_decorators.check_desktop_request_auth()
    return desktop_auth


def _is_trusted_origin_request() -> bool:
    trusted_origins = current_app.config.get("DLE_TRUSTED_CSRF_ORIGINS", set())
    origin_header = request.headers.get("Origin", "")
    if origin_header:
        return _normalize_origin(origin_header) in trusted_origins

    referer_header = request.headers.get("Referer", "")
    if referer_header:
        return _normalize_origin(referer_header) in trusted_origins

    return False


@core_bp.before_app_request
def csrf_for_forms_only():
    if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
        return None

    if current_app.config.get("TESTING") or os.environ.get("FLASK_ENV") == "testing":
        return None

    is_api_like_request = request.path.startswith("/api/") or request.path.startswith("/graphql")
    if is_api_like_request:
        if _request_uses_session_cookie() and not _request_uses_stateless_auth():
            if _request_uses_signed_desktop_auth():
                return None
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
@core_bp.app_errorhandler(CSRFError)
def handle_csrf_error(e):
    from flask import request
    if request.is_json or request.headers.get('Content-Type', '').startswith('application/json'):
        return jsonify({'error': 'CSRF token missing or invalid', 'success': False}), 400
    flash('Security token expired. Please try again.', 'danger')
    return redirect(request.url)

# Initialize Unified Middleware Stack (Hardened)
from backend.middleware import setup_middleware


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

def _should_auto_create_schema(app: Flask | None = None) -> bool:
    """Require explicit opt-in before mutating schema at process startup."""
    if app is None:
        return _env_bool("AUTO_CREATE_SCHEMA")
    return bool(app.config.get("DLE_INITIALIZE_SCHEMA"))


def _initialize_database_schema(app: Flask) -> None:
    """Initialize schema only when explicitly requested for disposable environments."""
    if not _should_auto_create_schema(app):
        logger.info("Startup schema auto-creation disabled; use 'flask db upgrade' or backend/init_db.py.")
        return

    if app.config.get("DLE_PRODUCTION_MODE"):
        raise RuntimeError(
            "AUTO_CREATE_SCHEMA=true is not allowed in production. "
            "Apply migrations explicitly with 'flask db upgrade' before startup."
        )

    with app.app_context():
        db.create_all()
        if app.config.get("DLE_DESKTOP_MODE") and app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"):
            from backend.desktop.schema_upgrade import apply_desktop_sqlite_upgrades

            upgraded_columns = apply_desktop_sqlite_upgrades(db.engine)
            if upgraded_columns:
                logger.info(
                    "Desktop SQLite schema upgraded with columns: %s",
                    ", ".join(upgraded_columns),
                )
        logger.warning(
            "Database tables auto-created because AUTO_CREATE_SCHEMA=true. "
            "Do not enable this in managed or production environments."
        )

# Multi-tenant Postgres RLS removed (single-mode / single-tenant deployment) — see
# docs/audits/DataLogicEngine_Auth_Deprecation_Plan.md (Phase D).

# MCP Routes moved to routes/mcp_routes.py (registered via routes package)

# AI Chat legacy blueprint removed (Superseded by LLM Gateway)

# KA Routes moved to routes/ka_routes.py (registered via routes package)

def _register_application_routes(app: Flask) -> None:
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
    app.register_blueprint(ukg_api, name='ukg_v1_legacy', url_prefix='/api/v1/ukg')

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
        logger.info("LLM Gateway API registered at /api/v1/gateway and /api/v1/admin")
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

    from backend.routes import register_routes

    register_routes(app)

def _initialize_storage_collections(app: Flask) -> dict[str, bool]:
    """Ensure ChromaDB named collections and object-storage buckets exist at startup."""
    result = {"chroma": False, "object_store": False}
    with app.app_context():
        try:
            from backend.storage.vector_store import initialize_collections
            initialize_collections()
            result["chroma"] = True
            logger.info("ChromaDB collections initialized")
            _maybe_start_db_c_indexing(app)
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("ChromaDB collection init skipped: %s", exc)

        try:
            from backend.storage.object_store import get_object_store
            store = get_object_store()
            for bucket in [
                "audit-logs",
                "simulation-artifacts",
                "deliverables",
                "graphs",
                "evaluation-data",
                "trace-exports",
            ]:
                if not store.create_bucket(bucket):
                    raise RuntimeError(f"required_object_bucket_unavailable:{bucket}")
            result["object_store"] = True
            logger.info("Object storage buckets initialized")
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Object storage bucket init skipped: %s", exc)
    if (
        app.config.get("DLE_PRODUCTION_MODE")
        or app.config.get("DLE_DATA_PLANE_DRIVER") == "podman"
    ) and not all(result.values()):
        raise RuntimeError("required_storage_initialization_failed")
    return result

def _chroma_collection_counts() -> dict:
    """Return ChromaDB collection counts for health and desktop IPC."""
    try:
        store = current_app.extensions.get("dle_vector_store")
        if store is None:
            return {}
        stats = store.list_collection_stats()
        return {
            name: int((data or {}).get("count", (data or {}).get("total_count", 0)) or 0)
            for name, data in stats.items()
        }
    except Exception as exc:  # pylint: disable=broad-except
        logger.debug("ChromaDB collection counts unavailable: %s", exc)
        return {}


def _redis_ping_ms() -> float | None:
    """Return Redis ping latency in milliseconds when Redis is reachable."""
    try:
        import redis

        redis_url = current_app.config.get("DLE_REDIS_URL") or os.environ.get(
            "REDIS_URL", "redis://127.0.0.1:6379/0"
        )
        client = redis.Redis.from_url(redis_url, socket_connect_timeout=0.5, socket_timeout=0.5)
        start = time.perf_counter()
        client.ping()
        return round((time.perf_counter() - start) * 1000, 3)
    except Exception as exc:  # pylint: disable=broad-except
        logger.debug("Redis ping unavailable: %s", exc)
        return None


def _object_store_bucket_stats() -> dict:
    """Return object-store bucket counts and byte totals for health and desktop IPC."""
    buckets = [
        "audit-logs",
        "simulation-artifacts",
        "deliverables",
        "graphs",
        "evaluation-data",
        "trace-exports",
    ]
    stats: dict[str, dict[str, int | str]] = {}
    try:
        store = current_app.extensions.get("dle_object_store")
        if store is None:
            raise RuntimeError("object_store_not_initialized")
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
        service = current_app.extensions.get("dle_unified_memory_service")
        if service is None:
            raise RuntimeError("memory_service_not_initialized")
        return service.stats()
    except Exception as exc:  # pylint: disable=broad-except
        logger.debug("Structured memory stats unavailable: %s", exc)
        return {
            "status": "unavailable",
            "memory_vertices": 0,
            "memory_edges": 0,
            "last_recall_timestamp": None,
        }


def _db_c_auto_index_enabled(app: Flask) -> bool:
    configured = app.config.get("DB_C_AUTO_INDEX_ON_STARTUP")
    if configured is not None:
        return configured.lower() in {"1", "true", "yes", "on"}
    if app.config.get("TESTING"):
        return False
    return bool(app.config.get("DLE_DESKTOP_MODE"))


def _run_db_c_indexing_background(app: Flask) -> None:
    """Run DB-C knowledge-node indexing inside an app context."""
    try:
        from scripts.index_knowledge_nodes import index_from_database

        with app.app_context():
            result = index_from_database()
        logger.info("DB-C knowledge_nodes background index complete: %s", result.to_dict())
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("DB-C knowledge_nodes background index failed: %s", exc)


def _maybe_start_db_c_indexing(app: Flask) -> None:
    """Trigger DB-C indexing when local desktop Chroma starts empty."""
    if not _db_c_auto_index_enabled(app):
        return
    counts = _chroma_collection_counts()
    if counts.get("knowledge_nodes", 0) > 0:
        return
    thread = Thread(
        target=_run_db_c_indexing_background,
        args=(app,),
        name="db-c-index-knowledge-nodes",
        daemon=True,
    )
    get_application_runtime(app).track_thread(thread)
    thread.start()


def _initialize_uskd_memory_graph(app: Flask) -> None:
    """Load the RAM-resident USKD graph from SQL rows, then Neo4j if available."""
    try:
        from backend.storage import get_graph_store, get_uskd_memory_graph

        with app.app_context():
            memory_graph = get_uskd_memory_graph()
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

@core_bp.route('/api/v1/csp-report', methods=['POST'])
@api_login_required
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

    secret_key_status = "set" if current_app.secret_key else "missing"
    environment = current_app.config.get("DLE_ENVIRONMENT", "production")
    return {
        "environment": environment,
        "secret_key": secret_key_status,
        "secret_source": current_app.config.get("DLE_SESSION_SECRET_SOURCE", "missing"),
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
    runtime_payload, _ = get_application_runtime().readiness()
    config_state = _config_health()
    database_state = _database_health()

    blockers = list(runtime_payload["blockers"])
    blocker_details = dict(runtime_payload.get("blocker_details", {}))
    if database_state.get("status") != "ok":
        blockers.append("database")
        blocker_details["database"] = "unavailable"
    if config_state.get("secret_key") == "missing":
        blockers.append("secret_key")
        blocker_details["secret_key"] = "missing"

    is_ready = not blockers
    status_code = 200 if is_ready else 503
    payload = {
        "status": "ready" if is_ready else "not_ready",
        "checks": {
            "runtime": runtime_payload["phase"],
            "database": database_state.get("status", "error"),
            "secret_key": config_state.get("secret_key", "missing"),
        },
        "blockers": blockers,
        "blocker_details": blocker_details,
        "correlation_id": _current_correlation_id(),
        "timestamp": datetime.now(UTC).isoformat(),
    }
    return payload, status_code


def _prometheus_metrics_payload() -> str:
    """Render low-cardinality Prometheus metrics in text exposition format."""
    metrics_snapshot = get_application_runtime().metrics.snapshot()
    uptime_seconds = max(0.0, time.time() - metrics_snapshot["started_at"])
    total_requests = metrics_snapshot["total"]
    inflight_requests = metrics_snapshot["inflight"]
    route_status_totals = metrics_snapshot["route_status_totals"]
    route_latency_ms = metrics_snapshot["route_latency_ms"]

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


@core_bp.route("/live", methods=["GET"])
def live() -> tuple:
    """Liveness endpoint: process is running."""
    return jsonify(
        {
            "status": "live",
            "service": "datalogicengine",
            "correlation_id": _current_correlation_id(),
            "timestamp": datetime.now(UTC).isoformat(),
        }
    ), 200


@core_bp.route("/ready", methods=["GET"])
def ready() -> tuple:
    """Readiness endpoint: app dependencies are operational."""
    payload, status_code = _readiness_payload()
    return jsonify(payload), status_code


@core_bp.route("/health", methods=["GET"])
def health() -> tuple:
    """Public-safe health endpoint without configuration or data-store details."""

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
        "service": "datalogicengine",
        "correlation_id": _current_correlation_id(),
        "timestamp": datetime.now(UTC).isoformat(),
    }

    return jsonify(payload), http_status


@core_bp.route("/api/v1/system/diagnostics/health", methods=["GET"])
@api_session_login_required
def health_diagnostics() -> tuple:
    """Authenticated desktop diagnostics separated from public health."""
    return jsonify(_diagnostics_summary()), 200


def _diagnostics_summary() -> dict:
    """Return local, authenticated, content-free diagnostic state."""
    from backend.observability.crash_reporting import crash_reporting_state

    runtime = get_application_runtime()
    metrics_snapshot = runtime.metrics.snapshot()
    crash_state = crash_reporting_state()
    init_error = crash_state.get("init_error")
    return {
        "schema_version": "dle.diagnostics.v1",
        "status": "ok",
        "runtime": runtime.capabilities(),
        "config": _config_health(),
        "database": _database_health(),
        "requests": {
            "total": metrics_snapshot["total"],
            "inflight": metrics_snapshot["inflight"],
            "uptime_seconds": max(0.0, time.time() - metrics_snapshot["started_at"]),
        },
        "logging": {
            "schema_version": "dle.log.v1",
            "format": "json",
            "app_max_bytes": 10 * 1024 * 1024,
            "app_backup_count": 5,
            "security_backup_count": 10,
            "audit_backup_count": 30,
            "redaction": "best_effort_redacted",
        },
        "external_telemetry": {
            "opted_in": bool(current_app.config.get("DLE_EXTERNAL_TELEMETRY_ENABLED")),
            "enabled": bool(crash_state.get("enabled")),
            "provider": crash_state.get("provider", "none"),
            "state_code": str(init_error).split(":", 1)[0] if init_error else None,
        },
        "support_bundle": {
            "schema_version": "dle.support-bundle.v1",
            "content_policy": "redacted_diagnostics_only",
            "user_content_included": False,
            "generic_reports_included": False,
            "preview_required": True,
            "encryption_available_via_cli": True,
        },
        "correlation_id": _current_correlation_id(),
        "timestamp": datetime.now(UTC).isoformat(),
    }


def _support_bundle_builder():
    from backend.observability.support_bundle import SupportBundleBuilder

    return SupportBundleBuilder(get_application_runtime().runtime_root)


def _support_bundle_options():
    from backend.observability.support_bundle import SupportBundleOptions

    return SupportBundleOptions(
        max_log_bytes=2_000_000,
        max_log_files=10,
        include_http=False,
        include_runtime_precheck=False,
    )


def _support_preview_fingerprint(preview: dict) -> str:
    import hashlib

    contract = [
        {
            "path": item.get("path"),
            "classification": item.get("classification"),
        }
        for item in preview.get("files", [])
    ]
    encoded = json.dumps(contract, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@core_bp.route("/api/v1/system/diagnostics/summary", methods=["GET"])
@api_session_login_required
def diagnostics_summary() -> tuple:
    """Return the owner-facing safe diagnostic contract."""
    return jsonify(_diagnostics_summary()), 200


@core_bp.route("/api/v1/system/diagnostics/support/preview", methods=["POST"])
@api_session_login_required
def support_bundle_preview() -> tuple:
    """Preview the exact allowlisted support-bundle file classes."""
    preview = _support_bundle_builder().preview(
        options=_support_bundle_options(),
        diagnostics=_diagnostics_summary(),
    )
    preview["preview_fingerprint"] = _support_preview_fingerprint(preview)
    return jsonify(preview), 200


@core_bp.route("/api/v1/system/diagnostics/support/export", methods=["POST"])
@api_session_login_required
def support_bundle_export() -> tuple:
    """Generate one bounded local bundle only after an explicit preview."""
    payload = request.get_json(silent=True) or {}
    if payload.get("confirm") is not True:
        return jsonify(
            {
                "success": False,
                "error": "Explicit support bundle confirmation is required",
                "code": "SUPPORT_BUNDLE_CONFIRMATION_REQUIRED",
            }
        ), 400
    preview = _support_bundle_builder().preview(
        options=_support_bundle_options(),
        diagnostics=_diagnostics_summary(),
    )
    expected_fingerprint = _support_preview_fingerprint(preview)
    if payload.get("preview_fingerprint") != expected_fingerprint:
        return jsonify(
            {
                "success": False,
                "error": "Support bundle preview is stale; review it again",
                "code": "SUPPORT_BUNDLE_PREVIEW_STALE",
            }
        ), 409

    output_dir = get_application_runtime().runtime_root / "support-bundles"
    result = _support_bundle_builder().export(
        output_dir,
        options=_support_bundle_options(),
        diagnostics=_diagnostics_summary(),
    )
    logger.info(
        "Redacted support bundle generated",
        extra={
            "event": "support_bundle.generated",
            "artifact_sha256": result["sha256"],
            "artifact_size_bytes": result["size_bytes"],
            "redaction_classification": "redacted_diagnostics",
        },
    )
    return jsonify(
        {
            "success": True,
            "artifact_name": Path(result["archive_path"]).name,
            "sidecar_name": Path(result["sidecar_path"]).name,
            "sha256": result["sha256"],
            "size_bytes": result["size_bytes"],
            "encrypted": result["encrypted"],
            "location": "application_support_bundles_directory",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    ), 201


@core_bp.route("/api/v1/system/capabilities", methods=["GET"])
@api_session_login_required
def system_capabilities() -> tuple:
    """Return authenticated, machine-readable runtime capability state."""
    return jsonify(
        {
            "status": "ok",
            "capabilities": get_application_runtime().capabilities(),
            "correlation_id": _current_correlation_id(),
            "timestamp": datetime.now(UTC).isoformat(),
        }
    ), 200


@core_bp.route("/api/v1/system/lifecycle/event", methods=["POST"])
@api_session_login_required
def system_lifecycle_event() -> tuple:
    """Accept signed main-process Windows lifecycle notifications."""
    from backend.auth.api_decorators import check_desktop_request_auth

    is_desktop_request, _user = check_desktop_request_auth()
    if not is_desktop_request:
        return jsonify(
            {
                "success": False,
                "error": "Desktop lifecycle authorization required",
                "code": "DESKTOP_LIFECYCLE_AUTH_REQUIRED",
            }
        ), 403
    payload = request.get_json(silent=True) or {}
    event = payload.get("event")
    try:
        get_application_runtime().handle_system_event(str(event or ""))
    except ValueError:
        return jsonify(
            {
                "success": False,
                "error": "Unsupported lifecycle event",
                "code": "UNSUPPORTED_LIFECYCLE_EVENT",
            }
        ), 400
    return jsonify({"success": True, "event": event}), 202


@core_bp.route("/health/cache", methods=["GET"])
@api_session_login_required
def health_cache() -> tuple:
    """Redis liveness check for QC validation."""
    from backend.storage.connection_manager import get_connection_manager
    ok = get_connection_manager().check_health("redis")
    status = "ok" if ok else "unavailable"
    return jsonify({"redis": status, "timestamp": datetime.now(UTC).isoformat()}), 200 if ok else 503


@core_bp.route("/metrics", methods=["GET"])
@api_session_login_required
def metrics() -> Response:
    """Canonical metrics endpoint for infrastructure scraping."""
    return Response(
        _prometheus_metrics_payload(),
        mimetype="text/plain; version=0.0.4; charset=utf-8",
    )

# Simulation API routes are registered via routes.register_routes()

@core_bp.route('/api-docs')
def api_docs():
    return render_template('api_docs.html')

@core_bp.route('/about')
def about():
    return render_template('about.html')

@core_bp.route('/contact')
def contact():
    return render_template('contact.html')

@core_bp.route('/terms')
def terms():
    return render_template('terms.html')

@core_bp.route('/privacy')
def privacy():
    return render_template('privacy.html')

# Note: /profile and /settings are defined in routes.py with more complete implementations

# Error handlers
@core_bp.app_errorhandler(404)
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

@core_bp.app_errorhandler(500)
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


@core_bp.app_errorhandler(Exception)
def unhandled_exception(e):
    """Fallback handler for non-HTTP uncaught exceptions."""
    if isinstance(e, HTTPException):
        return e
    return server_error(e)

@core_bp.app_errorhandler(403)
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

@core_bp.app_errorhandler(429)
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

def _env_bool(name: str, default: bool = False) -> bool:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _service_names(value) -> tuple[str, ...]:
    if not value:
        return ()
    if isinstance(value, str):
        values = value.split(",")
    else:
        values = value
    return tuple(sorted({str(item).strip() for item in values if str(item).strip()}))


def _configure_application(
    app: Flask,
    config_name=None,
    config_overrides: dict | None = None,
) -> None:
    """Load and validate configuration without starting process resources."""
    load_dotenv(override=False)
    apply_runtime_compatibility_patches()

    named_overrides = config_name if isinstance(config_name, dict) else {}
    profile = str(config_name or os.environ.get("FLASK_ENV", "production")).lower()
    testing = profile in {"test", "testing"}
    environment = "testing" if testing else str(os.environ.get("FLASK_ENV", profile)).lower()
    production = environment == "production" and not testing
    desktop = _env_bool("IS_DESKTOP_APP")
    database_url = os.environ.get("DATABASE_URL", "sqlite:///ukg_database.db")
    required_default = "postgresql,redis,neo4j,minio,chroma" if production else ""
    data_plane_driver = os.environ.get(
        "DLE_DATA_PLANE_DRIVER",
        "podman" if production else "legacy",
    ).strip().lower()
    data_plane_profile = os.environ.get(
        "DLE_DATA_PLANE_PROFILE",
        "production" if production else "qualification",
    ).strip().lower()

    app.config.from_mapping(
        ENV=environment,
        TESTING=testing,
        DLE_ENVIRONMENT=environment,
        APP_VERSION=os.environ.get("APP_VERSION", "0.1.1"),
        DLE_PRODUCTION_MODE=production,
        DLE_DESKTOP_MODE=desktop,
        DLE_START_RUNTIME=False,
        DLE_START_MANAGED_SERVICES=production or desktop,
        DLE_INITIALIZE_SCHEMA=_env_bool("AUTO_CREATE_SCHEMA"),
        DLE_INITIALIZE_STORES=not testing,
        DLE_START_BACKGROUND_WORKERS=not testing,
        DLE_REQUIRED_SERVICES=os.environ.get("DLE_REQUIRED_SERVICES", required_default),
        DLE_DATA_PLANE_DRIVER=data_plane_driver,
        DLE_DATA_PLANE_PROFILE=data_plane_profile,
        DLE_MCP_CONNECTORS_QUALIFIED=_env_bool("DLE_MCP_CONNECTORS_QUALIFIED"),
        DLE_EXTERNAL_TELEMETRY_ENABLED=_env_bool("DLE_EXTERNAL_TELEMETRY_ENABLED"),
        DLE_DATA_PLANE_LOCK_PATH=os.environ.get(
            "DLE_DATA_PLANE_LOCK_PATH",
            str(Path(__file__).resolve().parent / "deploy" / "internal-data-plane.candidate-lock.json"),
        ),
        DLE_RUNTIME_ROOT=os.environ.get("DLE_RUNTIME_ROOT"),
        DLE_CONFIGURE_LOGGING=not testing,
        DLE_SERVICE_START_TIMEOUT_SECONDS=float(
            os.environ.get("DLE_SERVICE_START_TIMEOUT_SECONDS", "30")
        ),
        DLE_SERVICE_STOP_TIMEOUT_SECONDS=float(
            os.environ.get("DLE_SERVICE_STOP_TIMEOUT_SECONDS", "15")
        ),
        DLE_DRAIN_TIMEOUT_SECONDS=float(
            os.environ.get("DLE_DRAIN_TIMEOUT_SECONDS", "5")
        ),
        DLE_FAIL_STARTUP_PHASE=os.environ.get("DLE_FAIL_STARTUP_PHASE", ""),
        DB_C_AUTO_INDEX_ON_STARTUP=os.environ.get("DB_C_AUTO_INDEX_ON_STARTUP"),
        PORT=int(os.environ.get("PORT", DEFAULT_PORT)),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE=os.environ.get(
            "SESSION_COOKIE_SAMESITE",
            "Strict" if production else "Lax",
        ),
        SESSION_COOKIE_SECURE=_env_bool("SESSION_COOKIE_SECURE", production),
        PERMANENT_SESSION_LIFETIME=timedelta(
            minutes=int(os.environ.get("SESSION_LIFETIME_MINUTES", 30))
        ),
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        RATELIMIT_DEFAULT=os.environ.get("GLOBAL_RATE_LIMIT", "200 per hour"),
        RATELIMIT_STORAGE_URI=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"),
        CORS_ORIGINS=os.environ.get("CORS_ORIGINS"),
        WTF_CSRF_CHECK_DEFAULT=False,
    )
    app.config.update(named_overrides)
    if config_overrides:
        app.config.update(config_overrides)

    # Overrides may select a test profile without using config_name.
    if app.config.get("TESTING"):
        app.config.update(
            DLE_ENVIRONMENT="testing",
            DLE_PRODUCTION_MODE=False,
            WTF_CSRF_ENABLED=False,
            RATELIMIT_ENABLED=False,
        )

    if app.config.get("DLE_PRODUCTION_MODE") and app.config.get("DLE_INITIALIZE_SCHEMA"):
        raise RuntimeError(
            "AUTO_CREATE_SCHEMA=true is not allowed in production. "
            "Apply versioned migrations before readiness."
        )

    database_url = str(app.config["SQLALCHEMY_DATABASE_URI"])
    if (
        app.config.get("DLE_PRODUCTION_MODE")
        and database_url.startswith("sqlite")
        and app.config.get("DLE_DATA_PLANE_DRIVER") != "podman"
    ):
        raise RuntimeError(
            "Production requires the supervised PostgreSQL data plane; SQLite fallback is disabled"
        )
    if database_url.startswith("sqlite"):
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
    else:
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_pre_ping": True,
            "pool_recycle": int(os.environ.get("DB_POOL_RECYCLE", 300)),
            "pool_size": int(os.environ.get("DB_POOL_SIZE", 20)),
            "max_overflow": int(os.environ.get("DB_POOL_MAX_OVERFLOW", 30)),
            "pool_timeout": int(os.environ.get("DB_POOL_TIMEOUT", 30)),
        }

    resolved_secret = app.config.get("SECRET_KEY")
    secret_source = "config" if resolved_secret else "missing"
    if not resolved_secret:
        resolved_secret, secret_source = resolve_runtime_secret(
            "SESSION_SECRET",
            required=False,
            production_mode=bool(app.config.get("DLE_PRODUCTION_MODE")),
        )
    if not resolved_secret:
        if app.config.get("DLE_PRODUCTION_MODE"):
            raise RuntimeError(
                "SESSION_SECRET must be configured before starting in production. "
                "Run: python scripts/generate_secrets.py"
            )
        resolved_secret = secrets.token_hex(32)
        secret_source = "ephemeral"
    app.secret_key = resolved_secret
    app.config["DLE_SESSION_SECRET_SOURCE"] = secret_source

    trust_proxy_headers = _env_bool("TRUST_PROXY_HEADERS")
    if app.config.get("DLE_DESKTOP_MODE") and trust_proxy_headers:
        raise RuntimeError("Proxy-provided Host/protocol headers are disabled for the desktop listener")
    if trust_proxy_headers:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)


def _configure_caching_and_extensions(app: Flask) -> None:
    """Initialize Flask extensions with per-application state."""
    redis_url = app.config.get("DLE_REDIS_URL") or os.environ.get(
        "REDIS_URL", "redis://localhost:6379/0"
    )
    use_redis = bool(app.config.get("DLE_PRODUCTION_MODE")) or (
        "localhost" not in redis_url or _env_bool("USE_REDIS")
    )
    app.config["DLE_USE_REDIS"] = use_redis
    if use_redis:
        app.config.update(
            CACHE_TYPE="RedisCache",
            CACHE_REDIS_URL=redis_url,
            CELERY_BROKER_URL=redis_url,
            CELERY_RESULT_BACKEND=redis_url,
        )
    else:
        app.config.update(
            CACHE_TYPE=app.config.get("CACHE_TYPE", "SimpleCache"),
            CELERY_BROKER_URL="memory://",
            CELERY_RESULT_BACKEND="db+sqlite:///results.db",
            CELERY_TASK_ALWAYS_EAGER=True,
        )

    explicit_rate_storage = os.environ.get("RATELIMIT_STORAGE_URI")
    if explicit_rate_storage:
        app.config["RATELIMIT_STORAGE_URI"] = explicit_rate_storage
    elif use_redis:
        app.config["RATELIMIT_STORAGE_URI"] = redis_url
    else:
        app.config["RATELIMIT_STORAGE_URI"] = "memory://"

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    cache.init_app(app)
    compress.init_app(app)
    init_socketio(app)
    configure_sso(app)

    cors_origins = _parse_cors_origins(app.config.get("CORS_ORIGINS"))
    if app.config.get("DLE_PRODUCTION_MODE") and not app.config.get("TESTING") and (
        not cors_origins or "*" in cors_origins
    ):
        raise RuntimeError("CORS_ORIGINS must be explicitly configured in production (wildcard is disallowed)")
    if not cors_origins:
        cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000", "app://-"]
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": cors_origins}},
        supports_credentials="*" not in cors_origins,
    )
    trusted_origins = {
        normalized
        for normalized in (_normalize_origin(origin) for origin in cors_origins)
        if normalized
    }
    trusted_origins.update({"app://-", "app://dashboard"})
    if not app.config.get("DLE_PRODUCTION_MODE"):
        trusted_origins.update(
            {
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:5000",
                "http://127.0.0.1:5000",
            }
        )
    app.config["DLE_TRUSTED_CSRF_ORIGINS"] = trusted_origins
    app.extensions["dle_celery"] = make_celery(app)
    setup_middleware(app)
    if use_redis:
        from backend.security.session_manager import configure_session_manager

        configure_session_manager(app)


def _configure_owned_security_services(app: Flask, runtime: ApplicationRuntime) -> None:
    """Create key and audit services under this application's runtime root."""
    from backend.security.audit_logger import AuditLogger
    from backend.security.encryption_manager import EncryptionManager

    audit_root = runtime.runtime_root / "logs" / "audit"
    immutable_root = runtime.runtime_root / "logs" / "audit_immutable"
    key_root = runtime.runtime_root / "security" / "keys"
    audit_logger = AuditLogger(
        {
            "log_dir": str(audit_root),
            "immutable_replica_dir": str(immutable_root),
        },
        auto_start=False,
    )
    encryption_manager = EncryptionManager(
        key_dir=str(key_root),
        audit_logger=audit_logger,
    )
    app.extensions["dle_audit_logger"] = audit_logger
    app.extensions["dle_encryption_manager"] = encryption_manager


def _configure_runtime_services(app: Flask, runtime: ApplicationRuntime) -> None:
    """Register every process-life service with the one runtime supervisor."""
    driver = str(app.config.get("DLE_DATA_PLANE_DRIVER", "legacy")).strip().lower()
    if driver == "podman":
        from backend.storage.connection_manager import ConnectionManager

        identity = InstallationIdentity.load_or_create(
            runtime.ownership.identity_path,
            version=str(app.config.get("APP_VERSION", "0.1.1")),
        )
        manager = PodmanDataPlaneManager(
            runtime_root=runtime.runtime_root,
            installation_id=identity.installation_id,
            profile=str(app.config.get("DLE_DATA_PLANE_PROFILE", "production")),
            lock_path=str(app.config["DLE_DATA_PLANE_LOCK_PATH"]),
            require_dpapi=not bool(app.config.get("TESTING")),
            command_timeout_seconds=float(
                app.config.get("DLE_SERVICE_START_TIMEOUT_SECONDS", 30.0)
            ),
        )
        settings = manager.connection_settings()
        app.extensions["dle_data_plane_manager"] = manager
        app.extensions["dle_connection_manager"] = ConnectionManager(
            runtime_root=runtime.runtime_root,
            data_plane=settings,
        )
        app.config["SQLALCHEMY_DATABASE_URI"] = settings["database_url"]
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_pre_ping": True,
            "pool_recycle": int(os.environ.get("DB_POOL_RECYCLE", 300)),
            "pool_size": int(os.environ.get("DB_POOL_SIZE", 20)),
            "max_overflow": int(os.environ.get("DB_POOL_MAX_OVERFLOW", 30)),
            "pool_timeout": int(os.environ.get("DB_POOL_TIMEOUT", 30)),
        }
        app.config["DLE_REDIS_URL"] = settings["redis_url"]
        app.config["DLE_NEO4J_URI"] = settings["neo4j_uri"]
        app.config["DLE_NEO4J_USER"] = settings["neo4j_user"]
        app.config["DLE_NEO4J_PASSWORD"] = settings["neo4j_password"]
        app.config["DLE_MANAGED_DATA_SERVICES"] = APP_SERVICE_KEYS

        required_services = set(_service_names(app.config.get("DLE_REQUIRED_SERVICES")))
        start_timeout = float(app.config.get("DLE_SERVICE_START_TIMEOUT_SECONDS", 30.0))
        stop_timeout = float(app.config.get("DLE_SERVICE_STOP_TIMEOUT_SECONDS", 15.0))
        for service in APP_SERVICE_KEYS:
            def supervised_podman_start(manager=manager, service=service):
                if manager.start_service(service):
                    return True
                reason = manager.last_failure_reasons.get(service, "start_failed")
                state = (
                    ServiceState.BLOCKED
                    if reason.startswith(("foreign_", "service_artifact_"))
                    else ServiceState.FAILED
                )
                return LifecycleResult(service, "start", False, state, reason)

            runtime.supervisor.register(
                service,
                required=service in required_services,
                start=supervised_podman_start,
                stop=lambda manager=manager, service=service: manager.stop_service(service),
                probe=lambda manager=manager, service=service: manager.probe_service(service),
                endpoint=manager.endpoint(service),
                expected_identity=manager.expected_identity(service),
                installed=True,
                start_timeout_seconds=start_timeout,
                stop_timeout_seconds=stop_timeout,
            )
        runtime.supervisor.register(
            "workers",
            installed=True,
            depends_on=tuple(sorted(required_services)),
            start_timeout_seconds=start_timeout,
            stop_timeout_seconds=stop_timeout,
        )
        runtime.supervisor.register(
            "api_gateway",
            installed=True,
            depends_on=("workers",),
            start_timeout_seconds=start_timeout,
            stop_timeout_seconds=stop_timeout,
        )
        return

    if app.config.get("DLE_PRODUCTION_MODE"):
        raise RuntimeError("production_requires_podman_data_plane")

    from backend.storage.database_manager import DatabaseLifecycleManager

    required_services = set(_service_names(app.config.get("DLE_REQUIRED_SERVICES")))
    app.config["DLE_MANAGED_DATA_SERVICES"] = ("postgresql", "redis", "neo4j")
    database_root = runtime.runtime_root / "databases"
    start_timeout = float(app.config.get("DLE_SERVICE_START_TIMEOUT_SECONDS", 30.0))
    stop_timeout = float(app.config.get("DLE_SERVICE_STOP_TIMEOUT_SECONDS", 15.0))
    manager = DatabaseLifecycleManager(
        base_dir=str(database_root),
        stop_timeout_seconds=stop_timeout,
        product_version=str(app.config.get("APP_VERSION", "0.1.1")),
    )
    app.extensions["dle_database_manager"] = manager

    start_callbacks = {
        "postgresql": manager.start_postgres,
        "redis": manager.start_redis,
        "neo4j": manager.start_neo4j,
    }
    for service, start_callback in start_callbacks.items():
        def supervised_start(service=service, start_callback=start_callback):
            success = start_callback()
            if success:
                return True
            reason = manager.last_failure_reasons.get(service, "start_failed")
            state = (
                ServiceState.BLOCKED
                if reason == "foreign_listener_on_configured_port"
                else ServiceState.FAILED
            )
            return LifecycleResult(service, "start", False, state, reason)

        service_dir = database_root / service
        runtime.supervisor.register(
            service,
            required=service in required_services,
            start=supervised_start,
            stop=lambda manager=manager, service=service: manager.stop_all().get(service, False),
            probe=lambda service=service: manager.probe_service(service),
            endpoint={
                "postgresql": f"127.0.0.1:{manager.pg_port}",
                "redis": f"127.0.0.1:{manager.redis_port}",
                "neo4j": f"127.0.0.1:{manager.neo4j_port}",
            }[service],
            expected_identity=manager.expected_identity(service),
            installed=service_dir.exists(),
            start_timeout_seconds=start_timeout,
            stop_timeout_seconds=stop_timeout,
        )

    # Phase 3 supplies the concrete MinIO/Chroma service adapters. Until then,
    # they are explicitly not installed and therefore block production readiness.
    for service in ("minio", "chroma"):
        runtime.supervisor.register(
            service,
            required=service in required_services,
            installed=False,
            start_timeout_seconds=start_timeout,
            stop_timeout_seconds=stop_timeout,
        )
    runtime.supervisor.register(
        "workers",
        installed=True,
        depends_on=tuple(sorted(required_services)),
        start_timeout_seconds=start_timeout,
        stop_timeout_seconds=stop_timeout,
    )
    runtime.supervisor.register(
        "api_gateway",
        installed=True,
        depends_on=("workers",),
        start_timeout_seconds=start_timeout,
        stop_timeout_seconds=stop_timeout,
    )


def _register_runtime_callbacks(app: Flask, runtime: ApplicationRuntime) -> None:
    def configure_phase(_runtime: ApplicationRuntime) -> None:
        validate_production_security(app)

    def paths_phase(active_runtime: ApplicationRuntime) -> None:
        active_runtime.runtime_root.mkdir(parents=True, exist_ok=True)
        if not app.config.get("TESTING"):
            from backend.security.windows_acl import (
                ensure_restricted_user_acl,
                verify_restricted_user_acl,
            )
            from backend.storage.data_at_rest import build_at_rest_report

            ensure_restricted_user_acl(
                active_runtime.runtime_root,
                required=bool(app.config.get("DLE_PRODUCTION_MODE")),
            )
            report = build_at_rest_report(
                active_runtime.runtime_root,
                acl_probe=verify_restricted_user_acl,
            )
            app.extensions["dle_at_rest_report"] = report
            if app.config.get("DLE_PRODUCTION_MODE") and not report["production_ready"]:
                raise RuntimeError("at_rest_protection_not_ready")

    def migration_phase(active_runtime: ApplicationRuntime) -> None:
        if app.config.get("DLE_DATA_PLANE_DRIVER") == "podman":
            from backend.storage.runtime_migrations import (
                run_managed_data_plane_migrations,
            )

            app.extensions["dle_migration_ledger"] = run_managed_data_plane_migrations(
                app,
                active_runtime,
            )
            pending_version = app.extensions.pop(
                "dle_pending_installation_version_upgrade",
                None,
            )
            if pending_version:
                active_runtime.ownership.record_completed_upgrade(pending_version)
            return
        _initialize_database_schema(app)

    def runtime_lock_phase(active_runtime: ApplicationRuntime) -> None:
        active_runtime.ownership.acquire()
        if (
            active_runtime.ownership.identity is not None
            and active_runtime.ownership.identity.version
            != str(app.config.get("APP_VERSION", "0.1.1"))
        ):
            from backend.storage.migration_inventory import SUPPORTED_UPGRADE_SOURCES

            installed_version = active_runtime.ownership.identity.version
            target_version = str(app.config.get("APP_VERSION", "0.1.1"))
            if (
                app.config.get("DLE_DATA_PLANE_DRIVER") == "podman"
                and installed_version in SUPPORTED_UPGRADE_SOURCES
            ):
                app.extensions["dle_pending_installation_version_upgrade"] = target_version
            else:
                raise RuntimeError("installation_version_mismatch")
        _configure_owned_security_services(app, active_runtime)
        if app.config.get("DLE_CONFIGURE_LOGGING"):
            app.config.setdefault("LOG_FILE", str(active_runtime.runtime_root / "logs" / "app.log"))
            app.config.setdefault("SECURITY_LOG_FILE", str(active_runtime.runtime_root / "logs" / "security.log"))
            app.config.setdefault("AUDIT_LOG_FILE", str(active_runtime.runtime_root / "logs" / "audit.log"))
            configure_structured_logging(app)

    def supervisor_phase(active_runtime: ApplicationRuntime) -> None:
        if not app.config.get("DLE_START_MANAGED_SERVICES"):
            return
        if app.config.get("DLE_DESKTOP_MODE"):
            from backend.storage.runtime_settings import get_auto_start_databases

            if not get_auto_start_databases():
                logger.info("Managed service auto-start is disabled by desktop settings")
                return
        for service in app.config.get("DLE_MANAGED_DATA_SERVICES", APP_SERVICE_KEYS):
            active_runtime.supervisor.start(service)

    def verification_phase(active_runtime: ApplicationRuntime) -> None:
        for service in app.config.get("DLE_MANAGED_DATA_SERVICES", APP_SERVICE_KEYS):
            state = active_runtime.supervisor.snapshot().get(service, {}).get("state")
            if state not in {"not_installed", "blocked"}:
                active_runtime.supervisor.probe(service)

    def stores_phase(_runtime: ApplicationRuntime) -> None:
        if app.config.get("DLE_INITIALIZE_STORES"):
            store_results = _initialize_storage_collections(app)
            if app.config.get("DLE_DATA_PLANE_DRIVER") == "podman":
                for service in ("chroma", "minio"):
                    _runtime.supervisor.probe(service)
            else:
                _runtime.supervisor.update_status(
                    "chroma",
                    ServiceState.READY if store_results["chroma"] else ServiceState.FAILED,
                    safe_reason=None if store_results["chroma"] else "store_initialization_failed",
                    observed_identity=f"datalogicengine:chroma:{_runtime.instance_id}",
                )
            _initialize_uskd_memory_graph(app)

    def workers_phase(_runtime: ApplicationRuntime) -> None:
        initialize_crash_reporting(
            enabled=bool(app.config.get("DLE_EXTERNAL_TELEMETRY_ENABLED")),
            dsn=os.environ.get("SENTRY_DSN"),
            environment=str(app.config.get("DLE_ENVIRONMENT", "production")),
            release=os.environ.get("APP_VERSION", "1.2.0"),
            traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            profiles_sample_rate=float(os.environ.get("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
        )
        if app.config.get("DLE_START_BACKGROUND_WORKERS"):
            app.extensions["dle_audit_logger"].start_log_rotation()
            from backend.ingestion.jobs import get_ingestion_job_runner
            from backend.llm_gateway.jobs import get_gateway_job_runner
            from backend.simulation.jobs import get_simulation_job_runner
            from backend.storage.materialization_dispatcher import (
                CrossStoreMaterializationWorker,
            )

            get_gateway_job_runner(app)
            get_ingestion_job_runner(app)
            get_simulation_job_runner(app)
            materializer = CrossStoreMaterializationWorker(app)
            app.extensions["dle_materialization_worker"] = materializer
            materializer.start(_runtime)

    def readiness_phase(active_runtime: ApplicationRuntime) -> None:
        if app.config.get("DLE_PRODUCTION_MODE") and active_runtime.supervisor.required_blockers():
            raise RuntimeError("required_services_not_ready")

    def shutdown_phase(_runtime: ApplicationRuntime) -> None:
        audit_logger = app.extensions.get("dle_audit_logger")
        if audit_logger is not None:
            try:
                audit_logger.stop_log_rotation()
            except Exception:
                logger.exception("Audit logger shutdown failed")
        memory_service = app.extensions.get("dle_unified_memory_service")
        if memory_service is not None:
            try:
                memory_service.save()
            except Exception:
                logger.exception("Memory checkpoint during shutdown failed")
        materializer = app.extensions.get("dle_materialization_worker")
        if materializer is not None:
            try:
                materializer.stop()
            except Exception:
                logger.exception("Cross-store materializer shutdown failed")
        gateway_job_runner = app.extensions.get("dle_gateway_job_runner")
        if gateway_job_runner is not None:
            try:
                gateway_job_runner.stop()
            except Exception:
                logger.exception("Gateway job runner shutdown failed")
        ingestion_job_runner = app.extensions.get("dle_ingestion_job_runner")
        if ingestion_job_runner is not None:
            try:
                ingestion_job_runner.stop()
            except Exception:
                logger.exception("Ingestion job runner shutdown failed")
        simulation_job_runner = app.extensions.get("dle_simulation_job_runner")
        if simulation_job_runner is not None:
            try:
                simulation_job_runner.stop()
            except Exception:
                logger.exception("Simulation job runner shutdown failed")
        graph_store = app.extensions.get("dle_graph_store")
        if graph_store is not None:
            try:
                graph_store.close()
            except Exception:
                logger.exception("Graph client shutdown failed")
        mcp_manager = app.extensions.get("dle_mcp_manager")
        if mcp_manager is not None:
            try:
                mcp_manager.shutdown()
            except Exception:
                logger.exception("MCP runtime shutdown failed")
        try:
            with app.app_context():
                db.session.remove()
                for engine in db.engines.values():
                    engine.dispose()
        finally:
            _runtime.ownership.release()

    runtime.on_phase(RuntimePhase.CONFIGURATION, configure_phase)
    runtime.on_phase(RuntimePhase.PATHS_AND_ACL, paths_phase)
    runtime.on_phase(RuntimePhase.RUNTIME_LOCK, runtime_lock_phase)
    runtime.on_phase(RuntimePhase.SERVICE_SUPERVISOR, supervisor_phase)
    runtime.on_phase(RuntimePhase.SERVICE_VERIFICATION, verification_phase)
    runtime.on_phase(RuntimePhase.MIGRATIONS, migration_phase)
    runtime.on_phase(RuntimePhase.STORES, stores_phase)
    runtime.on_phase(RuntimePhase.ROUTES_AND_WORKERS, workers_phase)
    runtime.on_phase(RuntimePhase.READINESS, readiness_phase)
    runtime.on_shutdown(shutdown_phase)


def create_app(
    config_name=None,
    config_overrides: dict | None = None,
    *,
    start_runtime: bool | None = None,
) -> Flask:
    """Build one isolated Flask application and its owned runtime state."""
    application = Flask(__name__)
    _configure_application(application, config_name, config_overrides)
    runtime = ApplicationRuntime(
        application,
        runtime_root=default_runtime_root(application),
        required_services=_service_names(application.config.get("DLE_REQUIRED_SERVICES")),
    )
    application.extensions["dle_runtime"] = runtime
    _configure_runtime_services(application, runtime)
    _configure_caching_and_extensions(application)
    application.register_blueprint(core_bp)
    _register_application_routes(application)
    _register_runtime_callbacks(application, runtime)

    should_start = application.config.get("DLE_START_RUNTIME") if start_runtime is None else start_runtime
    if should_start:
        runtime.start()
    return application


_default_app = None
_default_app_lock = Lock()


def _get_default_app() -> Flask:
    """Return the deprecated compatibility app without import-time construction."""
    global _default_app
    if _default_app is None:
        with _default_app_lock:
            if _default_app is None:
                testing = "pytest" in sys.modules
                _default_app = create_app(
                    "testing" if testing else None,
                    {
                        "DLE_INITIALIZE_SCHEMA": False,
                        "DLE_INITIALIZE_STORES": False if testing else not _env_bool("DLE_SKIP_STORE_INIT"),
                        "DLE_START_BACKGROUND_WORKERS": False if testing else True,
                    },
                    start_runtime=True,
                )
    return _default_app


# Compatibility only. Importing app.py no longer constructs an application; new
# code and every process entry point must call create_app explicitly.
app = LocalProxy(_get_default_app)
celery = LocalProxy(lambda: _get_default_app().extensions["dle_celery"])


if __name__ == '__main__':
    from backend.security.listener_policy import resolve_loopback_listener_host

    application = create_app(start_runtime=True)
    is_prod = bool(application.config.get("DLE_PRODUCTION_MODE"))
    debug_mode = False if is_prod else (
        application.config.get("DLE_ENVIRONMENT") == "development" or _env_bool("FLASK_DEBUG")
    )
    run_host = resolve_loopback_listener_host(os.environ.get('FLASK_RUN_HOST'))
    application.run(
        host=run_host,
        port=int(application.config.get("PORT", DEFAULT_PORT)),
        debug=debug_mode,
        use_reloader=False,
    )
