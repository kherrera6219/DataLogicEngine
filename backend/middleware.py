
from flask import request, jsonify
from functools import wraps
import os

def require_replit_auth(f):
    """Middleware to require Replit authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.headers.get('X-Replit-User-Id')
        username = request.headers.get('X-Replit-User-Name')
        
        if not user_id or not username:
            return jsonify({'error': 'Not authenticated with Replit'}), 401
            
        # Add user info to request for access in the route
        request.replit_user = {
            'id': user_id,
            'username': username,
            'roles': request.headers.get('X-Replit-User-Roles', '')
        }
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Middleware to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_jwt_extended import get_jwt_identity
        from .models import User
        
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
            
        return f(*args, **kwargs)
    return decorated_function

def log_request_info(app):
    """Middleware to log request information"""
    @app.before_request
    def before_request():
        if app.debug:
            app.logger.info(f"Request: {request.method} {request.path}")
