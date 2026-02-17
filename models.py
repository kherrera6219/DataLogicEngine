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
        try:
            return encryption_manager.decrypt(self._email, field_name='email')
        except (ValueError, TypeError) as e:
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
        """Verify TOTP token for MFA."""
        if not self.mfa_enabled or not self.mfa_secret:
            return False
        from backend.security.mfa import MFAManager
        return MFAManager.verify_totp(self.mfa_secret, token)

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
    """Knowledge graph node model."""

    __tablename__ = 'ukg_knowledge_nodes'
    __table_args__ = (
        Index('ix_ukg_knowledge_nodes_node_type', 'node_type'),
        Index('ix_ukg_knowledge_nodes_axis_number', 'axis_number'),
        Index('ix_ukg_knowledge_nodes_type_axis', 'node_type', 'axis_number'),
        {'extend_existing': True}
    )

    id: int = db.Column(db.Integer, primary_key=True)
    node_id: str = db.Column(db.String(50), unique=True, nullable=False)
    node_type: Optional[str] = db.Column(db.String(50))
    label: Optional[str] = db.Column(db.String(100))
    description: Optional[str] = db.Column(db.Text)
    axis_number: Optional[int] = db.Column(db.Integer)
    data: Optional[Dict] = db.Column(JSON)

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
            'data': self.data
        }

    def __repr__(self) -> str:
        return f'<KnowledgeGraphNode {self.node_id}>'


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
        if not self.api_key_encrypted: return None
        try:
            key = current_app.config.get('ENCRYPTION_KEY')
            if not key:
                import hashlib
                import base64
                secret = current_app.config.get('SECRET_KEY', 'default-secret')
                key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
            f = Fernet(key)
            return f.decrypt(self.api_key_encrypted).decode()
        except: return None

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
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
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
        return cls.query.filter_by(key_hash=key_hash, is_active=True).first()

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'prefix': self.key_prefix,
            'is_active': self.is_active,
            'total_requests': self.total_requests,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
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


class TraceRun(db.Model):
    """Top-level trace run capturing a complete chat interaction."""
    __tablename__ = 'trace_runs'

    __table_args__ = (
        Index('ix_trace_runs_session_id', 'session_id'),
        Index('ix_trace_runs_user_id', 'user_id'),
        Index('ix_trace_runs_created_at', 'created_at'),
        Index('ix_trace_runs_status', 'status'),
        {'extend_existing': True}
    )

    run_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = db.Column(UUID(as_uuid=True), nullable=True)
    tenant_id = db.Column(db.String(100), nullable=True)
    workspace_id = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    correlation_id = db.Column(db.String(100), nullable=True)

    # Status and timing
    status = db.Column(db.String(20), default='running')  # running, pass, warn, fail
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    completed_at = db.Column(db.DateTime, nullable=True)

    # Model and policy context
    model_name = db.Column(db.String(100), nullable=True)
    model_version = db.Column(db.String(50), nullable=True)
    policy_pack_id = db.Column(db.String(100), nullable=True)
    policy_pack_version = db.Column(db.String(50), nullable=True)

    # Data snapshot references
    data_snapshot = db.Column(JSONB, nullable=True)  # ukg_snapshot, uskd_snapshot, index_versions

    # Scores
    confidence = db.Column(db.Float, default=0.0)
    entropy = db.Column(db.Float, default=0.0)
    bias_risk = db.Column(db.Float, default=0.0)

    # Input/Output
    input_message = db.Column(db.Text, nullable=True)
    final_answer = db.Column(db.Text, nullable=True)

    # Relationships
    stages = db.relationship('TraceStage', backref='run', lazy='dynamic', cascade='all, delete-orphan')
    evidence_items = db.relationship('TraceEvidence', backref='run', lazy='dynamic', cascade='all, delete-orphan')
    claims = db.relationship('TraceClaim', backref='run', lazy='dynamic', cascade='all, delete-orphan')
    personas = db.relationship('TracePersona', backref='run', lazy='dynamic', cascade='all, delete-orphan')
    ka_invocations = db.relationship('TraceKAInvocation', backref='run', lazy='dynamic', cascade='all, delete-orphan')
    policy_decisions = db.relationship('TracePolicyDecision', backref='run', lazy='dynamic', cascade='all, delete-orphan')
    memory_events = db.relationship('TraceMemoryEvent', backref='run', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'run_id': str(self.run_id),
            'session_id': str(self.session_id) if self.session_id else None,
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'model': {'name': self.model_name, 'version': self.model_version},
            'policy_pack': {'id': self.policy_pack_id, 'version': self.policy_pack_version},
            'data_snapshot': self.data_snapshot,
            'scores': {
                'confidence': self.confidence,
                'entropy': self.entropy,
                'bias_risk': self.bias_risk
            },
            'input_message': self.input_message,
            'final_answer': self.final_answer
        }


