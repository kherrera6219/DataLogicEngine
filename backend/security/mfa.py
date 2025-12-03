"""
Multi-Factor Authentication (MFA) Module

Implements Time-Based One-Time Password (TOTP) for DataLogicEngine.
Provides 2FA security layer for user authentication.

Features:
- TOTP generation and verification (RFC 6238)
- QR code generation for authenticator apps
- Backup codes for account recovery
- MFA enforcement policies
- Support for Google Authenticator, Authy, Microsoft Authenticator, etc.

Standards:
- RFC 6238: TOTP - Time-Based One-Time Password Algorithm
- RFC 4226: HOTP - HMAC-Based One-Time Password Algorithm
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
    """
    Multi-Factor Authentication Manager

    Handles TOTP generation, verification, QR codes, and backup codes.
    """

    # Configuration
    TOTP_ISSUER = "DataLogicEngine"
    TOTP_INTERVAL = 30  # seconds
    TOTP_DIGITS = 6
    BACKUP_CODE_COUNT = 10
    BACKUP_CODE_LENGTH = 8

    def __init__(self, app_name: Optional[str] = None):
        """
        Initialize MFA Manager.

        Args:
            app_name: Application name for TOTP issuer (default: DataLogicEngine)
        """
        if app_name:
            self.TOTP_ISSUER = app_name

    @staticmethod
    def generate_secret() -> str:
        """
        Generate a new TOTP secret key.

        Returns:
            Base32-encoded secret (32 characters)

        Example:
            secret = MFAManager.generate_secret()
            # Returns: 'JBSWY3DPEHPK3PXP'
        """
        return pyotp.random_base32()

    def get_totp_uri(self, secret: str, username: str) -> str:
        """
        Generate TOTP provisioning URI for QR code.

        Args:
            secret: TOTP secret key
            username: User's username or email

        Returns:
            TOTP URI string

        Example:
            uri = mfa.get_totp_uri('JBSWY3DPEHPK3PXP', 'john@example.com')
            # Returns: 'otpauth://totp/DataLogicEngine:john@example.com?secret=...'
        """
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=username,
            issuer_name=self.TOTP_ISSUER
        )

    def generate_qr_code(self, secret: str, username: str) -> str:
        """
        Generate QR code as base64-encoded PNG image.

        Args:
            secret: TOTP secret key
            username: User's username or email

        Returns:
            Base64-encoded PNG image string (data URI ready)

        Example:
            qr_code = mfa.generate_qr_code(secret, 'john@example.com')
            # Can be used in HTML: <img src="data:image/png;base64,{qr_code}">
        """
        # Get TOTP URI
        uri = self.get_totp_uri(secret, username)

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        return img_base64

    @staticmethod
    def verify_totp(secret: str, token: str, window: int = 1) -> bool:
        """
        Verify a TOTP token.

        Args:
            secret: TOTP secret key
            token: 6-digit TOTP code from user
            window: Number of time windows to check (1 = ±30 seconds)

        Returns:
            True if token is valid, False otherwise

        Example:
            is_valid = MFAManager.verify_totp('JBSWY3DPEHPK3PXP', '123456')
        """
        if not secret or not token:
            return False

        try:
            totp = pyotp.TOTP(secret)
            # Verify with time window (allows for clock drift)
            return totp.verify(token, valid_window=window)
        except Exception as e:
            logger.error(f"TOTP verification error: {str(e)}")
            return False

    @staticmethod
    def get_current_totp(secret: str) -> str:
        """
        Get current TOTP code (for testing/debugging only).

        Args:
            secret: TOTP secret key

        Returns:
            Current 6-digit TOTP code

        WARNING: Only use for testing. Never expose to users!
        """
        totp = pyotp.TOTP(secret)
        return totp.now()

    @staticmethod
    def generate_backup_codes(count: int = 10, length: int = 8) -> List[str]:
        """
        Generate backup codes for account recovery.

        Args:
            count: Number of backup codes to generate (default: 10)
            length: Length of each code (default: 8)

        Returns:
            List of backup codes (plaintext)

        Example:
            codes = MFAManager.generate_backup_codes()
            # Returns: ['A1B2C3D4', 'E5F6G7H8', ...]
        """
        codes = []
        for _ in range(count):
            # Generate cryptographically secure random code
            code = secrets.token_hex(length // 2).upper()
            codes.append(code)
        return codes

    @staticmethod
    def hash_backup_code(code: str) -> str:
        """
        Hash a backup code for secure storage.

        Args:
            code: Plaintext backup code

        Returns:
            SHA-256 hash of the code

        Example:
            hashed = MFAManager.hash_backup_code('A1B2C3D4')
        """
        return hashlib.sha256(code.encode('utf-8')).hexdigest()

    @staticmethod
    def hash_backup_codes(codes: List[str]) -> List[str]:
        """
        Hash multiple backup codes.

        Args:
            codes: List of plaintext backup codes

        Returns:
            List of hashed backup codes

        Example:
            hashed_codes = MFAManager.hash_backup_codes(codes)
        """
        return [MFAManager.hash_backup_code(code) for code in codes]

    @staticmethod
    def verify_backup_code(code: str, hashed_codes: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Verify a backup code against stored hashes.

        Args:
            code: Plaintext backup code from user
            hashed_codes: List of hashed backup codes

        Returns:
            Tuple of (is_valid, matched_hash)

        Example:
            is_valid, matched_hash = MFAManager.verify_backup_code('A1B2C3D4', user.mfa_backup_codes)
            if is_valid:
                # Remove the used backup code
                user.mfa_backup_codes.remove(matched_hash)
        """
        if not code or not hashed_codes:
            return False, None

        # Hash the provided code
        code_hash = MFAManager.hash_backup_code(code.upper().strip())

        # Check if hash exists in list
        if code_hash in hashed_codes:
            return True, code_hash

        return False, None


