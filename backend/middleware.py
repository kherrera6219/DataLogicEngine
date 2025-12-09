"""
Universal Knowledge Graph (UKG) System - API Middleware

This module provides middleware functions for the UKG API.
"""

import logging
from datetime import datetime
from functools import wraps
from flask import jsonify
from flask_login import current_user

logger = logging.getLogger(__name__)


def admin_required(f):
    """
    Decorator to require admin privileges for an endpoint.

    This decorator checks if the current user has admin privileges.
    Must be used after @login_required or @jwt_required decorators.

    Usage:
        @app.route('/admin/users')
        @login_required
        @admin_required
        def manage_users():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({
                'error': 'Authentication required',
                'message': 'You must be logged in to access this resource'
            }), 401

        if not current_user.is_admin:
            logger.warning(
                f"Unauthorized admin access attempt by user {current_user.id} "
                f"to endpoint {f.__name__}"
            )
            return jsonify({
                'error': 'Forbidden',
                'message': 'Admin privileges required to access this resource'
            }), 403

        return f(*args, **kwargs)
    return decorated_function

def api_response(f):
    """
    Decorator to standardize API responses.

    Automatically wraps the return value of the decorated function in a
    standard response format with success status, timestamp, and appropriate
    HTTP status code.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            result = f(*args, **kwargs)

            # If function returns a tuple of (data, status_code)
            if isinstance(result, tuple) and len(result) == 2:
                data, status_code = result
            else:
                data, status_code = result, 200

            # If data is a dict with an 'error' key, treat it as an error response
            if isinstance(data, dict) and 'error' in data:
                response = {
                    "success": False,
                    "message": data['error'],
                    "error_code": data.get('error_code', 'API_ERROR'),
                    "timestamp": datetime.utcnow().isoformat()
                }
                return jsonify(response), status_code

            # Otherwise, it's a success response
            response = {
                "success": True,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            return jsonify(response), status_code

        except Exception as e:
            logger.error(f"API error in {f.__name__}: {str(e)}")
            response = {
                "success": False,
                "message": str(e),
                "error_code": "INTERNAL_ERROR",
                "timestamp": datetime.utcnow().isoformat()
            }
            return jsonify(response), 500

    return decorated
"""
UKG Middleware

This module provides middleware functions for the Flask application.
"""

import logging
import uuid
from flask import request, g
from functools import wraps
from datetime import datetime

logger = logging.getLogger(__name__)

def request_id_middleware():
    """Middleware to assign a unique ID to each request."""
    request_id = request.headers.get('X-Request-ID')
    if not request_id:
        request_id = str(uuid.uuid4())
    g.request_id = request_id
    return request_id

def audit_request_middleware():
    """Middleware to audit API requests."""
    from backend.security import get_audit_logger
    
    def audit_request(response):
        try:
            # Get the audit logger
            audit_logger = get_audit_logger()
            
            # Get request details
            endpoint = request.endpoint
            method = request.method
            status_code = response.status_code
            ip_address = request.remote_addr
            user_id = getattr(g, 'user_id', None)
            request_id = getattr(g, 'request_id', str(uuid.uuid4()))
            
            # Log the API request
            audit_logger.log_api_request(
                request_id=request_id,
                user_id=user_id,
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                ip_address=ip_address
            )
            
        except Exception as e:
            logger.error(f"Error in audit middleware: {str(e)}")
            
        return response
    
    return audit_request

def rate_limit_middleware(limit=100, period=60):
    """
    Middleware for rate limiting.
    
    Args:
        limit: Maximum number of requests per period
        period: Time period in seconds
    """
    from backend.security import get_security_manager
    
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Get the security manager
            security_manager = get_security_manager()
            
            # Get client IP
            ip_address = request.remote_addr
            
            # Check rate limit
            if not security_manager.check_rate_limit(ip_address, limit, period):
                return {
                    "error": "Rate limit exceeded",
                    "status": "error",
                    "timestamp": datetime.now().isoformat()
                }, 429
                
            return f(*args, **kwargs)
        return wrapped
    return decorator

def security_headers_middleware():
    """Middleware to add security headers to responses."""
    
    def add_security_headers(response):
        try:
            # Add security headers
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:;"
            
        except Exception as e:
            logger.error(f"Error in security headers middleware: {str(e)}")
            
        return response
    
    return add_security_headers

def setup_middleware(app):
    """
    Set up all middleware for the application.
    
    Args:
        app: Flask application
    """
    # Register middleware
    app.before_request(request_id_middleware)
    app.after_request(audit_request_middleware())
    app.after_request(security_headers_middleware())
    
    logger.info("Middleware configured")
