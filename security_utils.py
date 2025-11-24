"""
Security utilities for the Universal Knowledge Graph (UKG) System

Provides password validation, input sanitization, and other security functions.
"""

import re
import secrets
import string
from typing import Tuple, Optional
from urllib.parse import urlparse, urljoin
from flask import request, current_app
from itsdangerous import URLSafeTimedSerializer


class PasswordValidator:
    """Validates password strength according to security policy"""

    @staticmethod
    def validate(password: str, min_length: int = 12) -> Tuple[bool, str]:
        """
        Validate password strength.

        Args:
            password: Password to validate
            min_length: Minimum required length (default: 12)

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not password:
            return False, "Password is required"

        if len(password) < min_length:
            return False, f"Password must be at least {min_length} characters long"

        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"

        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"

        if not re.search(r'\d', password):
            return False, "Password must contain at least one number"

        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
            return False, "Password must contain at least one special character"

        # Check for common weak passwords
        weak_passwords = ['password', '12345678', 'qwerty', 'admin123', 'letmein']
        if password.lower() in weak_passwords:
            return False, "Password is too common and easily guessable"

        return True, "Password is valid"

    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """
        Generate a cryptographically secure random password.

        Args:
            length: Length of password to generate

        Returns:
            Secure random password
        """
        alphabet = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(alphabet) for _ in range(length))


class URLValidator:
    """Validates and sanitizes URLs to prevent open redirect attacks"""

    @staticmethod
    def is_safe_redirect_url(target: str) -> bool:
        """
        Check if a redirect URL is safe (same domain, no external redirects).

        Args:
            target: URL to validate

        Returns:
            True if URL is safe for redirect
        """
        if not target:
            return False

        # Parse the target URL
        parsed = urlparse(target)

        # Only allow relative URLs or URLs to same host
        if parsed.netloc:
            # If there's a network location, must match current host
            ref_url = urlparse(request.host_url)
            return parsed.netloc == ref_url.netloc

        # Relative URLs must start with /
        return target.startswith('/')

    @staticmethod
    def get_safe_redirect_target(default: str = '/') -> str:
        """
        Get a safe redirect target from request args.

        Args:
            default: Default URL if no safe target found

        Returns:
            Safe redirect URL
        """
        for target in request.args.get('next'), request.referrer:
            if target and URLValidator.is_safe_redirect_url(target):
                return target
        return default


class InputSanitizer:
    """Sanitizes user input to prevent injection attacks"""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize a filename to prevent path traversal attacks.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove path components
        filename = filename.split('/')[-1].split('\\')[-1]

        # Remove non-alphanumeric characters except .-_
        filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)

        # Limit length
        if len(filename) > 255:
            filename = filename[:255]

        return filename

    @staticmethod
    def validate_uuid(uuid_string: str) -> bool:
        """
        Validate UUID format.

        Args:
            uuid_string: String to validate

        Returns:
            True if valid UUID format
        """
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        return bool(uuid_pattern.match(uuid_string))

    @staticmethod
    def validate_integer_range(value: str, min_val: int, max_val: int) -> Tuple[bool, int]:
        """
        Validate and parse integer within range.

        Args:
            value: String value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value

        Returns:
            Tuple of (is_valid, parsed_value)
        """
        try:
            int_val = int(value)
            if min_val <= int_val <= max_val:
                return True, int_val
            return False, 0
        except (ValueError, TypeError):
            return False, 0

    @staticmethod
    def validate_float_range(value: str, min_val: float, max_val: float) -> Tuple[bool, float]:
        """
        Validate and parse float within range.

        Args:
            value: String value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value

        Returns:
            Tuple of (is_valid, parsed_value)
        """
        try:
            float_val = float(value)
            if min_val <= float_val <= max_val:
                return True, float_val
            return False, 0.0
        except (ValueError, TypeError):
            return False, 0.0


class TokenGenerator:
    """Generates secure tokens for various purposes"""

    @staticmethod
    def generate_reset_token() -> str:
        """Generate a secure password reset token"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_api_key() -> str:
        """Generate a secure API key"""
        return secrets.token_urlsafe(48)

    @staticmethod
    def generate_session_id() -> str:
        """Generate a secure session ID"""
        return secrets.token_urlsafe(24)


def validate_simulation_parameters(params: dict) -> Tuple[bool, str]:
    """
    Validate simulation parameters to prevent resource exhaustion.

    Args:
        params: Dictionary of simulation parameters

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate refinement_steps
    if 'refinement_steps' in params:
        valid, value = InputSanitizer.validate_integer_range(
            str(params['refinement_steps']), 1, 100
        )
        if not valid:
            return False, "refinement_steps must be between 1 and 100"
        params['refinement_steps'] = value

    # Validate confidence_threshold
    if 'confidence_threshold' in params:
        valid, value = InputSanitizer.validate_float_range(
            str(params['confidence_threshold']), 0.0, 1.0
        )
        if not valid:
            return False, "confidence_threshold must be between 0.0 and 1.0"
        params['confidence_threshold'] = value

    return True, "Valid"


class PasswordResetManager:
    """Manages secure password reset tokens"""

    @staticmethod
    def get_serializer() -> URLSafeTimedSerializer:
        """Get the password reset token serializer"""
        return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

    @staticmethod
    def generate_reset_token(email: str) -> str:
        """
        Generate a secure, time-limited password reset token.

        Args:
            email: User's email address

        Returns:
            Secure reset token
        """
        serializer = PasswordResetManager.get_serializer()
        return serializer.dumps(email, salt='password-reset-salt')

    @staticmethod
    def verify_reset_token(token: str, max_age: int = 3600) -> Optional[str]:
        """
        Verify a password reset token and return the email if valid.

        Args:
            token: Reset token to verify
            max_age: Maximum age of token in seconds (default: 3600 = 1 hour)

        Returns:
            Email address if token is valid, None otherwise
        """
        serializer = PasswordResetManager.get_serializer()
        try:
            email = serializer.loads(
                token,
                salt='password-reset-salt',
                max_age=max_age
            )
            return email
        except Exception:
            return None
