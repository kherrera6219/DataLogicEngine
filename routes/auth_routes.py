# ruff: noqa: E402
"""
Authentication Routes Blueprint (JSON API)

Handles user login, logout, and registration via REST API.
"""

import datetime
from datetime import UTC
import logging
import os

from flask import Blueprint, request, jsonify, session, current_app
from flask_login import current_user, login_user, logout_user

from extensions import db
from backend.auth.api_decorators import api_session_login_required, check_desktop_request_auth
from models import User
from backend.schemas.auth_schemas import LoginRequest, RegisterRequest, TokenRequest
from backend.utils.request_validation import validate_pydantic_payload
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
    if remote_addr in {"127.0.0.1", "::1", "localhost", ""}:
        return True
    return False


def _validate_desktop_preconditions():
    if os.name != 'nt':
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
        mfa_verified = session.get('mfa_verified', False) if current_user.mfa_enabled else True
        return success_response(data={
            "user": current_user.to_dict(),
            "mfa_verified": mfa_verified
        })

    desktop_auth, desktop_user = check_desktop_request_auth()
    if desktop_auth and desktop_user:
        return success_response(data={
            "user": desktop_user.to_dict(),
            "mfa_verified": True,
            "auth_mode": "desktop",
        })

    return jsonify({"authenticated": False}), 200

@auth_bp.route('/login', methods=['POST'])
def login():
    """Handle user login via JSON."""
    if current_user.is_authenticated:
        return success_response(message="Already logged in", data={"user": current_user.to_dict()})

    validated, validation_error_response = validate_pydantic_payload(
        LoginRequest,
        request.get_json(silent=True),
    )
    if validation_error_response:
        return validation_error_response

    username = validated.username if validated else ""
    password = validated.password if validated else ""
    remember = bool(validated.remember) if validated else False
        
    user = User.query.filter_by(username=username).first()
    
    if not user:
        logger.warning("Login failed: user not found for username=%s", username)
        return error_response("Invalid username or password", 401)
    
    if user.is_account_locked():
        logger.warning("Login blocked: account locked for username=%s", username)
        return error_response("Account is locked. Try again later.", 403)
    
    if not user.check_password(password):
        logger.warning("Login failed: bad password for username=%s", username)
        user.record_failed_login()
        db.session.commit()
        remaining = max(0, 5 - user.failed_login_attempts)
        return error_response(f"Invalid credentials. {remaining} attempts remaining.", 401)
    
    if user.is_password_expired():
        logger.warning("Login blocked: password expired for username=%s", username)
        return error_response("Password expired", 403, code="PASSWORD_EXPIRED")
    
    # MFA Check
    if user.mfa_enabled:
        session['mfa_user_id'] = user.id
        session['mfa_remember'] = remember
        return success_response(message="MFA required", data={"mfa_required": True}, status_code=202)
    
    # Enforce MFA for Admins (simplified flow: require setup if not enabled)
    if user.is_admin and not user.mfa_enabled:
        # For API, we might block login until MFA is set up. 
        # But for now, we'll allow login but flag it in response
        pass 

    user.record_successful_login()
    login_user(user, remember=remember)
    db.session.commit()
    logger.info("Login successful for username=%s user_id=%s", username, user.id)
    
    return success_response(message="Login successful", data={"user": user.to_dict()})

@auth_bp.route('/mfa/verify', methods=['POST'])
def mfa_verify():
    """Verify MFA token."""
    if current_user.is_authenticated:
        return success_response(message="Already logged in")
        
    if 'mfa_user_id' not in session:
        return error_response("MFA session expired or invalid", 401)
        
    validated, validation_error_response = validate_pydantic_payload(
        TokenRequest,
        request.get_json(silent=True),
    )
    if validation_error_response:
        return validation_error_response
    token = validated.token if validated else ""
    
    user = User.query.get(session['mfa_user_id'])
    
    if not user or not user.verify_totp(token):
        return error_response("Invalid MFA token", 401)
        
    # Success
    user.record_successful_login()
    remember = session.get('mfa_remember', False)
    login_user(user, remember=remember)
    db.session.commit()
    
    # Cleanup
    session.pop('mfa_user_id', None)
    session.pop('mfa_remember', None)
    
    return success_response(message="MFA verified", data={"user": user.to_dict()})

@auth_bp.route('/mfa/setup', methods=['POST'])
@api_session_login_required
def mfa_setup():
    """Initiate MFA setup."""
    from backend.security.mfa import MFAManager
    secret, qr_code, backup_codes = MFAManager.setup_mfa(current_user.username)
    
    # Store temporary secret in session until confirmed
    session['mfa_setup_secret'] = secret
    
    return success_response(data={
        "qr_code": qr_code,
        "backup_codes": backup_codes,
        "secret": secret
    })

@auth_bp.route('/mfa/confirm', methods=['POST'])
@api_session_login_required
def mfa_confirm():
    """Confirm and enable MFA."""
    validated, validation_error_response = validate_pydantic_payload(
        TokenRequest,
        request.get_json(silent=True),
    )
    if validation_error_response:
        return validation_error_response
    token = validated.token if validated else ""
    secret = session.get('mfa_setup_secret')
    
    if not secret or not token:
        return error_response("Token and setup session required")
        
    from backend.security.mfa import MFAManager
    if not MFAManager.validate_mfa_setup(secret, token):
        return error_response("Invalid verification token", 401)
        
    # Enable MFA for user
    current_user.mfa_enabled = True
    current_user.mfa_secret = secret
    # backup_codes should be stored securely too if passed back
    db.session.commit()
    
    session.pop('mfa_setup_secret', None)
    session['mfa_verified'] = True # Mark as verified for current session
    
    return success_response(message="MFA successfully enabled")
    
