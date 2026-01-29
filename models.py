"""
Database Models for DataLogicEngine.

This module defines the core SQLAlchemy models with:
- Database indexes for performance
- Atomic operations for security
- Type hints for better maintainability
- Proper exception handling
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging

from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Index, event, JSON, UUID, LargeBinary
from sqlalchemy.exc import SQLAlchemyError
from cryptography.fernet import Fernet
from flask import current_app
import uuid

from extensions import db

logger = logging.getLogger(__name__)


class User(db.Model):
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
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)

    # MFA fields
    mfa_enabled: bool = db.Column(db.Boolean, default=False)
    mfa_secret: Optional[str] = db.Column(db.String(255))
    backup_codes: Optional[List] = db.Column(JSON)  # Encrypted list of backup codes

    # Account security fields
    failed_login_attempts: int = db.Column(db.Integer, default=0)
    locked_until: Optional[datetime] = db.Column(db.DateTime)
    last_successful_login: Optional[datetime] = db.Column(db.DateTime)
    last_password_change: datetime = db.Column(db.DateTime, default=datetime.utcnow)

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
        self.last_password_change = datetime.utcnow()

    def check_password(self, password: str) -> bool:
        """Verify password against stored hash."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def is_account_locked(self) -> bool:
        """Check if account is currently locked."""
        if self.locked_until and self.locked_until > datetime.utcnow():
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
                    .values(locked_until=datetime.utcnow() + lockout_duration)
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
                    last_successful_login=datetime.utcnow()
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PasswordHistory user_id={self.user_id} created={self.created_at}>'


class AuditLog(db.Model):
    """Compliance audit log for tracking sensitive system actions."""
    __tablename__ = 'audit_logs'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
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
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow)
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
            'source_id': self.source_id,
            'target_id': self.target_id,
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = db.Column(db.DateTime, nullable=True)
    
    usage_records = db.relationship('LLMProviderUsage', backref='provider', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_api_key(self, api_key: str) -> None:
        key = current_app.config.get('ENCRYPTION_KEY')
        if not key:
            import hashlib, base64
            secret = current_app.config.get('SECRET_KEY', 'default-secret')
            key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
        f = Fernet(key)
        self.api_key_encrypted = f.encrypt(api_key.encode())
    
    def get_api_key(self) -> Optional[str]:
        if not self.api_key_encrypted: return None
        try:
            key = current_app.config.get('ENCRYPTION_KEY')
            if not key:
                import hashlib, base64
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
    success = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    usage_records = db.relationship('LLMProviderUsage', backref='api_key', lazy='dynamic')


class ChatSession(db.Model):
    """A collection of related messages."""
    __tablename__ = 'chat_sessions'
    __table_args__ = {'extend_existing': True}

    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=True)
    model = db.Column(db.String(100), nullable=True)
    mode = db.Column(db.String(50), default='chat')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class TraceRun(db.Model):
    """Top-level trace run capturing a complete chat interaction."""
    __tablename__ = 'trace_runs'
    
    run_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = db.Column(UUID(as_uuid=True), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(20), default='running')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    model_name = db.Column(db.String(100), nullable=True)
    input_message = db.Column(db.Text, nullable=True)
    final_answer = db.Column(db.Text, nullable=True)
    
    stages = db.relationship('TraceStage', backref='run', lazy='dynamic', cascade='all, delete-orphan')


class TraceStage(db.Model):
    """Individual stage in the execution pipeline."""
    __tablename__ = 'trace_stages'
    
    stage_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='running')
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    duration_ms = db.Column(db.Integer, nullable=True)


class TraceEvidence(db.Model):
    """Evidence item used in a run."""
    __tablename__ = 'trace_evidence'
    
    evidence_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)
    source_type = db.Column(db.String(50), nullable=True)
    source_title = db.Column(db.String(500), nullable=True)
    snippet = db.Column(db.Text, nullable=True)
    relevance_score = db.Column(db.Float, nullable=True)


class TraceClaim(db.Model):
    """Individual claim extracted from the final answer."""
    __tablename__ = 'trace_claims'
    
    claim_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')
    confidence = db.Column(db.Float, default=0.0)


class TracePolicyDecision(db.Model):
    """Policy/guardrail decision trace."""
    __tablename__ = 'trace_policy_decisions'
    
    decision_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False)
    policy_rule_id = db.Column(db.String(100), nullable=True)
    decision_type = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
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

    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
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

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
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

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reset_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

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

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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

# Moved IntegratedView back up to maintain logical grouping if needed, 
# but ensuring it's not double-defined or merged with TruthLinkMessage.
