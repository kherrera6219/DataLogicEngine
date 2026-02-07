"""
Request Timeout Middleware

Implements request timeout to prevent long-running requests from
exhausting server resources and to protect against slowloris attacks.
"""

import signal
import os
import logging
from functools import wraps
from flask import request, jsonify

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Custom exception for request timeouts."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Request timeout exceeded")


class RequestTimeout:
    """
    Middleware for implementing request timeouts.

    This prevents slow clients or long-running operations from
    tying up worker processes indefinitely.
    """

    def __init__(self, app=None, timeout=None):
        """
        Initialize timeout middleware.

        Args:
            app: Flask application
            timeout: Timeout in seconds (default: 30)
        """
        self._timeout_explicit = timeout is not None
        self.timeout = 30 if timeout is None else int(timeout)
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the middleware with Flask app."""
        # Environment timeout applies only when caller did not pass one explicitly.
        if not self._timeout_explicit:
            self.timeout = int(os.environ.get('REQUEST_TIMEOUT', self.timeout))

        # Configure timeout for gunicorn
        app.config['REQUEST_TIMEOUT'] = self.timeout

        # Note: Signal-based timeout only works on Unix-like systems
        # For Windows or production with gunicorn, configure worker timeout instead
        if hasattr(signal, 'SIGALRM'):
            app.before_request(self.start_timeout)
            app.after_request(self.cancel_timeout)
        else:
            logger.warning("Signal-based timeout not available on this platform. "
                         "Configure gunicorn worker timeout instead: --timeout %d", self.timeout)

    def start_timeout(self):
        """Start the timeout timer before processing request."""
        # Skip timeout for health check endpoints
        if request.endpoint and request.endpoint in ['health', 'static']:
            return

        # Only set timeout on Unix-like systems
        if hasattr(signal, 'SIGALRM'):
            try:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(self.timeout)
            except Exception as e:
                logger.error(f"Failed to set timeout: {e}")

    def cancel_timeout(self, response):
        """Cancel the timeout timer after processing request."""
        # Only cancel timeout on Unix-like systems
        if hasattr(signal, 'SIGALRM'):
            try:
                signal.alarm(0)  # Cancel the alarm
            except Exception as e:
                logger.error(f"Failed to cancel timeout: {e}")

        return response


def with_timeout(timeout_seconds=30):
    """
    Decorator to apply timeout to specific endpoints.

    Usage:
        @app.route('/slow-endpoint')
        @with_timeout(60)  # 60 second timeout
        def slow_endpoint():
            # Long-running operation
            pass

    Args:
        timeout_seconds: Timeout in seconds

    Returns:
        Decorated function with timeout
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Only works on Unix-like systems
            if not hasattr(signal, 'SIGALRM'):
                logger.warning("Timeout decorator not available on this platform")
                return f(*args, **kwargs)

            def timeout_handler(signum, frame):
                raise TimeoutError(f"Request exceeded {timeout_seconds} second timeout")

            # Set the signal handler and alarm
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)

            try:
                result = f(*args, **kwargs)
            except TimeoutError as e:
                logger.error(f"Timeout in {f.__name__}: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'REQUEST_TIMEOUT',
                        'message': 'Request took too long to process. Please try again.'
                    }
                }), 504  # Gateway Timeout
            finally:
                # Cancel the alarm and restore old handler
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)

            return result

        return wrapper
    return decorator


def configure_gunicorn_timeout(app):
    """
    Configure gunicorn timeout via application config.

    For production deployments with gunicorn, add this to your
    gunicorn configuration:

        timeout = 30  # seconds
        graceful_timeout = 30

    Or run gunicorn with:
        gunicorn --timeout 30 --graceful-timeout 30 main:app

    Args:
        app: Flask application
    """
    timeout = app.config.get('REQUEST_TIMEOUT', 30)

    # Log the configuration
    logger.info(f"Request timeout configured: {timeout} seconds")
    logger.info(f"For gunicorn, use: --timeout {timeout} --graceful-timeout {timeout}")

    return timeout


# Export main classes and functions
__all__ = [
    'RequestTimeout',
    'TimeoutError',
    'with_timeout',
    'configure_gunicorn_timeout',
]
