"""
Backend middleware package for Universal Knowledge Graph system.

This package provides middleware components for request handling,
rate limiting, and other cross-cutting concerns.
"""

from functools import wraps
from flask import jsonify
import logging

from .request_limits import configure_request_limits

logger = logging.getLogger(__name__)


def api_response(f):
    """Decorator to standardize API responses with proper JSON formatting.
    
    Handles:
    - Plain dict returns (wrapped in success response)
    - (dict, status_code) tuples
    - Flask Response objects (passed through unchanged)
    - Exceptions (wrapped in error response)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            from flask import Response
            result = f(*args, **kwargs)
            
            if isinstance(result, Response):
                return result
            
            if isinstance(result, tuple):
                if len(result) == 3:
                    return result
                elif len(result) == 2:
                    data, status_code = result
                else:
                    data = result
                    status_code = 200
            else:
                data = result
                status_code = 200
            
            if isinstance(data, dict) and 'error' in data:
                return jsonify({
                    'success': False,
                    'error': data.get('error'),
                    'data': None
                }), status_code
            
            return jsonify({
                'success': True,
                'data': data,
                'error': None
            }), status_code
            
        except Exception as e:
            logger.error(f"API error in {f.__name__}: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e),
                'data': None
            }), 500
    
    return decorated_function


__all__ = ['configure_request_limits', 'api_response']
