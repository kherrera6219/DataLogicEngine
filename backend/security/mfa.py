"""
Multi-Factor Authentication (MFA) Module

Provides TOTP-based multi-factor authentication using pyotp.
Includes:
- MFA setup and verification
- QR code generation
- Backup codes
- Recovery process
"""

import pyotp
import qrcode
import io
import base64
import secrets
import hashlib
from typing import Tuple, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MFAManager:
    """Manage Multi-Factor Authentication for users"""

    # Configuration
    ISSUER_NAME = "DataLogicEngine"
    BACKUP_CODE_COUNT = 10
    BACKUP_CODE_LENGTH = 8

    @staticmethod
    def generate_secret() -> str:
        """
        Generate a new MFA secret key.

        Returns:
            Base32-encoded secret key
        """
        return pyotp.random_base32()

    @staticmethod
    def generate_totp_uri(username: str, secret: str, issuer: Optional[str] = None) -> str:
        """
        Generate TOTP URI for QR code.

        Args:
            username: User's username or email
            secret: MFA secret key
            issuer: Issuer name (default: DataLogicEngine)

        Returns:
            TOTP URI string
        """
        issuer = issuer or MFAManager.ISSUER_NAME
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=username,
            issuer_name=issuer
        )

    @staticmethod
    def generate_qr_code(totp_uri: str) -> str:
        """
        Generate QR code image as base64-encoded string.

        Args:
            totp_uri: TOTP URI from generate_totp_uri()

        Returns:
            Base64-encoded PNG image of QR code
        """
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(totp_uri)
        qr.make(fit=True)

        # Generate image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"

    @staticmethod
    def verify_totp(secret: str, code: str, window: int = 1) -> bool:
        """
        Verify TOTP code against secret.

        Args:
            secret: User's MFA secret
            code: 6-digit TOTP code from authenticator app
            window: Number of time windows to check (default: 1 = 30 seconds before/after)

        Returns:
            True if code is valid, False otherwise
        """
        if not secret or not code:
            return False

        # Remove spaces and validate format
        code = code.replace(' ', '').replace('-', '')
        if not code.isdigit() or len(code) != 6:
            return False

        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(code, valid_window=window)
        except Exception as e:
            logger.error(f"Error verifying TOTP: {str(e)}")
            return False

    @staticmethod
    def generate_backup_codes(count: Optional[int] = None) -> List[str]:
        """
        Generate backup codes for MFA recovery.

        Args:
            count: Number of codes to generate (default: 10)

        Returns:
            List of backup codes (not hashed)
        """
        count = count or MFAManager.BACKUP_CODE_COUNT
        length = MFAManager.BACKUP_CODE_LENGTH

        backup_codes = []
        for _ in range(count):
            # Generate random code (alphanumeric)
            code = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(length))
            # Format as XXXX-XXXX for readability
            formatted_code = f"{code[:4]}-{code[4:]}"
            backup_codes.append(formatted_code)

        return backup_codes

    @staticmethod
    def hash_backup_code(code: str) -> str:
        """
        Hash a backup code for secure storage.

        Args:
            code: Backup code to hash

        Returns:
            SHA-256 hash of the code
        """
        # Remove formatting
        code = code.replace('-', '').replace(' ', '').upper()
        # Hash with SHA-256
        return hashlib.sha256(code.encode()).hexdigest()

    @staticmethod
    def hash_backup_codes(codes: List[str]) -> List[dict]:
        """
        Hash multiple backup codes for storage.

        Args:
            codes: List of backup codes

        Returns:
            List of dictionaries with hash, used status, and creation date
        """
        return [
            {
                'hash': MFAManager.hash_backup_code(code),
                'used': False,
                'created_at': datetime.utcnow().isoformat()
            }
            for code in codes
        ]

    @staticmethod
    def verify_backup_code(code: str, hashed_codes: List[dict]) -> Tuple[bool, Optional[str]]:
        """
        Verify a backup code against stored hashes.

        Args:
            code: Backup code to verify
            hashed_codes: List of stored backup code dictionaries

        Returns:
            Tuple of (is_valid, matching_hash)
        """
        if not code or not hashed_codes:
            return False, None

        # Hash the provided code
        code_hash = MFAManager.hash_backup_code(code)

        # Check against all stored hashes
        for backup in hashed_codes:
            if backup['hash'] == code_hash:
                # Check if already used
                if backup.get('used', False):
                    logger.warning(f"Backup code already used: {code_hash[:8]}...")
                    return False, None

                # Valid and unused backup code
                return True, backup['hash']

        return False, None

    @staticmethod
    def mark_backup_code_used(code_hash: str, hashed_codes: List[dict]) -> List[dict]:
        """
        Mark a backup code as used.

        Args:
            code_hash: Hash of the backup code that was used
            hashed_codes: List of stored backup code dictionaries

        Returns:
            Updated list of backup codes
        """
        for backup in hashed_codes:
            if backup['hash'] == code_hash:
                backup['used'] = True
                backup['used_at'] = datetime.utcnow().isoformat()
                break

        return hashed_codes

    @staticmethod
    def setup_mfa(username: str) -> Tuple[str, str, List[str]]:
        """
        Complete MFA setup for a user.

        Args:
            username: User's username

        Returns:
            Tuple of (secret, qr_code_data_uri, backup_codes)
        """
        # Generate secret
        secret = MFAManager.generate_secret()

        # Generate QR code
        totp_uri = MFAManager.generate_totp_uri(username, secret)
        qr_code = MFAManager.generate_qr_code(totp_uri)

        # Generate backup codes
        backup_codes = MFAManager.generate_backup_codes()

        logger.info(f"MFA setup initiated for user: {username}")

        return secret, qr_code, backup_codes

    @staticmethod
    def validate_mfa_setup(secret: str, verification_code: str) -> bool:
        """
        Validate MFA setup by verifying the first code.

        Args:
            secret: MFA secret that was generated
            verification_code: Code from user's authenticator app

        Returns:
            True if verification successful
        """
        is_valid = MFAManager.verify_totp(secret, verification_code, window=2)

        if is_valid:
            logger.info("MFA setup verification successful")
        else:
            logger.warning("MFA setup verification failed")

        return is_valid

    @staticmethod
    def check_mfa_required(user) -> bool:
        """
        Check if MFA is required for a user.

        Args:
            user: User model instance

        Returns:
            True if MFA should be required
        """
        # MFA is required for admin users
        if user.is_admin:
            return True

        # MFA is optional but recommended for regular users
        return user.mfa_enabled

    @staticmethod
    def get_unused_backup_codes_count(hashed_codes: List[dict]) -> int:
        """
        Get count of unused backup codes.

        Args:
            hashed_codes: List of stored backup code dictionaries

        Returns:
            Number of unused backup codes
        """
        if not hashed_codes:
            return 0

        return sum(1 for code in hashed_codes if not code.get('used', False))


def require_mfa(f):
    """
    Decorator to require MFA verification for protected routes.

    Usage:
        @app.route('/admin/dashboard')
        @login_required
        @require_mfa
        def admin_dashboard():
            return render_template('admin.html')
    """
    from functools import wraps
    from flask import session, redirect, url_for, flash
    from flask_login import current_user

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated
        if not current_user.is_authenticated:
            return redirect(url_for('login'))

        # Check if MFA is required
        if not MFAManager.check_mfa_required(current_user):
            # MFA not required, proceed
            return f(*args, **kwargs)

        # Check if MFA is verified in this session
        if not session.get('mfa_verified', False):
            flash('Multi-factor authentication required', 'warning')
            return redirect(url_for('mfa_verify'))

        # MFA verified, proceed
        return f(*args, **kwargs)

    return decorated_function
