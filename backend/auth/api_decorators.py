from functools import wraps
from flask import jsonify, request, g
from flask_login import current_user
from models import ExternalAPIKey, User


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
    
    # 2. Check API Key Auth (header only, hashed ExternalAPIKey)
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

def api_admin_required(f):
    """Decorator to require admin privileges via session or API key principal."""
    @wraps(f)
    def api_admin_required_wrapper(*args, **kwargs):
        is_auth, principal = check_api_auth()
        if not is_auth:
            return jsonify({
                'status': 'error',
                'success': False,
                'message': 'Authentication required',
                'code': 'UNAUTHORIZED'
            }), 401
            
        if not getattr(principal, 'is_admin', False):
            return jsonify({
                'status': 'error',
                'success': False,
                'message': 'Admin privileges required',
                'code': 'FORBIDDEN'
            }), 403
        return f(*args, **kwargs)
        
    # Manually preserve function attributes to prevent Flask endpoint collisions
    try:
        api_admin_required_wrapper.__name__ = f.__name__
        api_admin_required_wrapper.__doc__ = f.__doc__
        api_admin_required_wrapper.__module__ = f.__module__
    except (AttributeError, TypeError):
        pass
        
    return api_admin_required_wrapper