@auth_bp.route('/step-up', methods=['POST'])
@api_session_login_required
def step_up_verify():
    """
    Verify MFA token for Step-Up Authentication (Sudo Mode).
    Sets 'last_sudo_time' in session on success.
    """
    from datetime import datetime
    
    # If user doesn't have MFA enabled, step-up is just password re-verify
    # But for "Exceeding Standards", we enforce MFA/OTP even for step-up
    # If not enabled, they must enable it first.
    if not current_user.mfa_enabled:
        return error_response("MFA must be enabled for this action", 403, code="MFA_REQUIRED")

    validated, validation_error_response = validate_pydantic_payload(
        TokenRequest,
        request.get_json(silent=True),
    )
    if validation_error_response:
        return validation_error_response
    token = validated.token if validated else ""

    # Just verify the token against the user's secret
    if not current_user.verify_totp(token):
        return error_response("Invalid authentication code", 401)
        
    # Success - Update session
    session['last_sudo_time'] = datetime.now(UTC).isoformat()
    logger.info(f"Step-Up auth successful for user {current_user.id}")
    
    return success_response(message="Identity verified")

@auth_bp.route('/register', methods=['POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
         return success_response(message="Already logged in")
         
    validated, validation_error_response = validate_pydantic_payload(
        RegisterRequest,
        request.get_json(silent=True),
    )
    if validation_error_response:
        return validation_error_response

    username = validated.username if validated else ""
    email = str(validated.email) if validated else ""
    password = validated.password if validated else ""
        
    if User.query.filter_by(username=username).first():
        return error_response("Username taken", 409)
        
    if User.query.filter_by(email=email).first():
        return error_response("Email registered", 409)
        
    try:
        user = User()
        user.username = username
        user.email = email
        user.set_password(password)
        # Default role is 'user'
        
        db.session.add(user)
        db.session.commit()
        
        return success_response(message="Registration successful", status_code=201)
    except ValueError as e:
        db.session.rollback()
        return error_response(str(e), 400)
    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration error: {e}")
        return error_response("Server error during registration", 500)

@auth_bp.route('/logout', methods=['POST'])
@api_session_login_required
def logout():
    """Handle user logout."""
    if os.environ.get("IS_DESKTOP_APP", "false").lower() == "true":
        return success_response(message="Desktop session is managed by Windows")

    logout_user()
    return success_response(message="Logged out")

# SSO Routes
from backend.auth.sso import login_sso, handle_sso_callback

@auth_bp.route('/login/sso', methods=['GET'])
def sso_login_route():
    """Initiate SSO Login."""
    return login_sso()

@auth_bp.route('/callback/sso', methods=['GET'])
def sso_callback_route():
    """Handle SSO Callback."""
    try:
        user_info = handle_sso_callback()
        
        email = user_info.get('email') or user_info.get('preferred_username')
        if not email:
            return error_response("No email provided by Identity Provider", 400)
            
        # Find or create user
        user = User.query.filter_by(email=email).first()
        if not user:
            # Auto-register new user from SSO
            username = email.split('@')[0]
            # Ensure unique username
            if User.query.filter_by(username=username).first():
                username = f"{username}_{datetime.datetime.now().strftime('%M%S')}"
                
            import secrets
            user = User()
            user.username = username
            user.email = email
            user.set_password(secrets.token_urlsafe(32)) # Secure random password for SSO fallback
            user.is_active = True
            
            db.session.add(user)
            db.session.commit()
            logger.info(f"Created new user via SSO: {username}")
            
        login_user(user)
        return success_response(message="SSO Login successful", data={"user": user.to_dict()})
        
    except Exception as e:
        logger.error(f"SSO Error: {e}")
        return error_response("SSO Authentication failed", 500)

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
        data={
            "nonce": nonce,
            "expires_in_seconds": ttl_seconds,
        },
        message="Desktop challenge issued",
    )


@auth_bp.route('/desktop/auto-login', methods=['POST'])
def desktop_auto_login():
    """
    Auto-login based on Windows System Identity.
    Used for 'Zero-Config' desktop experience.
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
        logger.error(f"Identity resolution failed: {e}")
        return error_response("Failed to resolve Windows identity", 500)

    if identity.get("is_fallback"):
        return error_response("Untrusted Windows fallback identity rejected", 403)
        
    sid = identity.get('sid')
    username = identity.get('username')
    
    if not sid:
        return error_response("Could not resolve Windows identity", 500)
    
    # Check if user exists by Windows SID
    user = User.query.filter_by(sid=sid).first()
    
    if not user:
        # Optional bootstrap path for controlled first-run installs.
        bootstrap_owner_enabled = os.environ.get(
            "DESKTOP_AUTOLOGIN_BOOTSTRAP_OWNER", "false"
        ).lower() == "true"
        total_users = User.query.count()
        role = 'owner' if (total_users == 0 and bootstrap_owner_enabled) else 'user'
        
        # Ensure unique username
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
        # Ensure password meets security requirements (length, case, digit, special)
        temp_password = secrets.token_urlsafe(32) + "!A1a"
        user.set_password(temp_password)
        user.sid = sid
        user.role = role
        user.is_admin = (role == 'owner')
        
        db.session.add(user)
        db.session.commit()
        
        # Audit registration
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
            username,
            role,
            bootstrap_owner_enabled,
        )
    
    login_user(user, remember=True)
    return success_response(message="Desktop auto-login successful", data={"user": user.to_dict()})


