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


def etag_middleware():
    """
    Middleware to add ETag headers for conditional requests.
    
    Supports If-None-Match header for GET requests, returning
    304 Not Modified when content hasn't changed.
    """
    import hashlib
    from flask import request, make_response
    
    def add_etag(response):
        try:
            # Only add ETags for successful GET/HEAD requests with content
            if request.method in ('GET', 'HEAD') and response.status_code == 200:
                # Generate ETag from response data
                if response.data:
                    etag = hashlib.md5(response.data).hexdigest()
                    response.headers['ETag'] = f'"{etag}"'
                    
                    # Check If-None-Match header
                    if_none_match = request.headers.get('If-None-Match')
                    if if_none_match:
                        # Strip quotes and compare
                        client_etag = if_none_match.strip('"')
                        if client_etag == etag:
                            # Content hasn't changed, return 304
                            return make_response('', 304)
            
            # Add Cache-Control for API responses
            if '/api/' in request.path:
                if 'Cache-Control' not in response.headers:
                    response.headers['Cache-Control'] = 'private, max-age=0, must-revalidate'
                    
        except Exception as e:
            logger.error(f"Error in ETag middleware: {str(e)}")
            
        return response
    
    return add_etag


__all__ = ['configure_request_limits', 'api_response', 'etag_middleware']

