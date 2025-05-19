"""
Universal Knowledge Graph (UKG) System - Middleware

This module provides middleware functionality for the UKG system,
including request processing, response standardization, and error handling.
"""

import time
import json
import logging
from functools import wraps
from flask import request, jsonify, g, current_app
from werkzeug.exceptions import HTTPException

# Set up logging
logger = logging.getLogger(__name__)

class ResponseFormatter:
    """Response formatting middleware for API standardization."""
    
    @staticmethod
    def standardize_response(data=None, message=None, status="success", status_code=200, errors=None):
        """
        Standardize API responses with a consistent format.
        
        Args:
            data: The actual data payload to return
            message: A human-readable message about the response
            status: 'success' or 'error'
            status_code: HTTP status code
            errors: Dictionary or list of errors if status is 'error'
            
        Returns:
            A standardized response dictionary
        """
        response = {
            "status": status,
            "code": status_code,
            "timestamp": int(time.time()),
            "message": message
        }
        
        if data is not None:
            response["data"] = data
            
        if errors is not None:
            response["errors"] = errors
            
        return response, status_code

def api_response(f):
    """Decorator to standardize API responses."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
            
            # If the result is already a fully formatted response
            if isinstance(result, tuple) and len(result) == 2 and isinstance(result[0], dict) and isinstance(result[1], int):
                return result
                
            # If it's just the data, format it properly
            data = result
            return ResponseFormatter.standardize_response(data=data)
            
        except HTTPException as e:
            logger.exception(f"HTTP Exception in {f.__name__}: {str(e)}")
            return ResponseFormatter.standardize_response(
                message=str(e),
                status="error",
                status_code=e.code,
                errors=[{"type": e.__class__.__name__, "message": str(e)}]
            )
        except Exception as e:
            logger.exception(f"Exception in {f.__name__}: {str(e)}")
            return ResponseFormatter.standardize_response(
                message="An internal server error occurred",
                status="error",
                status_code=500,
                errors=[{"type": e.__class__.__name__, "message": str(e)}]
            )
    
    return decorated_function

class RequestLogger:
    """Middleware for logging all requests."""
    
    @staticmethod
    def before_request():
        """Log before request processing."""
        g.start_time = time.time()
        logger.debug(f"Request: {request.method} {request.path}")
        
        if request.method in ['POST', 'PUT'] and request.is_json:
            logger.debug(f"Request Body: {json.dumps(request.json, indent=2)}")
    
    @staticmethod
    def after_request(response):
        """Log after request processing."""
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            logger.debug(f"Response: {response.status_code} ({duration:.4f}s)")
        
        return response

def setup_middleware(app):
    """Set up all middleware for the application."""
    # Register request/response logging middleware
    app.before_request(RequestLogger.before_request)
    app.after_request(RequestLogger.after_request)
    
    # Add any other middleware setup here
    
    return app