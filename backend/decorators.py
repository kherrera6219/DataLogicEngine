"""
Custom decorators for the UKG application.

This module provides reusable decorators for access control and other cross-cutting concerns.
"""

from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user, login_required


def admin_required(f):
    """
    Decorator that requires the current user to be an admin.
    
    Must be used after @login_required to ensure user is authenticated.
    Redirects to dashboard with error message if user is not an admin.
    
    Usage:
        @app.route('/admin/users')
        @login_required
        @admin_required
        def admin_users():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*roles):
    """
    Decorator that requires the current user to have one of the specified roles.
    
    Args:
        *roles: Variable number of role names that are allowed access
        
    Usage:
        @app.route('/moderator/panel')
        @login_required
        @role_required('admin', 'moderator')
        def moderator_panel():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            user_role = getattr(current_user, 'role', None)
            if user_role not in roles:
                flash('Access denied. Insufficient privileges.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def api_key_required(f):
    """
    Decorator that requires a valid API key for API endpoints.
    
    Checks for API key in approved headers only.
    Returns 401 if no valid key is provided.
    
    Usage:
        @app.route('/api/v1/data')
        @api_key_required
        def get_data():
            ...
    """
    from flask import request, jsonify
    from models import ExternalAPIKey
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            auth_header = request.headers.get('Authorization', '')
            if auth_header.lower().startswith('bearer '):
                api_key = auth_header.split(' ', 1)[1].strip()
        
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        if not str(api_key).startswith('ukg_'):
            return jsonify({'error': 'Invalid or inactive API key'}), 401

        key_record = ExternalAPIKey.verify_key(str(api_key))
        if not key_record:
            return jsonify({'error': 'Invalid or inactive API key'}), 401
        
        return f(*args, **kwargs)
    return decorated_function
