"""
API Security with Request Signing and Validation.

This module implements:
- HMAC request signing
- Request/response validation
- Replay attack prevention
- Timestamp verification
- Body integrity verification

Compliance: OWASP API Security Top 10
"""

import hmac
import hashlib
import base64
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from functools import wraps
from flask import request, jsonify


class RequestSigner:
    """
    HMAC-based request signing for API security.

    Signs requests with:
    - Timestamp (prevents replay attacks)
    - Method + Path + Body
    - API key ID
    - HMAC-SHA256 signature
    """

    def __init__(self, audit_logger=None):
        self.audit_logger = audit_logger
        self.max_timestamp_skew = 300  # 5 minutes
        self.nonce_store = {}  # In production, use Redis
        self.nonce_ttl = 600  # 10 minutes

    def sign_request(
        self,
        method: str,
        path: str,
        body: Optional[str],
        api_key_id: str,
        api_secret: str,
        timestamp: Optional[int] = None
    ) -> Dict[str, str]:
        """
        Sign an API request.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path
            body: Request body (JSON string or None)
            api_key_id: API key identifier
            api_secret: API secret for signing
            timestamp: Unix timestamp (optional, defaults to now)

        Returns:
            Dictionary with signature headers
        """
        if timestamp is None:
            timestamp = int(time.time())

        # Create canonical string
        canonical = self._create_canonical_string(method, path, body, timestamp)

        # Generate HMAC signature
        signature = self._generate_signature(canonical, api_secret)

        return {
            'X-API-Key': api_key_id,
            'X-API-Timestamp': str(timestamp),
            'X-API-Signature': signature
        }

    def verify_request(
        self,
        method: str,
        path: str,
        body: Optional[str],
        api_key_id: str,
        api_secret: str,
        timestamp: str,
        signature: str,
        nonce: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify a signed API request.

        Args:
            method: HTTP method
            path: Request path
            body: Request body
            api_key_id: API key ID from header
            api_secret: API secret for verification
            timestamp: Timestamp from header
            signature: Signature from header
            nonce: Optional nonce for replay prevention

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            timestamp_int = int(timestamp)
        except ValueError:
            return False, "Invalid timestamp format"

        # Check timestamp freshness (prevent replay attacks)
        current_time = int(time.time())
        time_diff = abs(current_time - timestamp_int)

        if time_diff > self.max_timestamp_skew:
            self._log_audit("request_signature_timestamp_invalid", {
                "api_key_id": api_key_id,
                "time_diff": time_diff,
                "max_skew": self.max_timestamp_skew
            })
            return False, "Request timestamp too old or too far in future"

        # Check nonce for replay prevention
        if nonce:
            nonce_key = f"{api_key_id}:{nonce}"
            if nonce_key in self.nonce_store:
                self._log_audit("request_replay_detected", {
                    "api_key_id": api_key_id,
                    "nonce": nonce
                })
                return False, "Nonce already used (replay attack detected)"

            # Store nonce
            self.nonce_store[nonce_key] = time.time()
            self._cleanup_old_nonces()

        # Recreate canonical string
        canonical = self._create_canonical_string(method, path, body, timestamp_int)

        # Generate expected signature
        expected_signature = self._generate_signature(canonical, api_secret)

        # Constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(signature, expected_signature):
            self._log_audit("request_signature_invalid", {
                "api_key_id": api_key_id,
                "method": method,
                "path": path
            })
            return False, "Invalid signature"

        # Log successful verification
        self._log_audit("request_signature_verified", {
            "api_key_id": api_key_id,
            "method": method,
            "path": path
        })

        return True, None

    def _create_canonical_string(
        self,
        method: str,
        path: str,
        body: Optional[str],
        timestamp: int
    ) -> str:
        """Create canonical string for signing."""
        # Normalize method
        method = method.upper()

        # Calculate body hash
        if body:
            body_hash = hashlib.sha256(body.encode()).hexdigest()
        else:
            body_hash = hashlib.sha256(b'').hexdigest()

        # Create canonical string: METHOD\nPATH\nTIMESTAMP\nBODY_HASH
        canonical = f"{method}\n{path}\n{timestamp}\n{body_hash}"

        return canonical

    def _generate_signature(self, canonical_string: str, secret: str) -> str:
        """Generate HMAC-SHA256 signature."""
        signature_bytes = hmac.new(
            secret.encode(),
            canonical_string.encode(),
            hashlib.sha256
        ).digest()

        return base64.b64encode(signature_bytes).decode()

    def _cleanup_old_nonces(self):
        """Remove expired nonces."""
        current_time = time.time()
        expired = [
            key for key, timestamp in self.nonce_store.items()
            if current_time - timestamp > self.nonce_ttl
        ]
        for key in expired:
            del self.nonce_store[key]

    def _log_audit(self, event_type: str, details: Dict[str, Any]):
        """Log to audit logger."""
        if self.audit_logger:
            self.audit_logger.log_security_event(
                event_type=event_type,
                details=details,
                severity="INFO" if "verified" in event_type else "WARNING"
            )


class APIValidator:
    """
    API request/response validation.

    Validates:
    - Request schema
    - Input sanitization
    - Output sanitization
    - Content-Type enforcement
    """

    def __init__(self, audit_logger=None):
        self.audit_logger = audit_logger

    def validate_json_request(
        self,
        required_fields: Optional[list] = None,
        optional_fields: Optional[list] = None,
        max_size_kb: int = 1024
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Validate JSON request.

        Args:
            required_fields: List of required field names
            optional_fields: List of optional field names
            max_size_kb: Maximum request size in KB

        Returns:
            Tuple of (is_valid, data, error_message)
        """
        # Check Content-Type
        content_type = request.headers.get('Content-Type', '')
        if 'application/json' not in content_type:
            return False, None, "Content-Type must be application/json"

        # Check request size
        content_length = request.content_length
        if content_length and content_length > max_size_kb * 1024:
            return False, None, f"Request too large (max {max_size_kb}KB)"

        # Parse JSON
        try:
            data = request.get_json(force=True)
        except Exception as e:
            return False, None, f"Invalid JSON: {str(e)}"

        if not isinstance(data, dict):
            return False, None, "Request body must be a JSON object"

        # Validate required fields
        if required_fields:
            missing = [f for f in required_fields if f not in data]
            if missing:
                return False, None, f"Missing required fields: {', '.join(missing)}"

        # Validate no unexpected fields
        if required_fields or optional_fields:
            allowed_fields = set(required_fields or []) | set(optional_fields or [])
            unexpected = [f for f in data.keys() if f not in allowed_fields]
            if unexpected:
                return False, None, f"Unexpected fields: {', '.join(unexpected)}"

        return True, data, None

    def sanitize_output(self, data: Any, sensitive_fields: Optional[list] = None) -> Any:
        """
        Sanitize output data.

        Args:
            data: Output data
            sensitive_fields: Fields to redact

        Returns:
            Sanitized data
        """
        if sensitive_fields is None:
            sensitive_fields = [
                'password', 'secret', 'token', 'api_key', 'private_key',
                'ssn', 'credit_card', 'cvv'
            ]

        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                # Check if field is sensitive
                if any(sensitive in key.lower() for sensitive in sensitive_fields):
                    sanitized[key] = '[REDACTED]'
                else:
                    sanitized[key] = self.sanitize_output(value, sensitive_fields)
            return sanitized

        elif isinstance(data, list):
            return [self.sanitize_output(item, sensitive_fields) for item in data]

        else:
            return data


# Flask decorators for API security

_request_signer = None
_api_validator = None


def get_request_signer(audit_logger=None) -> RequestSigner:
    """Get or create request signer instance."""
    global _request_signer
    if _request_signer is None:
        _request_signer = RequestSigner(audit_logger=audit_logger)
    return _request_signer


def get_api_validator(audit_logger=None) -> APIValidator:
    """Get or create API validator instance."""
    global _api_validator
    if _api_validator is None:
        _api_validator = APIValidator(audit_logger=audit_logger)
    return _api_validator


def require_signed_request(get_api_secret_func):
    """
    Decorator to require signed API requests.

    Args:
        get_api_secret_func: Function that takes api_key_id and returns api_secret

    Usage:
        @app.route('/api/secure-endpoint')
        @require_signed_request(lambda key_id: get_api_secret_from_db(key_id))
        def secure_endpoint():
            return jsonify({"data": "secure"})
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            signer = get_request_signer()

            # Get signature headers
            api_key_id = request.headers.get('X-API-Key')
            timestamp = request.headers.get('X-API-Timestamp')
            signature = request.headers.get('X-API-Signature')
            nonce = request.headers.get('X-API-Nonce')  # Optional

            if not all([api_key_id, timestamp, signature]):
                return jsonify({
                    "error": "Missing required signature headers",
                    "required": ["X-API-Key", "X-API-Timestamp", "X-API-Signature"]
                }), 401

            # Get API secret
            try:
                api_secret = get_api_secret_func(api_key_id)
                if not api_secret:
                    return jsonify({"error": "Invalid API key"}), 401
            except Exception as e:
                return jsonify({"error": "API key verification failed"}), 500

            # Get request body
            body = None
            if request.data:
                body = request.data.decode('utf-8')

            # Verify signature
            is_valid, error_msg = signer.verify_request(
                method=request.method,
                path=request.path,
                body=body,
                api_key_id=api_key_id,
                api_secret=api_secret,
                timestamp=timestamp,
                signature=signature,
                nonce=nonce
            )

            if not is_valid:
                return jsonify({"error": error_msg}), 403

            return f(*args, **kwargs)

        return decorated_function
    return decorator


def validate_json_schema(required_fields=None, optional_fields=None, max_size_kb=1024):
    """
    Decorator to validate JSON request schema.

    Usage:
        @app.route('/api/create-user', methods=['POST'])
        @validate_json_schema(required_fields=['username', 'email'], optional_fields=['name'])
        def create_user():
            data = request.get_json()
            # data is guaranteed to have username and email
            return jsonify({"status": "created"})
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            validator = get_api_validator()

            is_valid, data, error_msg = validator.validate_json_request(
                required_fields=required_fields,
                optional_fields=optional_fields,
                max_size_kb=max_size_kb
            )

            if not is_valid:
                return jsonify({"error": error_msg}), 400

            # Store validated data in request context
            request.validated_data = data

            return f(*args, **kwargs)

        return decorated_function
    return decorator
