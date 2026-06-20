from functools import wraps
import logging
import os

from flask import jsonify, request, g
from flask_login import current_user
from extensions import db
from models import ExternalAPIKey, User
from backend.security.desktop_local_auth import (
    get_or_create_install_secret,
    verify_desktop_request_signature,
)

logger = logging.getLogger(__name__)


def _is_loopback_request() -> bool:
    remote_addr = (request.remote_addr or "").strip().lower()
    return remote_addr in {"127.0.0.1", "::1", "localhost", ""}


def _is_desktop_mode() -> bool:
    return os.environ.get("IS_DESKTOP_APP", "false").lower() == "true"


def _desktop_header_present() -> bool:
    return (request.headers.get("X-DataLogic-Desktop") or "").strip().lower() in {"true", "1"}


def _get_or_create_desktop_user() -> User:
    from backend.auth.windows_identity import get_windows_user_identity

    try:
        identity = get_windows_user_identity()
    except Exception as exc:
        # In production desktop mode, windows_identity raises RuntimeError when the
        # Windows SID cannot be resolved. Re-raise here so the caller receives a
        # clean failure rather than silently creating a user from an env-var fallback.
        if _is_desktop_mode():
            logger.error("Desktop identity resolution failed in production mode: %s", exc)
            raise
        # Dev/test only: use env-var fallback identity.
        username = os.environ.get("USERNAME") or "desktop_user"
        logger.warning(
            "Falling back to env-var identity (dev/test only): username=%s", username
        )
        identity = {
            "username": username,
            "sid": f"desktop-local:{username}",
            "is_fallback": True,
        }

    sid = str(identity.get("sid") or "").strip()
    username = str(identity.get("username") or "desktop_user").strip() or "desktop_user"
    if not sid:
        sid = f"desktop-local:{username}"

    user = User.query.filter_by(sid=sid).first()
    if user:
        return user

    import secrets

    base_username = username
    username_candidate = base_username
    counter = 1
    while User.query.filter_by(username=username_candidate).first():
        username_candidate = f"{base_username}_{counter}"
        counter += 1

    user = User()
    user.username = username_candidate
    user.email = f"{username_candidate}@local.ukg"
    user.set_password(secrets.token_urlsafe(32) + "!A1a")
    user.sid = sid
    db.session.add(user)
    db.session.commit()
    return user


def check_desktop_request_auth():
    """Check signed Electron loopback auth for packaged desktop requests."""
    if not (_is_desktop_mode() and _is_loopback_request() and _desktop_header_present()):
        return False, None

    timestamp = (request.headers.get("X-Desktop-Auth-Timestamp") or "").strip()
    signature = (request.headers.get("X-Desktop-Auth-Request-Signature") or "").strip()
    install_secret = get_or_create_install_secret()
    is_valid, _ = verify_desktop_request_signature(
        method=request.method,
        full_path=request.full_path,
        timestamp=timestamp,
        signature=signature,
        install_secret=install_secret,
    )
    if not is_valid:
        return False, None

    user = _get_or_create_desktop_user()
    g.auth_user = user
    g.auth_mode = "desktop"
    return True, user


def _extract_api_key() -> str | None:
    """Extract API key from approved headers only."""
    header_key = request.headers.get('X-API-Key')
    if header_key:
        return header_key.strip()

    auth_header = request.headers.get('Authorization', '')
    if auth_header.lower().startswith('bearer '):
        return auth_header.split(' ', 1)[1].strip()
    return None


def _is_user_active(user: User) -> bool:
    """Support both `active` and Flask-Login `is_active` styles."""
    active_flag = bool(getattr(user, 'active', True))
    login_flag = bool(getattr(user, 'is_active', True))
    return active_flag and login_flag


def check_api_auth():
    """Check if the request is authenticated via session or API key."""
    # 1. Check Session Auth
    if current_user.is_authenticated:
        g.auth_user = current_user
        g.auth_mode = "session"
        return True, current_user

    # 2. Check signed desktop loopback auth
    desktop_auth, desktop_user = check_desktop_request_auth()
    if desktop_auth:
        return True, desktop_user

    # 3. Check API Key Auth (header only, hashed ExternalAPIKey)
    api_key = _extract_api_key()
    if api_key and api_key.startswith("ukg_"):
        key_record = ExternalAPIKey.verify_key(api_key)
        if not key_record:
            return False, None

        user = User.query.get(key_record.user_id)
        if not user or not _is_user_active(user):
            return False, None

        g.auth_user = user
        g.auth_mode = "api_key"
        g.external_api_key = key_record
        return True, user

    return False, None


def api_login_required(f):
    """Decorator to require authentication via session or API key."""
    @wraps(f)
    def api_login_required_wrapper(*args, **kwargs):
        is_auth, _ = check_api_auth()
        if not is_auth:
            return jsonify({
                'status': 'error',
                'success': False,
                'message': 'Authentication required. Please provide a valid session or API key.',
                'code': 'UNAUTHORIZED'
            }), 401
        return f(*args, **kwargs)

    # Manually preserve function attributes to prevent Flask endpoint collisions
    try:
        api_login_required_wrapper.__name__ = f.__name__
        api_login_required_wrapper.__doc__ = f.__doc__
        api_login_required_wrapper.__module__ = f.__module__
    except (AttributeError, TypeError):
        pass

    return api_login_required_wrapper


def api_session_login_required(f):
    """Decorator to require an authenticated Flask session or valid desktop auth."""
    @wraps(f)
    def api_session_login_required_wrapper(*args, **kwargs):
        if current_user.is_authenticated:
            g.auth_user = current_user
            g.auth_mode = "session"
            return f(*args, **kwargs)

        desktop_auth, desktop_user = check_desktop_request_auth()
        if desktop_auth:
            g.auth_user = desktop_user
            g.auth_mode = "desktop"
            return f(*args, **kwargs)

        # Neither session nor desktop auth succeeded.
        return jsonify({
            'status': 'error',
            'success': False,
            'message': 'Authentication required. Please log in with an active session.',
            'code': 'UNAUTHORIZED'
        }), 401

    try:
        api_session_login_required_wrapper.__name__ = f.__name__
        api_session_login_required_wrapper.__doc__ = f.__doc__
        api_session_login_required_wrapper.__module__ = f.__module__
    except (AttributeError, TypeError):
        pass

    return api_session_login_required_wrapper


# Single-mode / OS-level auth (auth deprecation Phase B, 2026-06-13): there is no
# admin vs. non-admin distinction — the one OS user is the owner with full access.
# `api_admin_required` is retained as an alias of `api_login_required` so existing
# call sites keep working without churn. Remove the alias + call sites in a later pass.
api_admin_required = api_login_required


def current_user_is_owner() -> bool:
    """Single-mode authorization: the one authenticated OS user is the owner.

    Multi-user roles/admin were removed (auth-deprecation Phase E), so admin-gated
    endpoints — already protected by login decorators — grant full access to the
    authenticated owner. Centralised here so the remaining "is this user an admin?"
    checks read intentionally and there is one place to change if a multi-user model
    is ever reintroduced.
    """
    return True
