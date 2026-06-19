"""
Database Models for DataLogicEngine.

This module defines the core SQLAlchemy models with:
- Database indexes for performance
- Atomic operations for security
- Type hints for better maintainability
- Proper exception handling
"""

from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any, List
import logging

from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Index, JSON, UUID, LargeBinary
from sqlalchemy import JSON as JSONB
from sqlalchemy.exc import SQLAlchemyError
from cryptography.fernet import Fernet
from flask import current_app
from flask_login import UserMixin
import uuid

from extensions import db

logger = logging.getLogger(__name__)


class User(db.Model, UserMixin):
    """
    User model with security features.

    Includes:
    - Encrypted email field
    - Account lockout with atomic updates
    - MFA support
    - Password policy enforcement
    """

    __tablename__ = 'users'
    __table_args__ = (
        Index('ix_users_username', 'username'),
        Index('ix_users_email', 'email'),
        Index('ix_users_role', 'role'),
        Index('ix_users_active', 'active'),
        Index('ix_users_created_at', 'created_at'),
        Index('ix_users_role_active', 'role', 'active'),
        {'extend_existing': True}
    )

    id: int = db.Column(db.Integer, primary_key=True)

    # Basic fields
    username: str = db.Column(db.String(64), unique=True, nullable=False)
    _email: str = db.Column('email', db.String(255), unique=True, nullable=False)
    password_hash: Optional[str] = db.Column(db.String(256))
    sid: Optional[str] = db.Column(db.String(255), unique=True, nullable=True)  # Windows SID

    @property
    def email(self) -> Optional[str]:
        """Decrypt and return email address."""
        if not self._email:
            return None
        from extensions import encryption_manager
        from cryptography.fernet import InvalidToken
        try:
            return encryption_manager.decrypt(self._email, field_name='email')
        except (InvalidToken, ValueError, TypeError) as e:
            # Fallback for if it's not encrypted yet (during migration)
            logger.debug(f"Email decryption fallback for user {self.id}: {e}")
            return self._email

    @email.setter
    def email(self, value: Optional[str]) -> None:
        """Encrypt and store email address."""
        if not value:
            self._email = None
            return
        from extensions import encryption_manager
        self._email = encryption_manager.encrypt(value, field_name='email')

    active: bool = db.Column(db.Boolean, default=True)
    is_admin: bool = db.Column(db.Boolean, default=False)
    role: str = db.Column(db.String(20), default='user')
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    # MFA fields
    mfa_enabled: bool = db.Column(db.Boolean, default=False)
    mfa_secret: Optional[str] = db.Column(db.String(255))
    backup_codes: Optional[List] = db.Column(JSON)  # Encrypted list of backup codes

    # Account security fields
    failed_login_attempts: int = db.Column(db.Integer, default=0)
    locked_until: Optional[datetime] = db.Column(db.DateTime)
    last_successful_login: Optional[datetime] = db.Column(db.DateTime)
    last_password_change: datetime = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    def set_password(self, password: str) -> None:
        """
        Set user password with strength validation.

        Args:
            password: Plain text password

        Raises:
            ValueError: If password doesn't meet strength requirements
        """
        from backend.security.password_security import PasswordSecurity
        is_strong, errors = PasswordSecurity.validate_password_strength(password)
        if not is_strong:
            raise ValueError(f"Password too weak: {', '.join(errors)}")
        self.password_hash = generate_password_hash(password)
        self.last_password_change = datetime.now(UTC)

    def check_password(self, password: str) -> bool:
        """Verify password against stored hash."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def is_account_locked(self) -> bool:
        """Check if account is currently locked."""
        if self.locked_until and self.locked_until > datetime.now(UTC):
            return True
        return False

    def record_failed_login(self) -> None:
        """
        Record a failed login attempt with atomic update to prevent race conditions.

        Uses direct SQL update to ensure atomicity and prevent concurrent
        requests from bypassing the lockout threshold.
        """
        from backend.config.settings import settings

        try:
            # Atomic increment using SQL UPDATE
            db.session.execute(
                db.update(User)
                .where(User.id == self.id)
                .values(failed_login_attempts=User.failed_login_attempts + 1)
            )
            db.session.commit()

            # Refresh to get updated count
            db.session.refresh(self)

            # Check if we should lock the account
            if self.failed_login_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
                lockout_duration = timedelta(minutes=settings.ACCOUNT_LOCKOUT_MINUTES)
                db.session.execute(
                    db.update(User)
                    .where(User.id == self.id)
                    .values(locked_until=datetime.now(UTC) + lockout_duration)
                )
                db.session.commit()
                logger.warning(
                    f"Account locked for user {self.username} after "
                    f"{self.failed_login_attempts} failed login attempts"
                )

        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Failed to record failed login for user {self.id}: {e}")
            # Re-raise to ensure the caller knows the operation failed
            raise

    def record_successful_login(self) -> None:
        """
        Record a successful login, resetting lockout state.

        Uses atomic update for consistency.
        """
        try:
            db.session.execute(
                db.update(User)
                .where(User.id == self.id)
                .values(
                    failed_login_attempts=0,
                    locked_until=None,
                    last_successful_login=datetime.now(UTC)
                )
            )
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Failed to record successful login for user {self.id}: {e}")
            raise

    def is_password_expired(self) -> bool:
        """Check if password has expired per policy."""
        from backend.security.password_security import PasswordSecurity
        return PasswordSecurity.is_password_expired(self.last_password_change)

    def verify_totp(self, token: str) -> bool:
        """Verify TOTP token for MFA using pyotp directly."""
        if not self.mfa_enabled or not self.mfa_secret:
            return False
        import pyotp
        return pyotp.TOTP(self.mfa_secret).verify(token)

    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary representation."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'active': self.active,
            'is_admin': self.is_admin,
            'role': self.role,
            'mfa_enabled': self.mfa_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_successful_login.isoformat() if self.last_successful_login else None
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'User':
        """Create user instance from dictionary."""
        user = User()
        for field in ['username', 'email', 'role', 'active', 'is_admin']:
            if field in data:
                setattr(user, field, data[field])
        return user

    def __repr__(self) -> str:
        return f'<User {self.username}>'


class APIKey(db.Model):
    """API key used for authenticating programmatic requests."""
    __tablename__ = 'api_keys'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False, default='Default Key')
    key = db.Column(db.String(128), unique=True, nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
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
    __table_args__ = (
        db.UniqueConstraint('provider', 'provider_user_id', name='uq_provider_user'),
        {'extend_existing': True}
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    provider = db.Column(db.String(50), nullable=False)
    provider_user_id = db.Column(db.String(255), nullable=False)
    token = db.Column(db.JSON)
    refresh_token = db.Column(db.String(512))
    token_expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    user = db.relationship('User', backref=db.backref('oauth_accounts', lazy='dynamic'))

    def __repr__(self):
        return f'<OAuthAccount provider={self.provider} user_id={self.user_id}>'


class PasswordHistory(db.Model):
    """Password history for preventing password reuse"""
    __tablename__ = 'password_history'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    def __repr__(self):
        return f'<PasswordHistory user_id={self.user_id} created={self.created_at}>'


class AuditLog(db.Model):
    """Compliance audit log for tracking sensitive system actions."""
    __tablename__ = 'audit_logs'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(UTC), index=True)
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


class SimulationSession(db.Model):
    """Simulation session model with encrypted fields."""

    __tablename__ = 'simulation_sessions'
    __table_args__ = (
        Index('ix_simulation_sessions_user_id', 'user_id'),
        Index('ix_simulation_sessions_status', 'status'),
        Index('ix_simulation_sessions_created_at', 'created_at'),
        Index('ix_simulation_sessions_user_status', 'user_id', 'status'),  # Composite
        {'extend_existing': True}
    )

    id: int = db.Column(db.Integer, primary_key=True)
    session_id: str = db.Column(db.String(36), unique=True, nullable=False)
    user_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    _name: Optional[str] = db.Column('name', db.String(100))
    _description: Optional[str] = db.Column('description', db.Text)

    @property
    def name(self) -> Optional[str]:
        """Decrypt and return simulation name."""
        if not self._name:
            return None
        from extensions import encryption_manager
        try:
            return encryption_manager.decrypt(self._name, field_name='sim_name')
        except (ValueError, TypeError):
            return self._name

    @name.setter
    def name(self, value: Optional[str]) -> None:
        """Encrypt and store simulation name."""
        if not value:
            self._name = None
            return
        from extensions import encryption_manager
        self._name = encryption_manager.encrypt(value, field_name='sim_name')

    @property
    def description(self) -> Optional[str]:
        """Decrypt and return simulation description."""
        if not self._description:
            return None
        from extensions import encryption_manager
        try:
            return encryption_manager.decrypt(self._description, field_name='sim_desc')
        except (ValueError, TypeError):
            return self._description

    @description.setter
    def description(self, value: Optional[str]) -> None:
        """Encrypt and store simulation description."""
        if not value:
            self._description = None
            return
        from extensions import encryption_manager
        self._description = encryption_manager.encrypt(value, field_name='sim_desc')

    parameters: Optional[Dict] = db.Column(JSON)
    status: Optional[str] = db.Column(db.String(20))
    current_step: Optional[int] = db.Column(db.Integer)
    total_steps: Optional[int] = db.Column(db.Integer)
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    started_at: Optional[datetime] = db.Column(db.DateTime)
    completed_at: Optional[datetime] = db.Column(db.DateTime)
    results: Optional[Dict] = db.Column(JSON)

    user = db.relationship('User', backref=db.backref('simulations', lazy='dynamic'))

    def to_dict(self) -> Dict[str, Any]:
        """Convert simulation to dictionary representation."""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'parameters': self.parameters,
            'results': self.results
        }

    def __repr__(self) -> str:
        return f'<SimulationSession {self.session_id}>'


class KnowledgeGraphNode(db.Model):
    """Canonical knowledge graph node model — merged from graph and content node schemas."""

    __tablename__ = 'ukg_knowledge_nodes'
    __table_args__ = (
        Index('ix_ukg_knowledge_nodes_node_type', 'node_type'),
        Index('ix_ukg_knowledge_nodes_axis_number', 'axis_number'),
        Index('ix_ukg_knowledge_nodes_type_axis', 'node_type', 'axis_number'),
        Index('ix_ukg_knowledge_nodes_tenant_id', 'tenant_id'),
        {'extend_existing': True}
    )

    id: int = db.Column(db.Integer, primary_key=True)
    # Graph identity fields
    node_id: str = db.Column(db.String(50), unique=True, nullable=True)
    node_type: Optional[str] = db.Column(db.String(50))
    label: Optional[str] = db.Column(db.String(100))
    description: Optional[str] = db.Column(db.Text)
    axis_number: Optional[int] = db.Column(db.Integer)
    data: Optional[Dict] = db.Column(JSON)
    # Knowledge content fields
    uid: Optional[str] = db.Column(db.String(255), unique=True, nullable=True)
    title: Optional[str] = db.Column(db.String(255), nullable=True)
    content: Optional[str] = db.Column(db.Text, nullable=True)
    content_type: Optional[str] = db.Column(db.String(50), nullable=True)
    pillar_level_id: Optional[int] = db.Column(db.Integer, db.ForeignKey('ukg_pillar_levels.id'), nullable=True)
    domain_id: Optional[int] = db.Column(db.Integer, db.ForeignKey('ukg_domains.id'), nullable=True)
    location_id: Optional[int] = db.Column(db.Integer, db.ForeignKey('ukg_locations.id'), nullable=True)
    time_context_id: Optional[int] = db.Column(db.Integer, db.ForeignKey('ukg_time_contexts.id'), nullable=True)
    node_metadata: Optional[Dict] = db.Column(JSON, nullable=True)
    tenant_id: Optional[str] = db.Column(db.String(64), nullable=True)
    created_at: Optional[datetime] = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at: Optional[datetime] = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Relationships
    integrated_views = db.relationship("IntegratedView", back_populates="knowledge_node", cascade="all, delete-orphan")
    perspectives = db.relationship("Perspective", back_populates="knowledge_node", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation."""
        return {
            'id': self.id,
            'node_id': self.node_id,
            'node_type': self.node_type,
            'label': self.label,
            'description': self.description,
            'axis_number': self.axis_number,
            'data': self.data,
            'uid': self.uid,
            'title': self.title,
            'content': self.content,
            'content_type': self.content_type,
            'pillar_level_id': self.pillar_level_id,
            'domain_id': self.domain_id,
            'location_id': self.location_id,
            'time_context_id': self.time_context_id,
            'metadata': self.node_metadata,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def set_axis_legacy_metadata(
        self,
        *,
        provenance: Optional[str] = None,
        object_type: Optional[str] = None,
        validation_state: Optional[str] = None,
        security_classification: Optional[str] = None,
    ) -> None:
        """Store retired Axis 14-17 concepts as metadata, not coordinate columns."""
        metadata = dict(self.node_metadata or {})
        legacy = dict(metadata.get("legacy_axis_metadata") or {})
        updates = {
            "provenance": provenance,
            "object_type": object_type,
            "validation_state": validation_state,
            "security_classification": security_classification,
        }
        for key, value in updates.items():
            if value is not None:
                legacy[key] = value
        if legacy:
            metadata["legacy_axis_metadata"] = legacy
        self.node_metadata = metadata

    def __repr__(self) -> str:
        return f'<KnowledgeGraphNode {self.node_id or self.uid}>'


class KnowledgeGraphEdge(db.Model):
    """Knowledge graph edge model."""

    __tablename__ = 'ukg_knowledge_edges'
    __table_args__ = (
        Index('ix_ukg_knowledge_edges_source_node_id', 'source_node_id'),
        Index('ix_ukg_knowledge_edges_target_node_id', 'target_node_id'),
        Index('ix_ukg_knowledge_edges_edge_type', 'edge_type'),
        Index('ix_ukg_knowledge_edges_source_target', 'source_node_id', 'target_node_id'),
        {'extend_existing': True}
    )

    id: int = db.Column(db.Integer, primary_key=True)
    edge_id: str = db.Column(db.String(50), unique=True, nullable=False)
    source_node_id: str = db.Column(db.String(50), db.ForeignKey('ukg_knowledge_nodes.node_id'), nullable=False)
    target_node_id: str = db.Column(db.String(50), db.ForeignKey('ukg_knowledge_nodes.node_id'), nullable=False)
    edge_type: Optional[str] = db.Column(db.String(50))
    weight: Optional[float] = db.Column(db.Float)
    data: Optional[Dict] = db.Column(JSON)

    source = db.relationship('KnowledgeGraphNode', foreign_keys=[source_node_id], backref=db.backref('out_edges', lazy='dynamic'))
    target = db.relationship('KnowledgeGraphNode', foreign_keys=[target_node_id], backref=db.backref('in_edges', lazy='dynamic'))

    def to_dict(self) -> Dict[str, Any]:
        """Convert edge to dictionary representation."""
        return {
            'id': self.id,
            'edge_id': self.edge_id,
            'source_id': self.source_node_id,
            'target_id': self.target_node_id,
            'edge_type': self.edge_type,
            'weight': self.weight,
            'data': self.data
        }

    def __repr__(self) -> str:
        return f'<KnowledgeGraphEdge {self.edge_id}>'


class LLMProvider(db.Model):
    """LLM Provider configuration with encrypted API keys."""
    __tablename__ = 'llm_providers'
    __table_args__ = {'extend_existing': True}

    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), nullable=False)
    provider_type = db.Column(db.String(50), nullable=False)
    api_key_encrypted = db.Column(LargeBinary, nullable=True)
    endpoint = db.Column(db.String(500), nullable=True)
    model_id = db.Column(db.String(100), nullable=True)
    deployment_name = db.Column(db.String(100), nullable=True)
    api_version = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_default = db.Column(db.Boolean, default=False)
    priority = db.Column(db.Integer, default=100)
    rate_limit_rpm = db.Column(db.Integer, nullable=True)
    rate_limit_tpm = db.Column(db.Integer, nullable=True)
    timeout_seconds = db.Column(db.Integer, default=30)
    max_retries = db.Column(db.Integer, default=3)
    config = db.Column(JSON, nullable=True)
    tenant_id = db.Column(db.String(100), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    last_used_at = db.Column(db.DateTime, nullable=True)
    
    usage_records = db.relationship('LLMProviderUsage', backref='provider', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_api_key(self, api_key: str) -> None:
        key = current_app.config.get('ENCRYPTION_KEY')
        if not key:
            import hashlib
            import base64
            secret = current_app.config.get('SECRET_KEY', 'default-secret')
            key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
        f = Fernet(key)
        self.api_key_encrypted = f.encrypt(api_key.encode())
    
    def get_api_key(self) -> Optional[str]:
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
        except Exception as _exc:
            _log = logging.getLogger(__name__)
            _log.warning(
                "LLMProvider(%s, type=%s): failed to decrypt stored API key — "
                "the key may have been saved with a different SESSION_SECRET. "
                "Re-save the API key in Settings to fix this. Error: %s",
                self.id,
                self.provider_type,
                _exc,
            )
            return None

    def to_dict(self, include_key: bool = False) -> dict:
        result = {
            'id': str(self.id),
            'name': self.name,
            'provider_type': self.provider_type,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'has_api_key': self.api_key_encrypted is not None,
        }
        return result


class LLMProviderUsage(db.Model):
    """Usage tracking for LLM providers."""
    __tablename__ = 'llm_provider_usage'
    __table_args__ = {'extend_existing': True}

    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = db.Column(UUID(as_uuid=True), db.ForeignKey('llm_providers.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    api_key_id = db.Column(UUID(as_uuid=True), db.ForeignKey('external_api_keys.id'), nullable=True)
    run_id = db.Column(UUID(as_uuid=True), nullable=True)
    model = db.Column(db.String(100), nullable=True)
    tokens_in = db.Column(db.Integer, default=0)
    tokens_out = db.Column(db.Integer, default=0)
    latency_ms = db.Column(db.Integer, nullable=True)
    estimated_cost_usd = db.Column(db.Float, nullable=True)
    success = db.Column(db.Boolean, default=True)
    error_code = db.Column(db.String(100), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))


class PromptTemplate(db.Model):
    """Versioned prompt template registry."""
    __tablename__ = 'prompt_templates'
    __table_args__ = (
        Index('ix_prompt_templates_key', 'template_key'),
        Index('ix_prompt_templates_active', 'is_active'),
        Index('ix_prompt_templates_approval', 'approval_state'),
        Index('ix_prompt_templates_key_version', 'template_key', 'version', unique=True),
        {'extend_existing': True},
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_key = db.Column(db.String(120), nullable=False)
    version = db.Column(db.String(40), nullable=False, default='1.0.0')
    template_body = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    template_metadata = db.Column('metadata', JSON, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    # Approval workflow
    approval_state = db.Column(db.String(30), nullable=False, default='draft')  # draft | pending_review | approved | rejected
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    rejected_reason = db.Column(db.Text, nullable=True)
    submitted_for_review_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'template_key': self.template_key,
            'version': self.version,
            'template_body': self.template_body,
            'description': self.description,
            'metadata': self.template_metadata or {},
            'is_active': self.is_active,
            'approval_state': self.approval_state,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'rejected_reason': self.rejected_reason,
            'submitted_for_review_at': self.submitted_for_review_at.isoformat() if self.submitted_for_review_at else None,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class FeatureFlag(db.Model):
    """Runtime feature flag registry with per-tenant targeting."""
    __tablename__ = 'feature_flags'
    __table_args__ = (
        Index('ix_feature_flags_key', 'flag_key', unique=True),
        {'extend_existing': True},
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flag_key = db.Column(db.String(120), nullable=False)
    value = db.Column(db.Boolean, nullable=False, default=False)
    description = db.Column(db.String(255), nullable=True)
    rollout_percentage = db.Column(db.Integer, nullable=False, default=100)  # 0-100
    target_roles = db.Column(JSON, nullable=True)  # list of role strings, null = all roles
    is_locked = db.Column(db.Boolean, nullable=False, default=False)  # prevents local overrides
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'flag_key': self.flag_key,
            'value': self.value,
            'description': self.description,
            'rollout_percentage': self.rollout_percentage,
            'target_roles': self.target_roles,
            'is_locked': self.is_locked,
            'updated_by': self.updated_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class FeatureFlagAuditEvent(db.Model):
    """Immutable audit log for feature flag changes."""
    __tablename__ = 'feature_flag_audit_events'
    __table_args__ = (
        Index('ix_feature_flag_audit_key', 'flag_key'),
        Index('ix_feature_flag_audit_actor', 'actor_id'),
        {'extend_existing': True},
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flag_key = db.Column(db.String(120), nullable=False)
    old_value = db.Column(db.Boolean, nullable=True)
    new_value = db.Column(db.Boolean, nullable=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    actor_username = db.Column(db.String(120), nullable=True)
    change_reason = db.Column(db.Text, nullable=True)
    source = db.Column(db.String(30), nullable=False, default='api')  # api | migration | seed
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'flag_key': self.flag_key,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'actor_id': self.actor_id,
            'actor_username': self.actor_username,
            'change_reason': self.change_reason,
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ModelRoutingPolicy(db.Model):
    """Versioned model routing policy registry."""
    __tablename__ = 'model_routing_policies'
    __table_args__ = (
        Index('ix_model_routing_policy_name', 'policy_name'),
        Index('ix_model_routing_policy_active', 'is_active'),
        Index('ix_model_routing_policy_name_version', 'policy_name', 'version', unique=True),
        {'extend_existing': True},
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_name = db.Column(db.String(120), nullable=False)
    version = db.Column(db.String(40), nullable=False, default='1.0.0')
    rules = db.Column(JSON, nullable=False, default=dict)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'policy_name': self.policy_name,
            'version': self.version,
            'rules': self.rules or {},
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class AIAuditEvent(db.Model):
    """AI governance audit trail with model/policy metadata."""
    __tablename__ = 'ai_audit_events'
    __table_args__ = (
        Index('ix_ai_audit_run_id', 'run_id'),
        Index('ix_ai_audit_created_at', 'created_at'),
        Index('ix_ai_audit_model', 'model'),
        {'extend_existing': True},
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    api_key_id = db.Column(UUID(as_uuid=True), db.ForeignKey('external_api_keys.id'), nullable=True)
    provider = db.Column(db.String(100), nullable=True)
    model = db.Column(db.String(120), nullable=False)
    model_version = db.Column(db.String(60), nullable=False, default='unknown')
    prompt_template_key = db.Column(db.String(120), nullable=True)
    prompt_template_version = db.Column(db.String(40), nullable=True)
    routing_policy_name = db.Column(db.String(120), nullable=True)
    routing_policy_version = db.Column(db.String(40), nullable=True)
    classification = db.Column(JSON, nullable=True)
    governance_flags = db.Column(JSON, nullable=True)
    request_tokens_estimate = db.Column(db.Integer, nullable=True)
    tokens_in = db.Column(db.Integer, nullable=True)
    tokens_out = db.Column(db.Integer, nullable=True)
    estimated_cost_usd = db.Column(db.Float, nullable=True)
    success = db.Column(db.Boolean, default=True)
    error_code = db.Column(db.String(100), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    event_metadata = db.Column('metadata', JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': str(self.id),
            'run_id': str(self.run_id) if self.run_id else None,
            'user_id': self.user_id,
            'api_key_id': str(self.api_key_id) if self.api_key_id else None,
            'provider': self.provider,
            'model': self.model,
            'model_version': self.model_version,
            'prompt_template_key': self.prompt_template_key,
            'prompt_template_version': self.prompt_template_version,
            'routing_policy_name': self.routing_policy_name,
            'routing_policy_version': self.routing_policy_version,
            'classification': self.classification,
            'governance_flags': self.governance_flags,
            'request_tokens_estimate': self.request_tokens_estimate,
            'tokens_in': self.tokens_in,
            'tokens_out': self.tokens_out,
            'estimated_cost_usd': self.estimated_cost_usd,
            'success': self.success,
            'error_code': self.error_code,
            'error_message': self.error_message,
            'metadata': self.event_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class ExternalAPIKey(db.Model):
    """API keys for external clients."""
    __tablename__ = 'external_api_keys'
    __table_args__ = {'extend_existing': True}

    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), nullable=False)
    key_prefix = db.Column(db.String(12), nullable=False)
    key_hash = db.Column(db.String(256), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Missing fields required by LLM Gateway
    total_requests = db.Column(db.Integer, default=0)
    last_used_at = db.Column(db.DateTime)
    rate_limit_rpm = db.Column(db.Integer, default=60)
    rate_limit_daily = db.Column(db.Integer)
    max_tokens_per_request = db.Column(db.Integer)
    permissions = db.Column(db.JSON)
    allowed_providers = db.Column(db.JSON)
    allowed_models = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    expires_at = db.Column(db.DateTime, nullable=True)
    
    usage_records = db.relationship('LLMProviderUsage', backref='api_key', lazy='dynamic')

    @staticmethod
    def generate_key():
        """Generate a new secure API key."""
        import secrets
        import hashlib
        prefix = f"ukg_{secrets.token_hex(4)}"
        secret = secrets.token_urlsafe(32)
        full_key = f"{prefix}_{secret}"
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        return full_key, prefix, key_hash

    @classmethod
    def verify_key(cls, full_key: str):
        """Verify an API key and return the record."""
        import hashlib
        if not full_key or '_' not in full_key:
            return None
        
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        key_record = cls.query.filter_by(key_hash=key_hash, is_active=True).first()
        if not key_record:
            return None

        expires_at = getattr(key_record, 'expires_at', None)
        if expires_at:
            now = datetime.now(UTC)
            if expires_at.tzinfo is None:
                now = now.replace(tzinfo=None)
            if expires_at <= now:
                return None

        return key_record

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'prefix': self.key_prefix,
            'is_active': self.is_active,
            'total_requests': self.total_requests,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }


class ChatSession(db.Model):
    """A collection of related messages."""
    __tablename__ = 'chat_sessions'
    __table_args__ = {'extend_existing': True}

    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=True)
    model = db.Column(db.String(100), nullable=True)
    mode = db.Column(db.String(50), default='chat')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    messages = db.relationship('ChatMessage', backref='session', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'title': self.title,
            'model': self.model,
            'mode': self.mode,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ChatMessage(db.Model):
    """A single turn in a chat session."""
    __tablename__ = 'chat_messages'
    __table_args__ = {'extend_existing': True}

    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = db.Column(UUID(as_uuid=True), db.ForeignKey('chat_sessions.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    run_id = db.Column(UUID(as_uuid=True), nullable=True)
    is_enhanced = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