class TraceStage(db.Model):
    """Individual stage in the execution pipeline (Layer 1-10 or Step 1-12)."""
    __tablename__ = 'trace_stages'

    __table_args__ = (
        Index('ix_trace_stages_run_id', 'run_id'),
        Index('ix_trace_stages_layer_index', 'layer_index'),
        Index('ix_trace_stages_step_index', 'step_index'),
        {'extend_existing': True}
    )

    stage_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)

    # Stage identification
    name = db.Column(db.String(100), nullable=False)
    stage_type = db.Column(db.String(20), default='layer')  # layer, step
    layer_index = db.Column(db.Integer, nullable=True)  # 1-10 for layers
    step_index = db.Column(db.Integer, nullable=True)   # 1-12 for steps

    # Status and timing
    status = db.Column(db.String(20), default='running')  # running, pass, warn, fail, skipped
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    duration_ms = db.Column(db.Integer, nullable=True)

    # Inputs/Outputs (artifact references)
    inputs = db.Column(JSONB, nullable=True)   # [{artifact_id, label}]
    outputs = db.Column(JSONB, nullable=True)  # [{artifact_id, label}]

    # Decisions made at this stage
    decisions = db.Column(JSONB, nullable=True)  # [{description, rationale, alternatives}]

    # Metrics
    metrics = db.Column(JSONB, nullable=True)  # tokens_in, tokens_out, retrieval_count, cache_hits, retries

    def to_dict(self):
        return {
            'stage_id': str(self.stage_id),
            'run_id': str(self.run_id),
            'name': self.name,
            'type': self.stage_type,
            'layer_index': self.layer_index,
            'step_index': self.step_index,
            'status': self.status,
            'timing': {
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'end_time': self.end_time.isoformat() if self.end_time else None,
                'duration_ms': self.duration_ms
            },
            'inputs': self.inputs,
            'outputs': self.outputs,
            'decisions': self.decisions,
            'metrics': self.metrics
        }


class TraceEvidence(db.Model):
    """Evidence item used in a run."""
    __tablename__ = 'trace_evidence'

    __table_args__ = (
        Index('ix_trace_evidence_run_id', 'run_id'),
        Index('ix_trace_evidence_source_type', 'source_type'),
        {'extend_existing': True}
    )

    evidence_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)

    # Source information
    source_type = db.Column(db.String(50), nullable=True)  # doc, url, db_record, user_upload
    source_id = db.Column(db.String(255), nullable=True)
    source_title = db.Column(db.String(500), nullable=True)
    authority = db.Column(db.String(20), default='medium')  # high, medium, low

    # Location within source
    locator = db.Column(JSONB, nullable=True)  # page, section, line_range, url

    # Content
    snippet = db.Column(db.Text, nullable=True)
    content_hash = db.Column(db.String(100), nullable=True)  # sha256

    # Retrieval metadata
    retrieval_method = db.Column(db.String(50), nullable=True)  # vector, graph, rules, manual
    relevance_score = db.Column(db.Float, nullable=True)
    axis_match_score = db.Column(db.Float, nullable=True)

    # Usage tracking
    used_by_claims = db.Column(JSONB, nullable=True)    # [claim_id]
    used_by_personas = db.Column(JSONB, nullable=True)  # [persona_id]
    used_by_stages = db.Column(JSONB, nullable=True)    # [stage_id]

    # Conflicts
    conflicts_with = db.Column(JSONB, nullable=True)  # [evidence_id]

    def to_dict(self):
        return {
            'evidence_id': str(self.evidence_id),
            'run_id': str(self.run_id),
            'source': {
                'type': self.source_type,
                'id': self.source_id,
                'title': self.source_title,
                'authority': self.authority
            },
            'locator': self.locator,
            'snippet': self.snippet,
            'hash': self.content_hash,
            'retrieval': {
                'method': self.retrieval_method,
                'relevance_score': self.relevance_score,
                'axis_match': self.axis_match_score
            },
            'used_by': {
                'claims': self.used_by_claims,
                'personas': self.used_by_personas,
                'stages': self.used_by_stages
            },
            'conflicts_with': self.conflicts_with
        }


class TraceClaim(db.Model):
    """Individual claim extracted from the final answer."""
    __tablename__ = 'trace_claims'

    claim_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)

    # Claim content
    text = db.Column(db.Text, nullable=False)
    answer_span_start = db.Column(db.Integer, nullable=True)
    answer_span_end = db.Column(db.Integer, nullable=True)

    # Support status
    status = db.Column(db.String(20), default='pending')  # supported, partial, unsupported, contested
    confidence = db.Column(db.Float, default=0.0)

    # Evidence links
    evidence_ids = db.Column(JSONB, nullable=True)  # [evidence_id]
    stage_ids = db.Column(JSONB, nullable=True)     # [stage_id]

    def to_dict(self):
        return {
            'claim_id': str(self.claim_id),
            'run_id': str(self.run_id),
            'text': self.text,
            'answer_span': {'start': self.answer_span_start, 'end': self.answer_span_end},
            'support': {
                'status': self.status,
                'confidence': self.confidence,
                'evidence_ids': self.evidence_ids,
                'stage_ids': self.stage_ids
            }
        }


class TraceAxisVector(db.Model):
    """17-axis coordinate vector for a run."""
    __tablename__ = 'trace_axis_vectors'

    vector_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False, unique=True)

    # Per-axis data
    axes = db.Column(JSONB, nullable=False)  # [{axis_id, name, selected, candidates, trigger_evidence}]

    # Coordinate hash for comparison
    coordinate_hash = db.Column(db.String(100), nullable=True)

    def to_dict(self):
        return {
            'vector_id': str(self.vector_id),
            'run_id': str(self.run_id),
            'axes': self.axes,
            'coordinate_hash': self.coordinate_hash
        }


