from datetime import datetime, timedelta, UTC
from typing import TYPE_CHECKING
import re

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from sqlalchemy.orm import relationship, backref

if TYPE_CHECKING:
    from flask_sqlalchemy.model import Model

def _utcnow():
    """Return current UTC datetime."""
    return datetime.now(UTC)

class APIKey(db.Model):
    """API key used for authenticating programmatic requests."""

    __tablename__ = 'api_keys'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False, default='Default Key')
    key = db.Column(db.String(128), unique=True, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=_utcnow)
    last_used_at = db.Column(db.DateTime)
    revoked_at = db.Column(db.DateTime)

    user = db.relationship('User', backref=db.backref('api_keys', lazy='dynamic'))

    def to_dict(self):
        """Serialize the API key metadata (without exposing the secret)."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'revoked_at': self.revoked_at.isoformat() if self.revoked_at else None,
        }

class OAuthAccount(db.Model):
    """OAuth account linking for external authentication providers (e.g., Replit Auth)"""
    __tablename__ = 'oauth_accounts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    provider = db.Column(db.String(50), nullable=False)
    provider_user_id = db.Column(db.String(255), nullable=False)
    token = db.Column(db.JSON)
    refresh_token = db.Column(db.String(512))
    token_expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    user = db.relationship('User', backref=db.backref('oauth_accounts', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('provider', 'provider_user_id', name='uq_provider_user'),
    )

    def __repr__(self):
        return f'<OAuthAccount provider={self.provider} user_id={self.user_id}>'


class PasswordHistory(db.Model):
    """Password history for preventing password reuse"""
    __tablename__ = 'password_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow)

    def __repr__(self):
        return f'<PasswordHistory user_id={self.user_id} created={self.created_at}>'


class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    active = db.Column(db.Boolean, default=True)
    
    # Multi-tenancy
    tenant_id = db.Column(db.String(64), index=True, nullable=True)
    
    is_admin = db.Column(db.Boolean, default=False)
    is_sso = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=_utcnow)
    last_login = db.Column(db.DateTime)

    password_changed_at = db.Column(db.DateTime, default=_utcnow)
    password_expires_at = db.Column(db.DateTime)
    force_password_change = db.Column(db.Boolean, default=False)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)

    mfa_enabled = db.Column(db.Boolean, default=False)
    mfa_secret = db.Column(db.String(32))
    mfa_backup_codes = db.Column(db.JSON)

    # Identifiers
    windows_sid = db.Column(db.String(255), unique=True, nullable=True, index=True)
    role = db.Column(db.String(20), default='user') # Owner, admin, user, viewer
    
    password_history_entries = db.relationship(
        'PasswordHistory',
        backref='user',
        lazy='dynamic',
        order_by='PasswordHistory.created_at.desc()'
    )

    # User Methods
    def check_password_history(self, password):
        """Check if password was used in the last N passwords"""
        from backend.security.password_security import PasswordSecurity

        history_count = PasswordSecurity.PASSWORD_HISTORY_COUNT
        recent_passwords = self.password_history_entries.limit(history_count).all()

        for history in recent_passwords:
            if check_password_hash(history.password_hash, password):
                return False

        return True

    def set_password(self, password):
        """Set password hash with security enhancements"""
        from backend.security.password_security import PasswordSecurity

        # Validate password strength
        is_valid, errors = PasswordSecurity.validate_password_strength(password)
        if not is_valid:
            raise ValueError(f"Password does not meet security requirements: {', '.join(errors)}")

        # Check password history (prevent reuse)
        if self.id and not self.check_password_history(password):
            raise ValueError(f"Password was used recently. Please choose a different password. Cannot reuse last {PasswordSecurity.PASSWORD_HISTORY_COUNT} passwords.")

        # Check password breach (warning only, don't block)
        is_breached, count = PasswordSecurity.check_password_breach(password)
        if is_breached and count and count > 10:
            # Log warning but allow - user should be notified
            import logging
            logging.warning(f"User {self.username} setting password found in {count} breaches")

        if self.id and self.password_hash:
            history_entry = PasswordHistory()
            history_entry.user_id = self.id
            history_entry.password_hash = self.password_hash
            db.session.add(history_entry)

            old_entries = self.password_history_entries.offset(PasswordSecurity.PASSWORD_HISTORY_COUNT).all()
            for old_entry in old_entries:
                db.session.delete(old_entry)

        # Set the password hash
        self.password_hash = generate_password_hash(password)
        self.password_changed_at = _utcnow()

        # Set expiration date (90 days from now)
        self.password_expires_at = _utcnow() + timedelta(days=PasswordSecurity.PASSWORD_EXPIRY_DAYS)

        # Reset failed login attempts
        self.failed_login_attempts = 0
        self.locked_until = None
        self.force_password_change = False

    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)

    def is_password_expired(self):
        """Check if password has expired"""
        from backend.security.password_security import PasswordSecurity
        return PasswordSecurity.is_password_expired(self.password_changed_at)

    def days_until_password_expiry(self):
        """Get days until password expires"""
        from backend.security.password_security import PasswordSecurity
        return PasswordSecurity.days_until_expiry(self.password_changed_at)

    def is_account_locked(self):
        """Check if account is locked due to failed login attempts"""
        if self.locked_until and _utcnow() < self.locked_until:
            return True
        return False

    def record_failed_login(self):
        """Record a failed login attempt and lock account if threshold exceeded"""
        self.failed_login_attempts += 1

        # Lock account after 5 failed attempts for 30 minutes
        if self.failed_login_attempts >= 5:
            self.locked_until = _utcnow() + timedelta(minutes=30)

    def record_successful_login(self):
        """Record a successful login"""
        self.last_login = _utcnow()
        self.failed_login_attempts = 0
        self.locked_until = None

    def to_dict(self):
        """Convert user to dictionary (excluding sensitive data)"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'tenant_id': self.tenant_id,
            'is_active': self.active,
            'is_admin': self.is_admin,
            'role': self.role,
            'windows_sid': self.windows_sid,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'mfa_enabled': self.mfa_enabled,
            'password_expires_in_days': self.days_until_password_expiry(),
            'force_password_change': self.force_password_change
        }
    
    def get_totp_uri(self) -> str:
        """Generate a TOTP URI for QR code generation."""
        import pyotp
        if not self.mfa_secret:
            self.mfa_secret = pyotp.random_base32()
            db.session.commit()
        
        return pyotp.totp.TOTP(self.mfa_secret).provisioning_uri(
            name=self.username,
            issuer_name="DataLogicEngine"
        )
    
    def verify_totp(self, token: str) -> bool:
        """Verify a TOTP token."""
        import pyotp
        if not self.mfa_secret:
            return False
            
        # Allow entry 1 window before/after for better UX
        totp = pyotp.TOTP(self.mfa_secret)
        return totp.verify(token, valid_window=1)

    def __repr__(self):
        return f'<User {self.username}>'


class AuditLog(db.Model):
    """Compliance audit log for tracking sensitive system actions."""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=_utcnow, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    windows_sid = db.Column(db.String(255))
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45)) # IPv4/IPv6 support

    user = db.relationship('User', backref=db.backref('audit_logs', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'user_id': self.user_id,
            'windows_sid': self.windows_sid,
            'action': self.action,
            'details': self.details
        }
