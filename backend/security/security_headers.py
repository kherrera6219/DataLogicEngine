"""
Security Headers Middleware

Implements comprehensive security headers to protect against common web vulnerabilities.
Supports SOC 2, OWASP Top 10, and industry best practices.
"""

from flask import Response
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers to all responses.

    Implements headers recommended by:
    - OWASP Secure Headers Project
    - Mozilla Observatory
    - Security best practices
    """

    def __init__(self, app=None, config: Optional[Dict] = None):
        """
        Initialize security headers middleware.

        Args:
            app: Flask application instance
            config: Optional configuration dictionary
        """
        self.config = config or {}
        if app:
            self.init_app(app)

    def init_app(self, app):
        """
        Initialize the middleware with a Flask app.

        Args:
            app: Flask application instance
        """
        app.after_request(self.add_security_headers)
        logger.info("Security headers middleware initialized")

    def add_security_headers(self, response: Response) -> Response:
        """
        Add comprehensive security headers to response.

        Args:
            response: Flask response object

        Returns:
            Response with security headers added
        """
        # Get environment from config
        environment = self.config.get('ENV', 'production')
        is_development = environment == 'development'

        # X-Content-Type-Options
        # Prevents MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # X-Frame-Options
        # Prevents clickjacking attacks
        response.headers['X-Frame-Options'] = 'DENY'

        # X-XSS-Protection
        # Enables browser's built-in XSS protection (legacy browsers)
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # Strict-Transport-Security (HSTS)
        # Forces HTTPS connections
        # Only add in production with HTTPS
        if not is_development:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'

        # Content-Security-Policy (CSP)
        # Prevents XSS, clickjacking, and other code injection attacks
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net",
            "img-src 'self' data: https: blob:",
            "font-src 'self' data: https://fonts.gstatic.com https://cdn.jsdelivr.net",
            "connect-src 'self' https://api.openai.com https://*.openai.azure.com",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]

        # Relax CSP in development for better DX
        if is_development:
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' *",
                "style-src 'self' 'unsafe-inline' *",
                "img-src 'self' data: https: blob: *",
                "font-src 'self' data: *",
                "connect-src 'self' *",
                "frame-ancestors 'self'",
                "base-uri 'self'",
                "form-action 'self'"
            ]

        response.headers['Content-Security-Policy'] = '; '.join(csp_directives)

        # Referrer-Policy
        # Controls how much referrer information is sent
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions-Policy (formerly Feature-Policy)
        # Controls which browser features can be used
        permissions = [
            'geolocation=()',
            'microphone=()',
            'camera=()',
            'payment=()',
            'usb=()',
            'magnetometer=()',
            'gyroscope=()',
            'speaker=()'
        ]
        response.headers['Permissions-Policy'] = ', '.join(permissions)

        # X-Permitted-Cross-Domain-Policies
        # Restrict Adobe Flash and PDF cross-domain requests
        response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'

        # Cache-Control for sensitive pages
        # Prevent caching of sensitive data
        if 'api' in response.headers.get('Content-Type', ''):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'

        # X-Download-Options
        # Prevents IE from executing downloads in site's context
        response.headers['X-Download-Options'] = 'noopen'

        # Cross-Origin policies
        response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
        response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
        response.headers['Cross-Origin-Resource-Policy'] = 'same-origin'

        return response


def configure_security_headers(app, config: Optional[Dict] = None):
    """
    Configure security headers for a Flask application.

    Args:
        app: Flask application instance
        config: Optional configuration dictionary

    Example:
        from flask import Flask
        from backend.security.security_headers import configure_security_headers

        app = Flask(__name__)
        configure_security_headers(app)
    """
    SecurityHeadersMiddleware(app, config)
    logger.info("Security headers configured")