class TracePersona(db.Model):
    """Persona execution trace (Quad Persona + custom)."""
    __tablename__ = 'trace_personas'

    persona_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)

    # Persona identification
    persona_type = db.Column(db.String(50), nullable=False)  # analyst, expert, critic, synthesizer, custom
    persona_name = db.Column(db.String(100), nullable=True)

    # Status
    status = db.Column(db.String(20), default='pending')  # pending, running, pass, warn, fail

    # Inputs (what this persona was given)
    evidence_ids = db.Column(JSONB, nullable=True)
    context_scope = db.Column(db.Text, nullable=True)

    # Output
    draft_text = db.Column(db.Text, nullable=True)
    confidence = db.Column(db.Float, default=0.0)

    # Objections and consensus
    objections = db.Column(JSONB, nullable=True)  # [{type, detail}]
    consensus_impact = db.Column(JSONB, nullable=True)  # {changed_answer, delta_summary}

    def to_dict(self):
        return {
            'persona_id': str(self.persona_id),
            'run_id': str(self.run_id),
            'persona_type': self.persona_type,
            'persona_name': self.persona_name,
            'status': self.status,
            'inputs': {
                'evidence_ids': self.evidence_ids,
                'context_scope': self.context_scope
            },
            'draft': {
                'text': self.draft_text,
                'confidence': self.confidence
            },
            'objections': self.objections,
            'consensus_impact': self.consensus_impact
        }


class TraceKAInvocation(db.Model):
    """Knowledge Algorithm invocation trace."""
    __tablename__ = 'trace_ka_invocations'

    invocation_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)
    stage_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_stages.stage_id'), nullable=True)

    # KA identification
    ka_id = db.Column(db.String(100), nullable=False)
    ka_name = db.Column(db.String(200), nullable=True)
    ka_version = db.Column(db.String(50), nullable=True)

    # Execution
    status = db.Column(db.String(20), default='pending')
    duration_ms = db.Column(db.Integer, nullable=True)

    # Inputs/Outputs
    inputs = db.Column(JSONB, nullable=True)
    outputs = db.Column(JSONB, nullable=True)

    # Routing decision
    routing = db.Column(JSONB, nullable=True)  # {complexity_score, axis_triggers, reason}

    # Side effects
    side_effects = db.Column(JSONB, nullable=True)  # [{type, ref_id}]

    def to_dict(self):
        return {
            'invocation_id': str(self.invocation_id),
            'run_id': str(self.run_id),
            'stage_id': str(self.stage_id) if self.stage_id else None,
            'ka_id': self.ka_id,
            'ka_name': self.ka_name,
            'ka_version': self.ka_version,
            'status': self.status,
            'timing': {'duration_ms': self.duration_ms},
            'inputs': self.inputs,
            'outputs': self.outputs,
            'routing': self.routing,
            'side_effects': self.side_effects
        }


class TracePolicyDecision(db.Model):
    """Policy/guardrail decision trace."""
    __tablename__ = 'trace_policy_decisions'

    decision_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)
    stage_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_stages.stage_id'), nullable=True)

    # Policy identification
    policy_id = db.Column(db.String(100), nullable=False)
    policy_name = db.Column(db.String(200), nullable=True)
    rule_id = db.Column(db.String(100), nullable=True)

    # Decision
    decision = db.Column(db.String(20), nullable=False)  # allow, block, flag, redact
    rationale = db.Column(db.Text, nullable=True)
    sensitivity_score = db.Column(db.Float, default=0.0)

    # Modifications (if redacted)
    modifications = db.Column(JSONB, nullable=True)  # [{type, original, replacement}]

    def to_dict(self):
        return {
            'decision_id': str(self.decision_id),
            'run_id': str(self.run_id),
            'stage_id': str(self.stage_id) if self.stage_id else None,
            'policy': {'id': self.policy_id, 'name': self.policy_name, 'rule_id': self.rule_id},
            'decision': self.decision,
            'rationale': self.rationale,
            'sensitivity': self.sensitivity_score,
            'modifications': self.modifications
        }


class TraceMemoryEvent(db.Model):
    """Event capturing memory interaction during a run."""
    __tablename__ = 'trace_memory_events'

    event_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)

    # Event identification
    event_type = db.Column(db.String(50), nullable=False)  # recall, commit, forget, consolidate
    memory_type = db.Column(db.String(20), default='short')  # short, long, semantic, episodic

    # Content
    content = db.Column(JSONB, nullable=False)
    context_keys = db.Column(JSONB, nullable=True)

    # Impact
    impact_score = db.Column(db.Float, default=0.0)

    def to_dict(self):
        return {
            'event_id': str(self.event_id),
            'run_id': str(self.run_id),
            'type': self.event_type,
            'memory_type': self.memory_type,
            'content': self.content,
            'context': self.context_keys,
            'impact': self.impact_score
        }


class TraceArtifact(db.Model):
    """Intermediate artifact generated during a run."""
    __tablename__ = 'trace_artifacts'

    artifact_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)
    stage_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_stages.stage_id'), nullable=True)

    # Artifact metadata
    label = db.Column(db.String(100), nullable=False)
    artifact_type = db.Column(db.String(50), nullable=True)  # code, diagram, summary, search_query
    media_type = db.Column(db.String(100), default='text/plain')

    # Content
    content = db.Column(db.Text, nullable=False)
    version = db.Column(db.Integer, default=1)

    # Redaction status
    is_redacted = db.Column(db.Boolean, default=False)
    redaction_level = db.Column(db.String(20), nullable=True)

    def to_dict(self):
        return {
            'artifact_id': str(self.artifact_id),
            'run_id': str(self.run_id),
            'stage_id': str(self.stage_id) if self.stage_id else None,
            'label': self.label,
            'type': self.artifact_type,
            'media_type': self.media_type,
            'content': self.content,
            'version': self.version,
            'is_redacted': self.is_redacted
        }


class ClaimEvidenceLink(db.Model):
    """Explicit link between claims and evidence with confidence."""
    __tablename__ = 'claim_evidence_links'

    id = db.Column(db.Integer, primary_key=True)
    claim_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_claims.claim_id'), nullable=False)
    evidence_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_evidence.evidence_id'), nullable=False)

    confidence = db.Column(db.Float, default=1.0)
    rationale = db.Column(db.Text, nullable=True)


