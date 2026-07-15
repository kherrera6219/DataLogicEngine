"""
Correlation ID Middleware

Adds a unique correlation ID to each request for distributed tracing
and improved debugging capabilities.
"""

import uuid
import logging
import re
from flask import request, g

from backend.observability.context import (
    bind_correlation_id,
    current_correlation_id,
    reset_correlation_id,
)

logger = logging.getLogger(__name__)

CORRELATION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")


def normalize_correlation_id(value: object) -> str | None:
    """Return one bounded log/header-safe correlation ID or ``None``."""
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not CORRELATION_ID_PATTERN.fullmatch(candidate):
        return None
    return candidate


class CorrelationIdMiddleware:
    """
    Middleware to add correlation IDs to all requests for tracing.
    """
    
    CORRELATION_ID_HEADER = 'X-Correlation-ID'
    REQUEST_ID_HEADER = 'X-Request-ID'
    
    def __init__(self, app=None):
        """Initialize the middleware."""
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize the middleware with a Flask app.
        """
        @app.before_request
        def add_correlation_id():
            """Add or extract correlation ID for the request."""
            # Try Correlation ID first, then Request ID
            supplied_id = request.headers.get(self.CORRELATION_ID_HEADER)
            if not supplied_id:
                supplied_id = request.headers.get(self.REQUEST_ID_HEADER)
            correlation_id = normalize_correlation_id(supplied_id)
            if correlation_id is None:
                correlation_id = str(uuid.uuid4())
                g.correlation_id_replaced = bool(supplied_id)
            
            # Set both for backward compatibility
            g.correlation_id = correlation_id
            g.request_id = correlation_id
            g.correlation_context_token = bind_correlation_id(correlation_id)
            
        @app.after_request
        def add_correlation_id_to_response(response):
            """Add correlation ID to response headers."""
            if hasattr(g, 'correlation_id'):
                response.headers[self.CORRELATION_ID_HEADER] = g.correlation_id
                response.headers[self.REQUEST_ID_HEADER] = g.correlation_id
            return response

        @app.teardown_request
        def reset_request_correlation(_error=None):
            token = getattr(g, 'correlation_context_token', None)
            if token is not None:
                reset_correlation_id(token)
                g.correlation_context_token = None
        
        logger.info("Correlation ID middleware initialized")


def get_correlation_id():
    """
    Get the correlation ID for the current request.
    
    Returns:
        str: The correlation ID or 'startup' if not in request context
    """
    try:
        from flask import has_request_context, g
        if has_request_context():
            # Use getattr with a default to avoid potential proxy resolution errors
            # accessing 'g' itself might raise RuntimeError in some edge cases
            return getattr(g, 'correlation_id', 'unknown')
    except Exception:
        pass
    return current_correlation_id()


def configure_correlation_id(app):
    """
    Configure correlation ID middleware for a Flask application.
    
    Args:
        app: Flask application instance
    """
    CorrelationIdMiddleware(app)
    logger.info("Correlation ID middleware configured")


class CorrelationIdFilter(logging.Filter):
    """
    Logging filter that adds correlation ID to log records.
    """
    
    def filter(self, record):
        """Add correlation ID to the log record."""
        record.correlation_id = get_correlation_id()
        return True


def setup_correlation_logging():
    """
    Setup logging to include correlation IDs in all log messages.
    
    Call this after configuring the correlation ID middleware.
    """
    correlation_filter = CorrelationIdFilter()
    
    for handler in logging.root.handlers:
        handler.addFilter(correlation_filter)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s'
    )
    
    for handler in logging.root.handlers:
        handler.setFormatter(formatter)
    
    logger.info("Correlation ID logging configured")
