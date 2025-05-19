"""
Universal Knowledge Graph (UKG) System - API Middleware

This module provides middleware functions for the UKG API.
"""

import logging
from datetime import datetime
from functools import wraps
from flask import jsonify

logger = logging.getLogger(__name__)

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