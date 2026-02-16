"""
Correlation ID Middleware

Adds a unique correlation ID to each request for distributed tracing
and improved debugging capabilities.
"""

import uuid
import logging
from flask import request, g

logger = logging.getLogger(__name__)


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
            correlation_id = request.headers.get(self.CORRELATION_ID_HEADER)
            if not correlation_id:
                correlation_id = request.headers.get(self.REQUEST_ID_HEADER)
            
            if not correlation_id:
                correlation_id = str(uuid.uuid4())
            
            # Set both for backward compatibility
            g.correlation_id = correlation_id
            g.request_id = correlation_id
            
        @app.after_request
        def add_correlation_id_to_response(response):
            """Add correlation ID to response headers."""
            if hasattr(g, 'correlation_id'):
                response.headers[self.CORRELATION_ID_HEADER] = g.correlation_id
                response.headers[self.REQUEST_ID_HEADER] = g.correlation_id
            return response
        
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
    return 'startup'


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
