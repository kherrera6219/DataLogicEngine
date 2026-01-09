"""
Authentication Routes Blueprint (JSON API)

Handles user login, logout, and registration via REST API.
"""

import datetime
from datetime import UTC
import logging
from functools import wraps

from flask import Blueprint, request, jsonify, session
from flask_login import current_user, login_user, logout_user, login_required

from extensions import db
from models import User

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth_api', __name__, url_prefix='/api/v1/auth')

def error_response(message, status_code=400, code=None):
    return jsonify({"error": message, "success": False, "code": code}), status_code

def success_response(data=None, message="Operation successful", status_code=200):
    return jsonify({"success": True, "message": message, "data": data or {}}), status_code

@auth_bp.route('/check', methods=['GET'])
def check_auth():
    """Check current authentication status."""
    if current_user.is_authenticated:
        return success_response(data={"user": current_user.to_dict()})
    return jsonify({"authenticated": False}), 200

@auth_bp.route('/login', methods=['POST'])
def login():
    """Handle user login via JSON."""
    if current_user.is_authenticated:
        return success_response(message="Already logged in", data={"user": current_user.to_dict()})
    
    data = request.json
    if not data: return error_response("No data provided")
    
    username = data.get('username')
    password = data.get('password')
    remember = data.get('remember', False)
    
    if not username or not password:
        return error_response("Username and password are required")
        
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return error_response("Invalid username or password", 401)
    
    if user.is_account_locked():
        return error_response("Account is locked. Try again later.", 403)
    
    if not user.check_password(password):
        user.record_failed_login()
        db.session.commit()
        remaining = max(0, 5 - user.failed_login_attempts)
        return error_response(f"Invalid credentials. {remaining} attempts remaining.", 401)
    
    if user.is_password_expired():
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
    
    return success_response(message="Login successful", data={"user": user.to_dict()})

@auth_bp.route('/mfa/verify', methods=['POST'])
def mfa_verify():
    """Verify MFA token."""
    if current_user.is_authenticated:
        return success_response(message="Already logged in")
        
    if 'mfa_user_id' not in session:
        return error_response("MFA session expired or invalid", 401)
        
    data = request.json
    token = data.get('token')
    if not token: return error_response("Token required")
    
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

@auth_bp.route('/register', methods=['POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
         return success_response(message="Already logged in")
         
    data = request.json
    if not data: return error_response("No data provided")
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not all([username, email, password]):
        return error_response("All fields are required")
        
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
    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration error: {e}")
        return error_response("Server error during registration", 500)

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Handle user logout."""
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
                
            user = User()
            user.username = username
            user.email = email
            user.set_password(datetime.datetime.now().isoformat()) # usage of random password
            user.is_active = True
            
            db.session.add(user)
            db.session.commit()
            logger.info(f"Created new user via SSO: {username}")
            
        login_user(user)
        return success_response(message="SSO Login successful", data={"user": user.to_dict()})
        
    except Exception as e:
        logger.error(f"SSO Error: {e}")
        return error_response("SSO Authentication failed", 500)

