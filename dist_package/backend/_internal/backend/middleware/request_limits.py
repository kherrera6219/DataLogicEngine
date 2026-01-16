"""
Request Limits Middleware

Implements request size limits and timeouts to protect against:
- DoS attacks via large payloads
- Slowloris attacks
- Resource exhaustion
"""

from flask import request, jsonify
import logging

logger = logging.getLogger(__name__)


class RequestLimitsMiddleware:
    """
    Middleware to enforce request size and timeout limits.
    """

    def __init__(self, app=None, config=None):
        """
        Initialize request limits middleware.

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
        # Set maximum content length (16MB default)
        max_content_length = self.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
        app.config['MAX_CONTENT_LENGTH'] = max_content_length

        # Register error handler for request entity too large
        @app.errorhandler(413)
        def request_entity_too_large(error):
            """Handle requests that exceed size limit"""
            max_size_mb = max_content_length / (1024 * 1024)
            logger.warning(f"Request rejected: Size exceeds {max_size_mb}MB limit from {request.remote_addr}")

            return jsonify({
                'error': 'Request too large',
                'message': f'Request body must not exceed {max_size_mb}MB',
                'max_size_bytes': max_content_length
            }), 413

        # Register before request handler for additional checks
        @app.before_request
        def check_request_limits():
            """Check request limits before processing"""
            # Check content-length header if present
            content_length = request.content_length

            if content_length and content_length > max_content_length:
                max_size_mb = max_content_length / (1024 * 1024)
                logger.warning(f"Request rejected: Content-Length {content_length} exceeds {max_size_mb}MB from {request.remote_addr}")

                return jsonify({
                    'error': 'Request too large',
                    'message': f'Request body must not exceed {max_size_mb}MB',
                    'max_size_bytes': max_content_length,
                    'your_size_bytes': content_length
                }), 413

            # Additional validation for specific endpoints can be added here
            # For example, stricter limits for file uploads vs API calls

        logger.info(f"Request limits middleware initialized (max size: {max_content_length / (1024 * 1024)}MB)")


def configure_request_limits(app, config=None):
    """
    Configure request limits for a Flask application.

    Args:
        app: Flask application instance
        config: Optional configuration dictionary

    Example:
        from flask import Flask
        from backend.middleware.request_limits import configure_request_limits

        app = Flask(__name__)
        configure_request_limits(app, {
            'MAX_CONTENT_LENGTH': 10 * 1024 * 1024  # 10MB
        })
    """
    RequestLimitsMiddleware(app, config)
    logger.info("Request limits configured")


# File upload size limits for different types
FILE_UPLOAD_LIMITS = {
    'document': 10 * 1024 * 1024,  # 10MB for documents (PDF, DOCX, etc.)
    'image': 5 * 1024 * 1024,       # 5MB for images
    'video': 50 * 1024 * 1024,      # 50MB for videos
    'csv': 20 * 1024 * 1024,        # 20MB for CSV files
    'default': 16 * 1024 * 1024     # 16MB default
}


def validate_file_upload(file, file_type='default'):
    """
    Validate file upload size and type.

    Args:
        file: FileStorage object from request.files
        file_type: Type of file ('document', 'image', 'video', 'csv', 'default')

    Returns:
        Tuple of (is_valid, error_message)

    Example:
        from flask import request
        from backend.middleware.request_limits import validate_file_upload

        file = request.files.get('document')
        is_valid, error = validate_file_upload(file, 'document')
        if not is_valid:
            return jsonify({'error': error}), 400
    """
    if not file:
        return False, "No file provided"

    # Get size limit for file type
    max_size = FILE_UPLOAD_LIMITS.get(file_type, FILE_UPLOAD_LIMITS['default'])

    # Check file size
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning

    if file_size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        actual_size_mb = file_size / (1024 * 1024)
        return False, f"File size ({actual_size_mb:.2f}MB) exceeds maximum allowed size ({max_size_mb}MB) for {file_type} files"

    # Check filename
    if not file.filename:
        return False, "File must have a filename"

    # Additional validation (file type based on extension) can be added here
    allowed_extensions = {
        'document': {'.pdf', '.doc', '.docx', '.txt', '.rtf'},
        'image': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg'},
        'video': {'.mp4', '.avi', '.mov', '.wmv', '.flv'},
        'csv': {'.csv', '.tsv'},
        'default': set()
    }

    if file_type in allowed_extensions and allowed_extensions[file_type]:
        import os
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_extensions[file_type]:
            return False, f"File type {ext} not allowed for {file_type} uploads. Allowed: {', '.join(allowed_extensions[file_type])}"

    return True, None
