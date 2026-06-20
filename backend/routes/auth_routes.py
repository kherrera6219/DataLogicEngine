# ruff: noqa: E402
"""
Authentication Routes Blueprint (JSON API) — Desktop Local-First

Handles desktop Windows identity auth for the local-first Windows app.
Web-app patterns (username/password login, MFA, SSO, registration) have
been removed. Auth is managed by Windows identity + signed Electron
loopback (see backend/auth/api_decorators.py and
backend/security/desktop_local_auth.py).
"""

import logging
import os

from flask import Blueprint, request, jsonify, session, current_app
from flask_login import current_user, login_user

from extensions import db
from backend.auth.api_decorators import check_desktop_request_auth
from models import User
from backend.security.api_csrf import get_or_create_api_csrf_token
from backend.security.desktop_local_auth import (
    get_or_create_install_secret,
    issue_desktop_auth_challenge,
    verify_desktop_auth_challenge,
)

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth_api', __name__, url_prefix='/api/v1/auth')


def _is_loopback_request() -> bool:
    """Restrict desktop identity login to local loopback requests."""
    remote_addr = (request.remote_addr or "").strip().lower()
    return remote_addr in {"127.0.0.1", "::1", "localhost", ""}


def _is_windows_desktop_host() -> bool:
    return os.name == 'nt'


def _validate_desktop_preconditions():
    if not _is_windows_desktop_host():
        return error_response("Desktop auto-login only supported on Windows", 400)

    is_desktop_mode = os.environ.get("IS_DESKTOP_APP", "false").lower() == "true"
    if not is_desktop_mode:
        return error_response("Desktop auto-login is disabled outside desktop mode", 403)

    if not _is_loopback_request():
        return error_response("Desktop auto-login only allowed from local loopback", 403)

    desktop_header = (request.headers.get("X-DataLogic-Desktop") or "").lower()
    if desktop_header not in {"true", "1"}:
        return error_response("Desktop identity header required", 403)

    return None


def error_response(message, status_code=400, code=None):
    return jsonify({"error": message, "success": False, "code": code}), status_code


def success_response(data=None, message="Operation successful", status_code=200):
    return jsonify({"success": True, "message": message, "data": data or {}}), status_code


@auth_bp.route('/check', methods=['GET'])
def check_auth():
    """Check current authentication status."""
    if current_user.is_authenticated:
        return success_response(data={"user": current_user.to_dict(), "auth_mode": "session"})

    desktop_auth, desktop_user = check_desktop_request_auth()
    if desktop_auth and desktop_user:
        return success_response(data={
            "user": desktop_user.to_dict(),
            "auth_mode": "desktop",
        })

    return jsonify({"authenticated": False}), 200


@auth_bp.route('/csrf-token', methods=['GET'])
def csrf_token():
    """Issue CSRF token for session-authenticated API mutations."""
    token = get_or_create_api_csrf_token()
    response, status_code = success_response(
        data={"csrf_token": token},
        message="CSRF token issued",
    )
    response.set_cookie(
        "csrf_token",
        token,
        httponly=False,
        secure=bool(current_app.config.get("SESSION_COOKIE_SECURE", False)),
        samesite=current_app.config.get("SESSION_COOKIE_SAMESITE", "Lax"),
    )
    return response, status_code


@auth_bp.route('/desktop/challenge', methods=['POST'])
def desktop_auth_challenge():
    """Issue one-time desktop auth challenge nonce."""
    precondition_error = _validate_desktop_preconditions()
    if precondition_error:
        return precondition_error

    nonce, ttl_seconds = issue_desktop_auth_challenge(session)
    return success_response(
        data={"nonce": nonce, "expires_in_seconds": ttl_seconds},
        message="Desktop challenge issued",
    )


@auth_bp.route('/desktop/auto-login', methods=['POST'])
def desktop_auto_login():
    """
    Auto-login based on Windows System Identity.
    Primary auth entry point for the local-first desktop app.
    Resolves the Windows SID, auto-provisions a local user on first run,
    and establishes a Flask-Login session.
    """
    precondition_error = _validate_desktop_preconditions()
    if precondition_error:
        return precondition_error

    nonce = (request.headers.get("X-Desktop-Auth-Nonce") or "").strip()
    signature = (request.headers.get("X-Desktop-Auth-Signature") or "").strip()
    install_secret = get_or_create_install_secret()
    challenge_ok, challenge_error = verify_desktop_auth_challenge(
        session,
        nonce=nonce,
        signature=signature,
        install_secret=install_secret,
    )
    if not challenge_ok:
        return error_response(
            challenge_error or "Desktop auth challenge verification failed",
            403,
            code="DESKTOP_AUTH_CHALLENGE_FAILED",
        )

    from backend.auth.windows_identity import get_windows_user_identity
    try:
        identity = get_windows_user_identity()
    except Exception as e:
        logger.error("Identity resolution failed: %s", e)
        return error_response("Failed to resolve Windows identity", 500)

    if identity.get("is_fallback"):
        return error_response("Untrusted Windows fallback identity rejected", 403)

    sid = identity.get('sid')
    username = identity.get('username')

    if not sid:
        return error_response("Could not resolve Windows identity", 500)

    user = User.query.filter_by(sid=sid).first()

    if not user:
        bootstrap_owner_enabled = os.environ.get(
            "DESKTOP_AUTOLOGIN_BOOTSTRAP_OWNER", "false"
        ).lower() == "true"
        total_users = User.query.count()
        role = 'owner' if (total_users == 0 and bootstrap_owner_enabled) else 'user'

        base_username = username
        counter = 1
        username_candidate = username
        while User.query.filter_by(username=username_candidate).first():
            username_candidate = f"{base_username}_{counter}"
            counter += 1
        username = username_candidate

        import secrets
        user = User()
        user.username = username
        user.email = f"{username}@local.ukg"
        user.set_password(secrets.token_urlsafe(32) + "!A1a")
        user.sid = sid
        # `role` is retained only as an audit label below (first-run owner vs.
        # subsequent user); it is no longer stored on User (single-mode, Phase E).

        db.session.add(user)
        db.session.commit()

        from models import AuditLog
        audit = AuditLog(
            windows_sid=sid,
            user_id=user.id,
            action="FIRST_RUN_REGISTRATION" if role == 'owner' else "USER_AUTO_REGISTRATION",
            details=f"User registered with role: {role}"
        )
        db.session.add(audit)
        db.session.commit()

        logger.info(
            "Auto-registered Windows user=%s role=%s bootstrap_owner_enabled=%s",
            username, role, bootstrap_owner_enabled,
        )

    login_user(user, remember=True)
    return success_response(message="Desktop auto-login successful", data={"user": user.to_dict()})
