from functools import wraps
from flask import jsonify, current_app
from flask_login import current_user

def api_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required. Please log in.',
                'code': 'UNAUTHORIZED'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def api_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'status': 'error',
                'message': 'Authentication required',
                'code': 'UNAUTHORIZED'
            }), 401
        if not current_user.is_admin:
            return jsonify({
                'status': 'error',
                'message': 'Admin privileges required',
                'code': 'FORBIDDEN'
            }), 403
        return f(*args, **kwargs)
    return decorated_function