class TraceSpan(db.Model):
    """Detailed timing span for performance tracing."""
    __tablename__ = 'trace_spans'

    span_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)
    parent_id = db.Column(UUID(as_uuid=True), nullable=True)

    name = db.Column(db.String(200), nullable=False)
    service = db.Column(db.String(100), nullable=True)

    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    tags = db.Column(JSONB, nullable=True)


class StageLog(db.Model):
    """Raw logs from a specific stage."""
    __tablename__ = 'trace_stage_logs'

    log_id = db.Column(db.Integer, primary_key=True)
    stage_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_stages.stage_id'), nullable=False)

    level = db.Column(db.String(20), default='info')
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    extra = db.Column(JSONB, nullable=True)


class TraceExport(db.Model):
    """History of trace exports."""
    __tablename__ = 'trace_exports'

    export_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)

    format = db.Column(db.String(20), default='json')
    destination = db.Column(db.String(100), nullable=True)  # s3, local, webhook
    exported_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)


class ComplianceMapping(db.Model):
    """Mapping of trace data to compliance requirements."""
    __tablename__ = 'compliance_mappings'

    mapping_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)

    framework = db.Column(db.String(50), nullable=False)  # gdpr, soc2, hipaa
    control_id = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='compliant')
    evidence_refs = db.Column(JSONB, nullable=True)


class ArtifactRedaction(db.Model):
    """Record of redaction operations on artifacts."""
    __tablename__ = 'artifact_redactions'

    redaction_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artifact_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_artifacts.artifact_id'), nullable=False)

    rule_id = db.Column(db.String(100), nullable=True)
    redactor_name = db.Column(db.String(100), nullable=True)
    pattern_matched = db.Column(db.String(255), nullable=True)

    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(UTC))


class EvidenceConflict(db.Model):
    """Record of identified evidence conflicts."""
    __tablename__ = 'evidence_conflicts'

    conflict_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)

    evidence_a_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_evidence.evidence_id'), nullable=False)
    evidence_b_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_evidence.evidence_id'), nullable=False)

    conflict_type = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    resolution = db.Column(db.String(100), nullable=True)


class PersonaEvidenceLink(db.Model):
    """Link between persona and evidence items."""
    __tablename__ = 'persona_evidence_links'

    id = db.Column(db.Integer, primary_key=True)
    persona_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_personas.persona_id'), nullable=False)
    evidence_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_evidence.evidence_id'), nullable=False)


class StageArtifactLink(db.Model):
    """Link between stage and its artifacts."""
    __tablename__ = 'stage_artifact_links'

    id = db.Column(db.Integer, primary_key=True)
    stage_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_stages.stage_id'), nullable=False)
    artifact_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_artifacts.artifact_id'), nullable=False)

    role = db.Column(db.String(20), default='output')  # input, output


class KAArtifactLink(db.Model):
    """Link between KA invocation and artifacts."""
    __tablename__ = 'ka_artifact_links'

    id = db.Column(db.Integer, primary_key=True)
    invocation_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_ka_invocations.invocation_id'), nullable=False)
    artifact_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_artifacts.artifact_id'), nullable=False)

    role = db.Column(db.String(20), default='output')

