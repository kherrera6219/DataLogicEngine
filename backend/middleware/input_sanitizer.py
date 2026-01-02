"""
Input Sanitization Middleware

Provides comprehensive input sanitization and validation middleware
to protect against XSS, SQL injection, and other injection attacks.
"""

import re
import bleach
from flask import request, jsonify
from functools import wraps
import logging

logger = logging.getLogger(__name__)


# XSS Protection - Allowed HTML tags (very restrictive)
ALLOWED_TAGS = ['b', 'i', 'u', 'em', 'strong', 'p', 'br', 'ul', 'ol', 'li']
ALLOWED_ATTRIBUTES = {}


def sanitize_html(value):
    """
    Sanitize HTML input to prevent XSS attacks.

    Args:
        value: Input string to sanitize

    Returns:
        Sanitized string with dangerous HTML removed
    """
    if not isinstance(value, str):
        return value

    # Remove all HTML tags (most secure option)
    # For rich text, use bleach.clean with ALLOWED_TAGS
    return bleach.clean(value, tags=[], strip=True)


def sanitize_string(value):
    """
    Sanitize string input for basic safety.

    Args:
        value: Input string to sanitize

    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return value

    # Remove null bytes
    value = value.replace('\x00', '')

    # Remove CRLF injection attempts
    value = value.replace('\r', '').replace('\n', ' ')

    # Normalize whitespace
    value = ' '.join(value.split())

    return value


def sanitize_dict(data):
    """
    Recursively sanitize dictionary values.

    Args:
        data: Dictionary to sanitize

    Returns:
        Sanitized dictionary
    """
    if not isinstance(data, dict):
        return data

    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = sanitize_string(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_dict(v) if isinstance(v, dict) else sanitize_string(v) if isinstance(v, str) else v for v in value]
        else:
            sanitized[key] = value

    return sanitized


def detect_sql_injection(value):
    """
    Detect potential SQL injection attempts.

    Args:
        value: Input string to check

    Returns:
        True if suspicious patterns detected, False otherwise
    """
    if not isinstance(value, str):
        return False

    # Common SQL injection patterns (basic detection)
    sql_patterns = [
        r"(?i)(union\s+select)",
        r"(?i)(insert\s+into)",
        r"(?i)(delete\s+from)",
        r"(?i)(drop\s+table)",
        r"(?i)(update\s+\w+\s+set)",
        r"(?i)(exec\s*\()",
        r"(?i)(execute\s+immediate)",
        r"--\s*$",  # SQL comments
        r"(?i)(xp_cmdshell)",
        r"(?i)(;.*drop)",
    ]

    for pattern in sql_patterns:
        if re.search(pattern, value):
            return True

    return False


def detect_path_traversal(value):
    """
    Detect path traversal attempts.

    Args:
        value: Input string to check

    Returns:
        True if suspicious patterns detected, False otherwise
    """
    if not isinstance(value, str):
        return False

    # Path traversal patterns
    path_patterns = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e",
        r"%252e%252e",
    ]

    for pattern in path_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            return True

    return False


def detect_command_injection(value):
    """
    Detect command injection attempts.

    Args:
        value: Input string to check

    Returns:
        True if suspicious patterns detected, False otherwise
    """
    if not isinstance(value, str):
        return False

    # Command injection patterns
    cmd_patterns = [
        r"[;&|`$]",  # Shell metacharacters
        r"(?i)(wget|curl|nc|ncat)\s+",
        r"(?i)(bash|sh|cmd|powershell)\s+",
    ]

    for pattern in cmd_patterns:
        if re.search(pattern, value):
            return True

    return False


class InputSanitizer:
    """Middleware for sanitizing all input data."""

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the middleware with Flask app."""
        app.before_request(self.sanitize_request)

    def sanitize_request(self):
        """Sanitize all request data before processing."""
        # Skip sanitization for static files
        if request.endpoint and request.endpoint.startswith('static'):
            return None

        # Check for malicious patterns
        if request.is_json and request.get_json(silent=True):
            data = request.get_json()
            if self.check_malicious_patterns(data):
                logger.warning(f"Malicious input detected: {request.url} - IP: {request.remote_addr}")
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_INPUT',
                        'message': 'Invalid input detected. Please check your data.'
                    }
                }), 400

        # Check form data
        if request.form:
            for key, value in request.form.items():
                if self.check_malicious_string(value):
                    logger.warning(f"Malicious input in form field '{key}': {request.url} - IP: {request.remote_addr}")
                    return jsonify({
                        'success': False,
                        'error': {
                            'code': 'INVALID_INPUT',
                            'message': f'Invalid input in field: {key}'
                        }
                    }), 400

        # Check query parameters
        if request.args:
            for key, value in request.args.items():
                if self.check_malicious_string(value):
                    logger.warning(f"Malicious input in query param '{key}': {request.url} - IP: {request.remote_addr}")
                    return jsonify({
                        'success': False,
                        'error': {
                            'code': 'INVALID_INPUT',
                            'message': f'Invalid input in parameter: {key}'
                        }
                    }), 400

        return None

    def check_malicious_patterns(self, data):
        """
        Check data for malicious patterns.

        Args:
            data: Data to check (dict, list, or string)

        Returns:
            True if malicious patterns found, False otherwise
        """
        if isinstance(data, dict):
            return any(self.check_malicious_patterns(v) for v in data.values())
        elif isinstance(data, list):
            return any(self.check_malicious_patterns(v) for v in data)
        elif isinstance(data, str):
            return self.check_malicious_string(data)
        return False

    def check_malicious_string(self, value):
        """
        Check if string contains malicious patterns.

        Args:
            value: String to check

        Returns:
            True if malicious, False otherwise
        """
        if not isinstance(value, str):
            return False

        # Check for various injection attempts
        if detect_sql_injection(value):
            logger.warning(f"SQL injection pattern detected: {value[:100]}")
            return True

        if detect_path_traversal(value):
            logger.warning(f"Path traversal pattern detected: {value[:100]}")
            return True

        if detect_command_injection(value):
            logger.warning(f"Command injection pattern detected: {value[:100]}")
            return True

        return False


def sanitize_input(f):
    """
    Decorator to sanitize function input parameters.

    Usage:
        @sanitize_input
        def my_function(param1, param2):
            # param1 and param2 are now sanitized
            pass
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        # Sanitize positional arguments
        sanitized_args = []
        for arg in args:
            if isinstance(arg, str):
                sanitized_args.append(sanitize_string(arg))
            elif isinstance(arg, dict):
                sanitized_args.append(sanitize_dict(arg))
            else:
                sanitized_args.append(arg)

        # Sanitize keyword arguments
        sanitized_kwargs = {}
        for key, value in kwargs.items():
            if isinstance(value, str):
                sanitized_kwargs[key] = sanitize_string(value)
            elif isinstance(value, dict):
                sanitized_kwargs[key] = sanitize_dict(value)
            else:
                sanitized_kwargs[key] = value

        return f(*sanitized_args, **sanitized_kwargs)

    return wrapper


# Export main functions
__all__ = [
    'InputSanitizer',
    'sanitize_html',
    'sanitize_string',
    'sanitize_dict',
    'sanitize_input',
    'detect_sql_injection',
    'detect_path_traversal',
    'detect_command_injection',
]
