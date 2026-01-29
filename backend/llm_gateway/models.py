"""
Database models for LLM Gateway.
"""

import uuid
from datetime import datetime, UTC
from typing import Optional

from sqlalchemy import JSON, UUID
from cryptography.fernet import Fernet
from flask import current_app

try:
    from extensions import db
except ImportError:
    import os
    import sys
    # Add root to path as fallback
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from extensions import db


class LLMProvider(db.Model):
    """LLM Provider configuration with encrypted API keys."""
    __tablename__ = 'llm_providers'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Provider identification
    name = db.Column(db.String(100), nullable=False)  # Display name
    provider_type = db.Column(db.String(50), nullable=False)  # openai, azure, anthropic, google, custom
    
    # Authentication (encrypted)
    api_key_encrypted = db.Column(db.LargeBinary, nullable=True)
    
    # Endpoint configuration
    endpoint = db.Column(db.String(500), nullable=True)  # For Azure/custom
    model_id = db.Column(db.String(100), nullable=True)  # Default model
    deployment_name = db.Column(db.String(100), nullable=True)  # For Azure
    api_version = db.Column(db.String(20), nullable=True)  # For Azure
    
    # Settings
    is_active = db.Column(db.Boolean, default=True)
    is_default = db.Column(db.Boolean, default=False)
    priority = db.Column(db.Integer, default=100)  # Lower = higher priority
    
    # Limits
    rate_limit_rpm = db.Column(db.Integer, nullable=True)  # Requests per minute
    rate_limit_tpm = db.Column(db.Integer, nullable=True)  # Tokens per minute
    timeout_seconds = db.Column(db.Integer, default=30)
    max_retries = db.Column(db.Integer, default=3)
    
    # Additional config
    config = db.Column(JSON, nullable=True)  # Extra provider-specific config
    
    # Ownership
    tenant_id = db.Column(db.String(100), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    last_used_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    usage_records = db.relationship('LLMProviderUsage', backref='provider', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_api_key(self, api_key: str) -> None:
        """Encrypt and store API key."""
        key = current_app.config.get('ENCRYPTION_KEY')
        if not key:
            # Generate key from secret key if not set
            import hashlib
            import base64
            secret = current_app.config.get('SECRET_KEY', 'default-secret')
            key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
        
        f = Fernet(key)
        self.api_key_encrypted = f.encrypt(api_key.encode())
    
    def get_api_key(self) -> Optional[str]:
        """Decrypt and return API key."""
        if not self.api_key_encrypted:
            return None
        
        try:
            key = current_app.config.get('ENCRYPTION_KEY')
            if not key:
                import hashlib
                import base64
                secret = current_app.config.get('SECRET_KEY', 'default-secret')
                key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
            
            f = Fernet(key)
            return f.decrypt(self.api_key_encrypted).decode()
        except Exception as e:
            # Handle decryption errors (InvalidToken, wrong key, etc.)
            import logging
            logging.getLogger(__name__).warning(f"Failed to decrypt API key for provider {self.name}: {e}")
            return None
    
    def to_dict(self, include_key: bool = False) -> dict:
        """Serialize provider (optionally include masked key)."""
        result = {
            'id': str(self.id),
            'name': self.name,
            'provider_type': self.provider_type,
            'endpoint': self.endpoint,
            'model_id': self.model_id,
            'deployment_name': self.deployment_name,
            'api_version': self.api_version,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'priority': self.priority,
            'rate_limit_rpm': self.rate_limit_rpm,
            'rate_limit_tpm': self.rate_limit_tpm,
            'timeout_seconds': self.timeout_seconds,
            'max_retries': self.max_retries,
            'config': self.config,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'has_api_key': self.api_key_encrypted is not None,
        }
        
        if include_key and self.api_key_encrypted:
            key = self.get_api_key()
            if key:
                # Mask all but last 4 chars
                result['api_key_masked'] = '*' * (len(key) - 4) + key[-4:]
        
        return result


class LLMProviderUsage(db.Model):
    """Usage tracking for LLM providers."""
    __tablename__ = 'llm_provider_usage'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = db.Column(UUID(as_uuid=True), db.ForeignKey('llm_providers.id'), nullable=False)
    
    # Request info
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    api_key_id = db.Column(UUID(as_uuid=True), db.ForeignKey('external_api_keys.id'), nullable=True)
    run_id = db.Column(UUID(as_uuid=True), nullable=True)  # Link to trace run
    
    # Model used
    model = db.Column(db.String(100), nullable=True)
    
    # Usage metrics
    tokens_in = db.Column(db.Integer, default=0)
    tokens_out = db.Column(db.Integer, default=0)
    latency_ms = db.Column(db.Integer, nullable=True)
    
    # Status
    success = db.Column(db.Boolean, default=True)
    error_code = db.Column(db.String(50), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    
    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'provider_id': str(self.provider_id),
            'user_id': self.user_id,
            'run_id': str(self.run_id) if self.run_id else None,
            'model': self.model,
            'tokens_in': self.tokens_in,
            'tokens_out': self.tokens_out,
            'latency_ms': self.latency_ms,
            'success': self.success,
            'error_code': self.error_code,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ExternalAPIKey(db.Model):
    """API keys for external clients to access the gateway."""
    __tablename__ = 'external_api_keys'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Key identification
    name = db.Column(db.String(100), nullable=False)
    key_prefix = db.Column(db.String(10), nullable=False)  # First 8 chars for lookup
    key_hash = db.Column(db.String(256), nullable=False)  # SHA256 hash
    
    # Ownership
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tenant_id = db.Column(db.String(100), nullable=True)
    
    # Permissions
    permissions = db.Column(JSON, default=lambda: {'read': True, 'write': True, 'admin': False})
    allowed_providers = db.Column(JSON, nullable=True)  # Restrict to specific providers
    allowed_models = db.Column(JSON, nullable=True)  # Restrict to specific models
    
    # Limits
    rate_limit_rpm = db.Column(db.Integer, default=60)
    rate_limit_daily = db.Column(db.Integer, nullable=True)
    max_tokens_per_request = db.Column(db.Integer, nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    # Usage tracking
    total_requests = db.Column(db.Integer, default=0)
    total_tokens = db.Column(db.Integer, default=0)
    last_used_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    
    # Relationships
    usage_records = db.relationship('LLMProviderUsage', backref='api_key', lazy='dynamic')
    
    @classmethod
    def generate_key(cls) -> tuple[str, str, str]:
        """Generate a new API key. Returns (full_key, prefix, hash)."""
        import secrets
        import hashlib
        
        # Generate 32-byte key
        key_bytes = secrets.token_bytes(32)
        full_key = 'ukg_' + secrets.token_urlsafe(32)
        prefix = full_key[:12]
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        
        return full_key, prefix, key_hash
    
    @classmethod
    def verify_key(cls, api_key: str) -> Optional['ExternalAPIKey']:
        """Verify an API key and return the record if valid."""
        import hashlib
        
        if not api_key or not api_key.startswith('ukg_'):
            return None
        
        prefix = api_key[:12]
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        record = cls.query.filter_by(key_prefix=prefix, key_hash=key_hash, is_active=True).first()
        
        if record and record.expires_at and record.expires_at < datetime.now(UTC):
            return None
        
        return record
    
    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'name': self.name,
            'key_prefix': self.key_prefix + '...',
            'user_id': self.user_id,
            'permissions': self.permissions,
            'rate_limit_rpm': self.rate_limit_rpm,
            'rate_limit_daily': self.rate_limit_daily,
            'is_active': self.is_active,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'total_requests': self.total_requests,
            'total_tokens': self.total_tokens,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
