"""
Backend middleware package for Universal Knowledge Graph system.

This package provides middleware components for request handling,
rate limiting, and other cross-cutting concerns.
"""

import logging
from functools import wraps
from flask import jsonify
from flask_login import current_user

from .request_limits import configure_request_limits

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


__all__ = ['configure_request_limits', 'admin_required']
