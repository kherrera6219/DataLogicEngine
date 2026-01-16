from functools import wraps
from flask import jsonify, current_app, request
from flask_login import current_user
from models import APIKey

def check_api_auth():
    """Check if the request is authenticated via session or API key."""
    # 1. Check Session Auth
    if current_user.is_authenticated:
        return True, current_user
    
    # 2. Check API Key Auth
    api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
    if api_key:
        key_record = APIKey.query.filter_by(key=api_key, is_active=True).first()
        if key_record:
            # We don't have a 'user' for API keys in the current model, 
            # but we can return the record or True
            return True, key_record
            
    return False, None

def api_login_required(f):
    """Decorator to require authentication via session or API key."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        is_auth, _ = check_api_auth()
        if not is_auth:
            return jsonify({
                'status': 'error',
                'success': False,
                'message': 'Authentication required. Please provide a valid session or API key.',
                'code': 'UNAUTHORIZED'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def api_admin_required(f):
    """Decorator to require admin privileges (only via session for now)."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'status': 'error',
                'success': False,
                'message': 'Authentication required',
                'code': 'UNAUTHORIZED'
            }), 401
            
        if not getattr(current_user, 'is_admin', False):
            return jsonify({
                'status': 'error',
                'success': False,
                'message': 'Admin privileges required',
                'code': 'FORBIDDEN'
            }), 403
        return f(*args, **kwargs)
    return decorated_function