class MFASetup:
    """
    Helper class for MFA setup flow.

    Manages the complete MFA enrollment process.
    """

    def __init__(self, username: str, app_name: Optional[str] = None):
        """
        Initialize MFA setup for a user.

        Args:
            username: User's username or email
            app_name: Application name (optional)
        """
        self.username = username
        self.mfa_manager = MFAManager(app_name)
        self.secret = None
        self.backup_codes = None

    def initiate_setup(self) -> dict:
        """
        Start MFA setup process.

        Returns:
            Dictionary with setup data:
            {
                'secret': str,  # TOTP secret (store securely)
                'qr_code': str,  # Base64 QR code image
                'manual_entry': str,  # Secret for manual entry
                'backup_codes': List[str]  # Plaintext backup codes (show once!)
            }

        Example:
            setup = MFASetup('john@example.com')
            data = setup.initiate_setup()
            # Display QR code and backup codes to user
            # Store secret and hashed backup codes in database
        """
        # Generate secret
        self.secret = self.mfa_manager.generate_secret()

        # Generate QR code
        qr_code = self.mfa_manager.generate_qr_code(self.secret, self.username)

        # Generate backup codes
        self.backup_codes = self.mfa_manager.generate_backup_codes()

        return {
            'secret': self.secret,
            'qr_code': qr_code,
            'manual_entry': self.secret,  # For manual entry in authenticator app
            'backup_codes': self.backup_codes  # Show these ONCE to user
        }

    def verify_setup(self, token: str) -> bool:
        """
        Verify that user has correctly configured their authenticator app.

        Args:
            token: 6-digit TOTP code from user's authenticator app

        Returns:
            True if setup is verified, False otherwise

        Example:
            if setup.verify_setup('123456'):
                # Save MFA configuration to database
                user.mfa_enabled = True
                user.mfa_secret = setup.secret
                user.mfa_backup_codes = MFAManager.hash_backup_codes(setup.backup_codes)
        """
        if not self.secret:
            raise ValueError("MFA setup not initiated. Call initiate_setup() first.")

        return self.mfa_manager.verify_totp(self.secret, token)

    def get_hashed_backup_codes(self) -> List[str]:
        """
        Get hashed backup codes for database storage.

        Returns:
            List of hashed backup codes

        Example:
            hashed = setup.get_hashed_backup_codes()
            user.mfa_backup_codes = hashed
        """
        if not self.backup_codes:
            raise ValueError("MFA setup not initiated. Call initiate_setup() first.")

        return self.mfa_manager.hash_backup_codes(self.backup_codes)


# ========================================
# Convenience Functions
# ========================================

