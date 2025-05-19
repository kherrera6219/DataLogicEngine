"""
Universal Knowledge Graph (UKG) System - API Middleware

This module provides middleware functions for the UKG API endpoints,
including response standardization and error handling.
"""

import json
import logging
import traceback
from functools import wraps
from flask import jsonify, request, make_response, current_app

# Set up logging
logger = logging.getLogger(__name__)

def api_response(f):
    """
    Decorator for standardizing API responses and handling errors.
    
    Args:
        f: The function to wrap
        
    Returns:
        A decorated function that handles standardized responses
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            # Call the API function
            result = f(*args, **kwargs)
            
            # If the result is a tuple, it contains data and status code
            if isinstance(result, tuple) and len(result) >= 2:
                data, status_code = result[0], result[1]
            else:
                data, status_code = result, 200
            
            # Standardize the response format
            return standardize_response(data, status_code)
            
        except Exception as e:
            # Log the full exception details for debugging
            logger.error(f"API Error in {f.__name__}: {str(e)}")
            logger.debug(traceback.format_exc())
            
            # Generate a standardized error response
            error_data = {
                'success': False,
                'error': str(e),
                'endpoint': request.path,
                'method': request.method
            }
            
            return standardize_response(error_data, 500)
    
    return decorated

def standardize_response(data, status_code=200):
    """
    Standardize API response format.
    
    Args:
        data: Response data
        status_code: HTTP status code
        
    Returns:
        Standardized response
    """
    # If status code is provided in data, extract it
    if isinstance(data, dict) and 'status_code' in data:
        status_code = data.pop('status_code')
    
    # Ensure we have a valid status code
    if status_code is None:
        status_code = 200
    
    # Create response
    response = make_response(jsonify(data), status_code)
    
    # Set common headers
    response.headers['Content-Type'] = 'application/json'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,PUT,DELETE,OPTIONS'
    
    return response

def setup_middleware(app):
    """
    Set up middleware for the Flask application.
    
    Args:
        app: The Flask application
    """
    @app.after_request
    def after_request(response):
        """Process response after each request."""
        # Add CORS headers to every response
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        return response
    
    @app.before_request
    def before_request():
        """Process request before handling."""
        # Log incoming requests for debugging
        if current_app.debug:
            logger.debug(f"Request: {request.method} {request.path}")
            if request.is_json:
                logger.debug(f"Request JSON: {json.dumps(request.get_json(), indent=2)}")