class Persona(db.Model):
    """Model for Personas in the Quad Persona System."""
    __tablename__ = 'ukg_personas'
    
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(255), unique=True, nullable=False)
    persona_id = db.Column(db.String(50), unique=True, nullable=False)  # e.g., "analyst", "explorer"
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    traits = db.Column(JSON, nullable=True)
    strengths = db.Column(JSON, nullable=True) # Assuming JSON from previous view
    focus = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # Relationships
    perspectives = db.relationship("Perspective", back_populates="persona", foreign_keys="Perspective.persona_id")
    
    def to_dict(self):
        """Convert persona to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'persona_id': self.persona_id,
            'name': self.name,
            'description': self.description,
            'traits': self.traits,
            'strengths': self.strengths,
            'focus': self.focus,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Perspective(db.Model):
    """Model for Perspectives generated by personas on knowledge nodes."""
    __tablename__ = 'ukg_perspectives'
    
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(255), unique=True, nullable=False)
    persona_id = db.Column(db.Integer, db.ForeignKey('ukg_personas.id'), nullable=False)
    knowledge_node_id = db.Column(db.Integer, db.ForeignKey('ukg_knowledge_nodes.id'), nullable=False)
    key_insights = db.Column(JSON, nullable=True)
    strengths_identified = db.Column(JSON, nullable=True)
    blind_spots = db.Column(JSON, nullable=True)
    recommendations = db.Column(JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # Relationships
    persona = db.relationship("Persona", back_populates="perspectives", foreign_keys=[persona_id])
    knowledge_node = db.relationship("KnowledgeGraphNode", back_populates="perspectives", foreign_keys=[knowledge_node_id])
    
    def to_dict(self):
        """Convert perspective to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'persona_id': self.persona_id,
            'knowledge_node_id': self.knowledge_node_id,
            'key_insights': self.key_insights,
            'strengths_identified': self.strengths_identified,
            'blind_spots': self.blind_spots,
            'recommendations': self.recommendations,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class IntegratedView(db.Model):
    """Model for Integrated Views synthesized from multiple perspectives."""
    __tablename__ = 'ukg_integrated_views'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(255), unique=True, nullable=False)
    knowledge_node_id = db.Column(db.Integer, db.ForeignKey('ukg_knowledge_nodes.id'), nullable=False)
    synthesis_method = db.Column(db.String(100), nullable=False)
    key_insights = db.Column(JSON, nullable=True)
    comprehensive_strengths = db.Column(JSON, nullable=True)
    potential_limitations = db.Column(JSON, nullable=True)
    balanced_recommendations = db.Column(JSON, nullable=True)
    perspectives = db.Column(JSON, nullable=True)  # Store IDs of contributing perspectives
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # Relationships
    knowledge_node = db.relationship("KnowledgeGraphNode", back_populates="integrated_views")
    
    def to_dict(self):
        """Convert integrated view to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'knowledge_node_id': self.knowledge_node_id,
            'synthesis_method': self.synthesis_method,
            'key_insights': self.key_insights,
            'comprehensive_strengths': self.comprehensive_strengths,
            'potential_limitations': self.potential_limitations,
            'balanced_recommendations': self.balanced_recommendations,
            'perspectives': self.perspectives,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Compatibility Aliases
# APIKey = ExternalAPIKey  # Replaced by direct class definition

class MCPServer(db.Model):
    """Model for MCP server configurations"""
    __tablename__ = 'mcp_servers'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False)
    version = db.Column(db.String(32), default='1.0.0')
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='inactive')  # active, inactive, error
    protocol_version = db.Column(db.String(32), default='2024-11-05')

    # Capabilities
    supports_resources = db.Column(db.Boolean, default=True)
    supports_tools = db.Column(db.Boolean, default=True)
    supports_prompts = db.Column(db.Boolean, default=True)
    supports_logging = db.Column(db.Boolean, default=True)

    # Configuration
    config = db.Column(db.JSON)
    server_metadata = db.Column(db.JSON)

    # Stats
    total_requests = db.Column(db.Integer, default=0)
    successful_requests = db.Column(db.Integer, default=0)
    failed_requests = db.Column(db.Integer, default=0)
    tenant_id = db.Column(db.String(64), index=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    last_active = db.Column(db.DateTime)

    # Relationships
    resources = db.relationship('MCPResource', backref='server', lazy='dynamic', cascade='all, delete-orphan')
    tools = db.relationship('MCPTool', backref='server', lazy='dynamic', cascade='all, delete-orphan')
    prompts = db.relationship('MCPPrompt', backref='server', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        """Convert server to dictionary"""
        return {
            'id': self.id,
            'server_id': self.server_id,
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'status': self.status,
            'protocol_version': self.protocol_version,
            'capabilities': {
                'resources': self.supports_resources,
                'tools': self.supports_tools,
                'prompts': self.supports_prompts,
                'logging': self.supports_logging
            }
        ,
            'config': self.config,
            'metadata': self.server_metadata,
            'stats': {
                'total_requests': self.total_requests,
                'successful_requests': self.successful_requests,
                'failed_requests': self.failed_requests
            },
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_active': self.last_active.isoformat() if self.last_active else None
        }


class MCPResource(db.Model):
    """Model for MCP resources"""
    __tablename__ = 'mcp_resources'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey('mcp_servers.id'), nullable=False)
    uri = db.Column(db.String(256), nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    mime_type = db.Column(db.String(64))

    # Resource metadata
    resource_metadata = db.Column(db.JSON)

    # Access stats
    access_count = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime)
    tenant_id = db.Column(db.String(64), index=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    def to_dict(self):
        """Convert resource to dictionary"""
        return {
            'id': self.id,
            'server_id': self.server_id,
            'uri': self.uri,
            'name': self.name,
            'description': self.description,
            'mime_type': self.mime_type,
            'metadata': self.resource_metadata,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class MCPTool(db.Model):
    """Model for MCP tools"""
    __tablename__ = 'mcp_tools'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey('mcp_servers.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)

    # Tool schema
    input_schema = db.Column(db.JSON, nullable=False)

    # Tool metadata
    tool_metadata = db.Column(db.JSON)

    # Execution stats
    execution_count = db.Column(db.Integer, default=0)
    success_count = db.Column(db.Integer, default=0)
    failure_count = db.Column(db.Integer, default=0)
    last_executed = db.Column(db.DateTime)
    tenant_id = db.Column(db.String(64), index=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    def to_dict(self):
        """Convert tool to dictionary"""
        return {
            'id': self.id,
            'server_id': self.server_id,
            'name': self.name,
            'description': self.description,
            'input_schema': self.input_schema,
            'metadata': self.tool_metadata,
            'stats': {
                'execution_count': self.execution_count,
                'success_count': self.success_count,
                'failure_count': self.failure_count
            },
            'last_executed': self.last_executed.isoformat() if self.last_executed else None,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class MCPPrompt(db.Model):
    """Model for MCP prompt templates"""
    __tablename__ = 'mcp_prompts'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey('mcp_servers.id'), nullable=False)
    name = db.Column(db.String(128), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)

    # Prompt arguments schema
    arguments = db.Column(db.JSON)  # List of argument definitions

    # Prompt metadata
    prompt_metadata = db.Column(db.JSON)

    # Usage stats
    usage_count = db.Column(db.Integer, default=0)
    last_used = db.Column(db.DateTime)
    tenant_id = db.Column(db.String(64), index=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    def to_dict(self):
        """Convert prompt to dictionary"""
        return {
            'id': self.id,
            'server_id': self.server_id,
            'name': self.name,
            'description': self.description,
            'arguments': self.arguments,
            'metadata': self.prompt_metadata,
            'usage_count': self.usage_count,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class TruthSession(db.Model):
    """Track Truth Engine reasoning sessions with 5-tier workflow support"""
    __tablename__ = 'truth_sessions'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    tenant_id = db.Column(db.String(64), index=True)

    tier = db.Column(db.String(20), default='trivial')
    status = db.Column(db.String(20), default='pending')

    query = db.Column(db.Text)
    response = db.Column(db.Text)

    budget_limit = db.Column(db.Float, default=0.0)
    budget_spent = db.Column(db.Float, default=0.0)
    token_count = db.Column(db.Integer, default=0)

    confidence_score = db.Column(db.Float, default=0.0)
    safety_score = db.Column(db.Float, default=1.0)

    llm_model = db.Column(db.String(64))
    routing_profile = db.Column(db.String(32))

    personas_used = db.Column(db.JSON)
    axis_context = db.Column(db.JSON)
    workflow_steps = db.Column(db.JSON)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)

    user = db.relationship('User', backref=db.backref('truth_sessions', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'tenant_id': self.tenant_id,
            'tier': self.tier,
            'status': self.status,
            'query': self.query,
            'response': self.response,
            'budget_limit': self.budget_limit,
            'budget_spent': self.budget_spent,
            'token_count': self.token_count,
            'confidence_score': self.confidence_score,
            'safety_score': self.safety_score,
            'llm_model': self.llm_model,
            'routing_profile': self.routing_profile,
            'personas_used': self.personas_used,
            'axis_context': self.axis_context,
            'workflow_steps': self.workflow_steps,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class TruthAuditEvent(db.Model):
    """EU AI Act Article 53 compliant audit trail with hash chain immutability"""
    __tablename__ = 'truth_audit_events'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    session_id = db.Column(db.String(64), db.ForeignKey('truth_sessions.session_id'), index=True)

    event_type = db.Column(db.String(50), nullable=False, index=True)
    event_category = db.Column(db.String(50))

    event_data = db.Column(db.JSON)
    decision_rationale = db.Column(db.Text)

    hash_chain = db.Column(db.String(64), nullable=False)
    previous_hash = db.Column(db.String(64))

    actor_id = db.Column(db.String(64))
    actor_type = db.Column(db.String(32))

    axis_involved = db.Column(db.JSON)
    compliance_flags = db.Column(db.JSON)

    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(UTC), index=True)
    retention_until = db.Column(db.DateTime)

    session = db.relationship('TruthSession', backref=db.backref('audit_events', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'session_id': self.session_id,
            'event_type': self.event_type,
            'event_category': self.event_category,
            'event_data': self.event_data,
            'decision_rationale': self.decision_rationale,
            'hash_chain': self.hash_chain,
            'previous_hash': self.previous_hash,
            'actor_id': self.actor_id,
            'actor_type': self.actor_type,
            'axis_involved': self.axis_involved,
            'compliance_flags': self.compliance_flags,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'retention_until': self.retention_until.isoformat() if self.retention_until else None
        }

class TruthArtifact(db.Model):
    """Store simulation outputs, graphs, deliverables with 7-year retention"""
    __tablename__ = 'truth_artifacts'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    artifact_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    session_id = db.Column(db.String(64), db.ForeignKey('truth_sessions.session_id'), index=True)

    artifact_type = db.Column(db.String(50), nullable=False)
    artifact_name = db.Column(db.String(256))

    content = db.Column(db.JSON)
    content_hash = db.Column(db.String(64))
    file_path = db.Column(db.String(512))
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(128))

    artifact_metadata = db.Column(db.JSON)
    tags = db.Column(db.JSON)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    retention_until = db.Column(db.DateTime)

    session = db.relationship('TruthSession', backref=db.backref('artifacts', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'artifact_id': self.artifact_id,
            'session_id': self.session_id,
            'artifact_type': self.artifact_type,
            'artifact_name': self.artifact_name,
            'content': self.content,
            'content_hash': self.content_hash,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'metadata': self.artifact_metadata,
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'retention_until': self.retention_until.isoformat() if self.retention_until else None
        }

class TruthBudget(db.Model):
    """Per-tenant budget tracking with kill-switch capability"""
    __tablename__ = 'truth_budgets'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    budget_limit = db.Column(db.Float, default=100.0)
    budget_spent = db.Column(db.Float, default=0.0)
    budget_period = db.Column(db.String(20), default='monthly')

    kill_switch_triggered = db.Column(db.Boolean, default=False)
    kill_switch_threshold = db.Column(db.Float, default=0.95)
    downgrade_tier = db.Column(db.String(20), default='trivial')

    tier_limits = db.Column(db.JSON)

    alerts_enabled = db.Column(db.Boolean, default=True)
    alert_thresholds = db.Column(db.JSON)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    reset_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    user = db.relationship('User', backref=db.backref('truth_budgets', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'budget_limit': self.budget_limit,
            'budget_spent': self.budget_spent,
            'budget_period': self.budget_period,
            'budget_remaining': self.budget_limit - self.budget_spent,
            'budget_utilization': (self.budget_spent / self.budget_limit * 100) if self.budget_limit > 0 else 0,
            'kill_switch_triggered': self.kill_switch_triggered,
            'kill_switch_threshold': self.kill_switch_threshold,
            'downgrade_tier': self.downgrade_tier,
            'tier_limits': self.tier_limits,
            'alerts_enabled': self.alerts_enabled,
            'alert_thresholds': self.alert_thresholds,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'reset_at': self.reset_at.isoformat() if self.reset_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class TruthMetric(db.Model):
    """MLflow-style metrics tracking for Truth Engine performance"""
    __tablename__ = 'truth_metrics'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    metric_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    session_id = db.Column(db.String(64), db.ForeignKey('truth_sessions.session_id'), nullable=True, index=True)

    metric_name = db.Column(db.String(128), nullable=False, index=True)
    metric_value = db.Column(db.Float, nullable=False)
    metric_unit = db.Column(db.String(32))

    metric_type = db.Column(db.String(32), default='gauge')

    tier = db.Column(db.String(20))
    llm_model = db.Column(db.String(64))

    labels = db.Column(db.JSON)

    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(UTC), index=True)

    session = db.relationship('TruthSession', backref=db.backref('metrics', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'metric_id': self.metric_id,
            'session_id': self.session_id,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'metric_unit': self.metric_unit,
            'metric_type': self.metric_type,
            'tier': self.tier,
            'llm_model': self.llm_model,
            'labels': self.labels,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class TruthLinkMessage(db.Model):
    """Inter-module messaging for TruthLink event bus"""
    __tablename__ = 'truth_link_messages'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.String(64), unique=True, nullable=False, index=True)

    source_module = db.Column(db.String(32), nullable=False)
    target_module = db.Column(db.String(32))

    message_type = db.Column(db.String(50), nullable=False, index=True)
    priority = db.Column(db.Integer, default=1)

    payload = db.Column(db.JSON)

    status = db.Column(db.String(20), default='pending')
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    def to_dict(self):
        return {
            'id': self.id,
            'message_id': self.message_id,
            'source_module': self.source_module,
            'target_module': self.target_module,
            'message_type': self.message_type,
            'priority': self.priority,
            'status': self.status,
            'retry_count': self.retry_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# -------------------------------------------------------------------------
# Missing UKG Model Definitions
# -------------------------------------------------------------------------

class PillarLevel(db.Model):
    """Model for Pillar Levels (Axis 1: Knowledge)."""
    __tablename__ = 'ukg_pillar_levels'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(255), unique=True, nullable=False)
    pillar_id = db.Column(db.String(10), unique=True, nullable=False)  # e.g., "PL01", "PL48"
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    sublevels = db.Column(db.JSON, nullable=True)
    tenant_id = db.Column(db.String(64), index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    def to_dict(self):
        return {
            'id': self.id,
            'uid': self.uid,
            'pillar_id': self.pillar_id,
            'name': self.name,
            'description': self.description,
            'sublevels': self.sublevels,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Sector(db.Model):
    """Model for Sectors (Axis 2)."""
    __tablename__ = 'ukg_sectors'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(255), unique=True, nullable=False)
    sector_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    tenant_id = db.Column(db.String(64), index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    def to_dict(self):
        return {
            'id': self.id,
            'uid': self.uid,
            'sector_code': self.sector_code,
            'name': self.name,
            'description': self.description,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Domain(db.Model):
    """Model for Domains (Axis 3)."""
    __tablename__ = 'ukg_domains'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    tenant_id = db.Column(db.String(64), index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    def to_dict(self):
        return {
            'id': self.id,
            'uid': self.uid,
            'name': self.name,
            'description': self.description,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Location(db.Model):
    """Model for Locations (Axis 12)."""
    __tablename__ = 'ukg_locations'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    location_type = db.Column(db.String(50), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    description = db.Column(db.Text, nullable=True)
    parent_location_id = db.Column(db.Integer, db.ForeignKey('ukg_locations.id'), nullable=True)
    attributes = db.Column(db.JSON, nullable=True)
    tenant_id = db.Column(db.String(64), index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    # Relationship for hierarchy
    parent = db.relationship('Location', remote_side=[id], backref='children')

    def to_dict(self):
        return {
            'id': self.id,
            'uid': self.uid,
            'name': self.name,
            'location_type': self.location_type,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'parent_location_id': self.parent_location_id,
            'attributes': self.attributes,
            'tenant_id': self.tenant_id
        }

class TimeContext(db.Model):
    """Model for Time Contexts (Axis 13)."""
    __tablename__ = 'ukg_time_contexts'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    tenant_id = db.Column(db.String(64), index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    def to_dict(self):
        return {
            'id': self.id,
            'uid': self.uid,
            'name': self.name,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'tenant_id': self.tenant_id
        }

class KnowledgeNode(db.Model):
    """Model for Knowledge Nodes containing actual knowledge content."""
    __tablename__ = 'ukg_knowledge_nodes'
    __table_args__ = (
        db.Index('ix_ukg_knowledge_nodes_tenant_id', 'tenant_id'),
        {'extend_existing': True}
    )

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(255), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    content_type = db.Column(db.String(50), nullable=False)  # e.g., "text", "markdown", "code"
    pillar_level_id = db.Column(db.Integer, db.ForeignKey('ukg_pillar_levels.id'), nullable=True)
    domain_id = db.Column(db.Integer, db.ForeignKey('ukg_domains.id'), nullable=True)
    location_id = db.Column(db.Integer, db.ForeignKey('ukg_locations.id'), nullable=True)
    node_metadata = db.Column(db.JSON, nullable=True)
    tenant_id = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    def to_dict(self):
        return {
            'id': self.id,
            'uid': self.uid,
            'title': self.title,
            'content': self.content,
            'content_type': self.content_type,
            'pillar_level_id': self.pillar_level_id,
            'domain_id': self.domain_id,
            'location_id': self.location_id,
            'metadata': self.node_metadata,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class MethodNode(db.Model):
    """Model for Method Nodes (Axis 4: Methods)."""
    __tablename__ = 'ukg_method_nodes'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    method_type = db.Column(db.String(100), nullable=False)
    implementation_details = db.Column(db.Text, nullable=True)
    tenant_id = db.Column(db.String(64), index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    def to_dict(self):
        return {
            'id': self.id,
            'uid': self.uid,
            'name': self.name,
            'method_type': self.method_type,
            'tenant_id': self.tenant_id
        }

class KnowledgeAlgorithm(db.Model):
    """Model for Knowledge Algorithms (KA)."""
    __tablename__ = 'ukg_knowledge_algorithms'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(255), unique=True, nullable=False)
    ka_id = db.Column(db.String(50), unique=True, nullable=False)  # e.g., "KA-117"
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    version = db.Column(db.String(20), default="1.0.0")
    config_schema = db.Column(db.JSON, nullable=True)
    tenant_id = db.Column(db.String(64), index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    def to_dict(self):
        return {
            'id': self.id,
            'uid': self.uid,
            'ka_id': self.ka_id,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'tenant_id': self.tenant_id
        }

class KAExecution(db.Model):
    """Model for tracking Knowledge Algorithm executions."""
    __tablename__ = 'ukg_ka_executions'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(255), unique=True, nullable=False)
    ka_id = db.Column(db.String(50), db.ForeignKey('ukg_knowledge_algorithms.ka_id'), nullable=False)
    status = db.Column(db.String(50), default="pending")  # pending, running, completed, failed
    input_data = db.Column(db.JSON, nullable=True)
    output_data = db.Column(db.JSON, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    execution_time_ms = db.Column(db.Integer, nullable=True)
    tenant_id = db.Column(db.String(64), index=True)
    started_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    completed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'uid': self.uid,
            'ka_id': self.ka_id,
            'status': self.status,
            'execution_time_ms': self.execution_time_ms,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class Node(db.Model):
    """Base model for all nodes in the UKG system (ukg_nodes)."""
    __tablename__ = 'ukg_nodes'
    __table_args__ = (
        db.Index('ix_ukg_nodes_node_type', 'node_type'),
        db.Index('ix_ukg_nodes_axis_number', 'axis_number'),
        {'extend_existing': True}
    )

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(255), unique=True, nullable=False)
    node_type = db.Column(db.String(100), nullable=False)
    label = db.Column(db.String(255), nullable=False)
    axis_number = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)
    attributes = db.Column(db.JSON, nullable=True)
    tenant_id = db.Column(db.String(64), index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    active = db.Column(db.Boolean, default=True)

    # Relationships
    outgoing_edges = db.relationship("Edge", foreign_keys="Edge.source_node_id", back_populates="source_node")
    incoming_edges = db.relationship("Edge", foreign_keys="Edge.target_node_id", back_populates="target_node")

    def to_dict(self):
        return {
            'id': self.id,
            'uid': self.uid,
            'node_type': self.node_type,
            'label': self.label,
            'axis_number': self.axis_number,
            'description': self.description,
            'attributes': self.attributes or {},
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'active': self.active
        }

class Edge(db.Model):
    """Base model for all edges in the UKG system (ukg_edges)."""
    __tablename__ = 'ukg_edges'
    __table_args__ = (
        db.Index('ix_ukg_edges_edge_type', 'edge_type'),
        {'extend_existing': True}
    )

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(255), unique=True, nullable=False)
    edge_type = db.Column(db.String(100), nullable=False)
    weight = db.Column(db.Float, default=1.0)
    source_node_id = db.Column(db.Integer, db.ForeignKey('ukg_nodes.id'), nullable=False)
    target_node_id = db.Column(db.Integer, db.ForeignKey('ukg_nodes.id'), nullable=False)
    attributes = db.Column(db.JSON, nullable=True)
    tenant_id = db.Column(db.String(64), index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    active = db.Column(db.Boolean, default=True)

    # Relationships
    source_node = db.relationship("Node", foreign_keys=[source_node_id], back_populates="outgoing_edges")
    target_node = db.relationship("Node", foreign_keys=[target_node_id], back_populates="incoming_edges")

    def to_dict(self):
        return {
            'id': self.id,
            'uid': self.uid,
            'edge_type': self.edge_type,
            'weight': self.weight,
            'source_node_id': self.source_node_id,
            'target_node_id': self.target_node_id,
            'attributes': self.attributes or {},
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'active': self.active
        }

class UkgSession(db.Model):
    """Model representing a user interaction session with the UKG"""
    __tablename__ = 'ukg_sessions'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Optional link to a user
    user_query = db.Column(db.Text, nullable=True)
    target_confidence = db.Column(db.Float, default=0.85)
    final_confidence = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), default='active')
    tenant_id = db.Column(db.String(64), index=True)
    started_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    memory_entries = db.relationship('MemoryEntry', backref='session', lazy='dynamic')
    user = db.relationship('User', backref='ukg_sessions')

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'user_query': self.user_query,
            'target_confidence': self.target_confidence,
            'final_confidence': self.final_confidence,
            'status': self.status,
            'tenant_id': self.tenant_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class MemoryEntry(db.Model):
    """Model representing entries in the structured memory store"""
    __tablename__ = 'memory_entries'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(255), unique=True, nullable=False, index=True)
    session_id = db.Column(db.String(255), db.ForeignKey('ukg_sessions.session_id'), nullable=False)
    entry_type = db.Column(db.String(100), nullable=False, index=True)
    pass_num = db.Column(db.Integer, default=0)
    layer_num = db.Column(db.Integer, default=0)
    content = db.Column(db.JSON, nullable=True)
    confidence = db.Column(db.Float, default=1.0)
    tenant_id = db.Column(db.String(64), index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    def to_dict(self):
        return {
            'id': self.id,
            'uid': self.uid,
            'session_id': self.session_id,
            'entry_type': self.entry_type,
            'pass_num': self.pass_num,
            'layer_num': self.layer_num,
            'content': self.content,
            'confidence': self.confidence,
            'tenant_id': self.tenant_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Moved IntegratedView back up to maintain logical grouping if needed, 
# but ensuring it's not double-defined or merged with TruthLinkMessage.
