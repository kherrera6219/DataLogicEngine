"""
Password Security Module

Provides enhanced password security features including:
- Password history tracking
- Password expiration
- Password breach detection (Have I Been Pwned API)
- Password strength validation
"""

import hashlib
import requests
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class PasswordSecurity:
    """Enhanced password security manager"""

    # Password policy constants
    MIN_PASSWORD_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = True
    PASSWORD_HISTORY_COUNT = 5  # Prevent reuse of last 5 passwords
    PASSWORD_EXPIRY_DAYS = 90  # Password expires after 90 days

    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, List[str]]:
        """
        Validate password meets strength requirements.

        Args:
            password: The password to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check length
        if len(password) < PasswordSecurity.MIN_PASSWORD_LENGTH:
            errors.append(f"Password must be at least {PasswordSecurity.MIN_PASSWORD_LENGTH} characters long")

        # Check for uppercase
        if PasswordSecurity.REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")

        # Check for lowercase
        if PasswordSecurity.REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")

        # Check for digit
        if PasswordSecurity.REQUIRE_DIGIT and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")

        # Check for special character
        if PasswordSecurity.REQUIRE_SPECIAL:
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?/"
            if not any(c in special_chars for c in password):
                errors.append("Password must contain at least one special character")

        # Check for common patterns
        common_patterns = ['123456', 'password', 'qwerty', 'abc123', '111111']
        password_lower = password.lower()
        for pattern in common_patterns:
            if pattern in password_lower:
                errors.append(f"Password contains common pattern: {pattern}")
                break

        return (len(errors) == 0, errors)

    @staticmethod
    def check_password_breach(password: str, timeout: int = 2) -> Tuple[bool, Optional[int]]:
        """
        Check if password has been exposed in data breaches using Have I Been Pwned API.

        Uses k-anonymity model - only sends first 5 chars of SHA-1 hash.

        Args:
            password: The password to check
            timeout: Request timeout in seconds

        Returns:
            Tuple of (is_breached, breach_count)
            Returns (False, None) if API is unavailable
        """
        try:
            # Hash the password with SHA-1
            sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()

            # Split into prefix (first 5 chars) and suffix
            prefix, suffix = sha1_hash[:5], sha1_hash[5:]

            # Query the API with the prefix
            url = f"https://api.pwnedpasswords.com/range/{prefix}"
            response = requests.get(url, timeout=timeout)

            if response.status_code == 200:
                # Parse the response
                hashes = response.text.split('\r\n')

                for hash_line in hashes:
                    hash_suffix, count = hash_line.split(':')
                    if hash_suffix == suffix:
                        # Password found in breach database
                        return (True, int(count))

                # Password not found in breaches
                return (False, 0)
            else:
                # API error, fail open (don't block user)
                logger.warning(f"HIBP API returned status {response.status_code}")
                return (False, None)

        except requests.exceptions.Timeout:
            logger.warning("HIBP API timeout")
            return (False, None)
        except Exception as e:
            logger.error(f"Error checking password breach: {str(e)}")
            return (False, None)

    @staticmethod
    def is_password_expired(last_changed: datetime, expiry_days: int = PASSWORD_EXPIRY_DAYS) -> bool:
        """
        Check if password has expired.

        Args:
            last_changed: DateTime when password was last changed
            expiry_days: Number of days before expiration

        Returns:
            True if password is expired
        """
        if not last_changed:
            # If never changed, consider expired
            return True

        expiry_date = last_changed + timedelta(days=expiry_days)
        return datetime.utcnow() > expiry_date

    @staticmethod
    def days_until_expiry(last_changed: datetime, expiry_days: int = PASSWORD_EXPIRY_DAYS) -> int:
        """
        Calculate days until password expires.

        Args:
            last_changed: DateTime when password was last changed
            expiry_days: Number of days before expiration

        Returns:
            Number of days until expiry (negative if already expired)
        """
        if not last_changed:
            return -1

        expiry_date = last_changed + timedelta(days=expiry_days)
        delta = expiry_date - datetime.utcnow()
        return delta.days

    @staticmethod
    def calculate_password_strength_score(password: str) -> Tuple[int, str]:
        """
        Calculate password strength score (0-100).

        Args:
            password: The password to evaluate

        Returns:
            Tuple of (score, strength_label)
        """
        score = 0

        # Length bonus (up to 30 points)
        if len(password) >= 8:
            score += 10
        if len(password) >= 12:
            score += 10
        if len(password) >= 16:
            score += 10

        # Character variety (up to 40 points)
        if any(c.isupper() for c in password):
            score += 10
        if any(c.islower() for c in password):
            score += 10
        if any(c.isdigit() for c in password):
            score += 10
        if any(not c.isalnum() for c in password):
            score += 10

        # Complexity bonus (up to 30 points)
        unique_chars = len(set(password))
        if unique_chars >= 8:
            score += 10
        if unique_chars >= 12:
            score += 10
        if unique_chars >= 16:
            score += 10

        # Determine strength label
        if score >= 80:
            label = "Very Strong"
        elif score >= 60:
            label = "Strong"
        elif score >= 40:
            label = "Moderate"
        elif score >= 20:
            label = "Weak"
        else:
            label = "Very Weak"

        return (score, label)