def setup_mfa(username: str) -> dict:
    """
    Convenience function to initiate MFA setup.

    Args:
        username: User's username or email

    Returns:
        Setup data dictionary

    Example:
        from backend.security.mfa import setup_mfa

        data = setup_mfa('john@example.com')
        # Display to user:
        # - QR code: data['qr_code']
        # - Manual entry key: data['manual_entry']
        # - Backup codes: data['backup_codes']
    """
    setup = MFASetup(username)
    return setup.initiate_setup()


def verify_mfa_token(secret: str, token: str) -> bool:
    """
    Convenience function to verify MFA token.

    Args:
        secret: User's TOTP secret
        token: 6-digit code from user

    Returns:
        True if valid, False otherwise

    Example:
        from backend.security.mfa import verify_mfa_token

        if verify_mfa_token(user.mfa_secret, request.json['mfa_code']):
            # Allow login
        else:
            # Reject login
    """
    return MFAManager.verify_totp(secret, token)


def verify_backup_code(code: str, hashed_codes: List[str]) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to verify backup code.

    Args:
        code: Backup code from user
        hashed_codes: List of hashed backup codes

    Returns:
        Tuple of (is_valid, matched_hash)

    Example:
        from backend.security.mfa import verify_backup_code

        is_valid, used_hash = verify_backup_code(code, user.mfa_backup_codes)
        if is_valid:
            # Remove used backup code
            user.mfa_backup_codes.remove(used_hash)
            db.session.commit()
            # Allow login
    """
    return MFAManager.verify_backup_code(code, hashed_codes)


def generate_backup_codes(count: int = 10) -> Tuple[List[str], List[str]]:
    """
    Generate new backup codes.

    Args:
        count: Number of codes to generate

    Returns:
        Tuple of (plaintext_codes, hashed_codes)

    Example:
        from backend.security.mfa import generate_backup_codes

        plaintext, hashed = generate_backup_codes()
        # Show plaintext to user (ONCE!)
        # Store hashed in database
        user.mfa_backup_codes = hashed
    """
    codes = MFAManager.generate_backup_codes(count)
    hashed = MFAManager.hash_backup_codes(codes)
    return codes, hashed


# ========================================
# Installation Check
# ========================================

def check_mfa_dependencies() -> Tuple[bool, str]:
    """
    Check if MFA dependencies are installed.

    Returns:
        Tuple of (is_installed, message)

    Example:
        is_ready, message = check_mfa_dependencies()
        if not is_ready:
            print(f"ERROR: {message}")
    """
    try:
        import pyotp
        import qrcode
        return True, "MFA dependencies installed and ready"
    except ImportError as e:
        missing = str(e).split("'")[1] if "'" in str(e) else "unknown"
        return False, f"Missing dependency: {missing}. Install with: pip install pyotp qrcode[pil]"


# ========================================
# Module Testing
# ========================================

if __name__ == '__main__':
    print("Multi-Factor Authentication Module Test\n" + "=" * 50)

    # Check dependencies
    is_ready, message = check_mfa_dependencies()
    print(f"\nDependencies: {message}")

    if not is_ready:
        print("\nInstall dependencies first:")
        print("pip install pyotp==2.9.0 qrcode[pil]==7.4.2")
        exit(1)

    # Test MFA setup flow
    print("\n1. Testing MFA Setup...")
    setup = MFASetup('test@example.com')
    data = setup.initiate_setup()

    print(f"   Secret: {data['secret']}")
    print(f"   Manual Entry: {data['manual_entry']}")
    print(f"   QR Code (base64): {data['qr_code'][:50]}...")
    print(f"   Backup Codes: {', '.join(data['backup_codes'][:3])}...")

    # Test TOTP verification
    print("\n2. Testing TOTP Verification...")
    current_token = MFAManager.get_current_totp(data['secret'])
    print(f"   Current TOTP: {current_token}")

    is_valid = setup.verify_setup(current_token)
    print(f"   Verification: {'✅ PASS' if is_valid else '❌ FAIL'}")

    # Test backup codes
    print("\n3. Testing Backup Codes...")
    plaintext_code = data['backup_codes'][0]
    hashed_codes = setup.get_hashed_backup_codes()

    is_valid, matched = MFAManager.verify_backup_code(plaintext_code, hashed_codes)
    print(f"   Backup Code Verification: {'✅ PASS' if is_valid else '❌ FAIL'}")
    print(f"   Matched Hash: {matched[:20]}..." if matched else "   No match")

    print("\n✅ All tests passed!" if is_valid else "\n❌ Some tests failed!")
