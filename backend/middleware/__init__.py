"""
Backend middleware package for Universal Knowledge Graph system.

This package provides middleware components for request handling,
rate limiting, and other cross-cutting concerns.
"""

from functools import wraps
from flask import jsonify, current_app, Response, request, g
import logging
import os
from datetime import datetime, UTC
import uuid

from backend.utils.exceptions import UKGException
from backend.security.pii_redaction import pii_redactor
from .request_limits import configure_request_limits
from .resource_governor import configure_resource_governor

logger = logging.getLogger(__name__)


def api_response(f):
    """Decorator to standardize API responses with proper JSON formatting.
    
    Handles:
    - Plain dict returns (wrapped in success response)
    - (dict, status_code) tuples
    - UKGException (wrapped in error response with sanitized messages)
    - Flask Response objects (passed through unchanged)
    - Exceptions (wrapped in error response with sanitized messages)
    - Both synchronous and asynchronous functions
    """
    import inspect

    async def async_wrapper(*args, **kwargs):
        is_dev = current_app.config.get('ENV') == 'development' or current_app.debug
        try:
            result = await f(*args, **kwargs)
            return _format_response(result, f, is_dev)
        except Exception as e:
            return _handle_exception(e, f, is_dev)

    def sync_wrapper(*args, **kwargs):
        is_dev = current_app.config.get('ENV') == 'development' or current_app.debug
        try:
            result = f(*args, **kwargs)
            return _format_response(result, f, is_dev)
        except Exception as e:
            return _handle_exception(e, f, is_dev)

    def _format_response(result, func, is_dev):
        if isinstance(result, Response):
            return result
        
        if isinstance(result, tuple):
            if len(result) == 3: # (data, status, headers)
                data, status_code, headers = result
            elif len(result) == 2:
                data, status_code = result
                headers = {}
            else:
                data = result
                status_code = 200
                headers = {}
        else:
            data = result
            status_code = 200
            headers = {}
        
        # PII Redaction for outgoing data
        if isinstance(data, (dict, list)):
            if isinstance(data, dict):
                data = pii_redactor.redact_dict(data)
            else:
                data = [pii_redactor.redact_dict(item) if isinstance(item, dict) else (pii_redactor.redact_text(item)[0] if isinstance(item, str) else item) for item in data]

        if isinstance(data, dict) and 'error' in data:
            return jsonify({
                'success': False,
                'error': data.get('error'),
                'data': None,
                'timestamp': datetime.now(UTC).isoformat()
            }), status_code, headers
        
        return jsonify({
            'success': True,
            'data': data,
            'error': None,
            'timestamp': datetime.now(UTC).isoformat()
        }), status_code, headers

    def _handle_exception(e, func, is_dev):
        if isinstance(e, UKGException):
            logger.warning(f"UKG Error in {func.__name__}: {e.message} ({e.error_code})")
            return jsonify({
                'success': False,
                'error': e.message,
                'code': e.error_code,
                'details': pii_redactor.redact_dict(e.details) if e.details else None,
                'timestamp': datetime.now(UTC).isoformat()
            }), e.status_code

        logger.error(f"Unhandled API error in {func.__name__}: {str(e)}", exc_info=True)
        error_msg = str(e) if is_dev else "An internal server error occurred."
        return jsonify({
            'success': False,
            'error': error_msg,
            'data': None,
            'code': 'INTERNAL_SERVER_ERROR',
            'timestamp': datetime.now(UTC).isoformat()
        }), 500

    wrapper = async_wrapper if inspect.iscoroutinefunction(f) else sync_wrapper
    
    # Manually preserve function attributes to prevent Flask endpoint collisions
    try:
        wrapper.__name__ = f.__name__
        wrapper.__doc__ = f.__doc__
        wrapper.__module__ = f.__module__
    except (AttributeError, TypeError):
        pass
        
    return wrapper


def audit_request_middleware():
    """Middleware to audit API requests."""
    from backend.security import get_audit_logger
    
    def audit_request(response):
        try:
            # Get the audit logger
            audit_logger = get_audit_logger()
            
            # Log the API request
            audit_logger.log_api_request(
                request_id=getattr(g, 'request_id', str(uuid.uuid4())),
                user_id=getattr(g, 'user_id', None),
                endpoint=request.endpoint,
                method=request.method,
                status_code=response.status_code,
                ip_address=request.remote_addr
            )
        except Exception as e:
            logger.error(f"Error in audit middleware: {str(e)}")
            
        return response
    
    return audit_request


def setup_middleware(app):
    """Set up all middleware for the application."""
    from .correlation_id import configure_correlation_id, setup_correlation_logging
    from backend.security.security_headers import configure_security_headers
    from .etag import etag_middleware
    from .timeout import RequestTimeout
    
    # Configure Correlation ID
    configure_correlation_id(app)
    log_format = str(app.config.get("LOG_FORMAT") or os.environ.get("LOG_FORMAT", "json")).lower()
    if log_format != "json":
        setup_correlation_logging()
    else:
        logger.info("Correlation logging formatter override skipped for JSON log format")
    
    # Configure Security Headers
    configure_security_headers(app, {'ENV': app.config.get('ENV', 'production')})
    
    # Configure Request Limits
    configure_request_limits(app, {
        'MAX_CONTENT_LENGTH': app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
    })
    
    # Initialize Request Timeout
    RequestTimeout(app)

    # Configure in-process resource governor (tenant/user concurrency caps)
    configure_resource_governor(app)
    
    # Register global after_request handlers
    app.after_request(etag_middleware())
    app.after_request(audit_request_middleware())
    
    logger.info("UKG Unified Middleware stack hardened and initialized")


__all__ = ['configure_request_limits', 'configure_resource_governor', 'api_response', 'setup_middleware']

