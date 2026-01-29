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

    # Add indexes for frequently queried fields
    __table_args__ = (
        Index('ix_users_username', 'username'),
        Index('ix_users_email', 'email'),
        Index('ix_users_role', 'role'),
        Index('ix_users_active', 'active'),
        Index('ix_users_created_at', 'created_at'),
        Index('ix_users_role_active', 'role', 'active'),  # Composite index for common filter
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

    active: bool = db.Column(db.Boolean, default=True, index=True)
    is_admin: bool = db.Column(db.Boolean, default=False)
    role: str = db.Column(db.String(20), default='user', index=True)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, index=True)

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


class SimulationSession(db.Model):
    """Simulation session model with encrypted fields."""

    __tablename__ = 'simulation_sessions'

    __table_args__ = (
        Index('ix_simulation_sessions_user_id', 'user_id'),
        Index('ix_simulation_sessions_status', 'status'),
        Index('ix_simulation_sessions_created_at', 'created_at'),
        Index('ix_simulation_sessions_user_status', 'user_id', 'status'),  # Composite
    )

    id: int = db.Column(db.Integer, primary_key=True)
    session_id: str = db.Column(db.String(36), unique=True, nullable=False)
    user_id: int = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
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
    status: Optional[str] = db.Column(db.String(20), index=True)
    current_step: Optional[int] = db.Column(db.Integer)
    total_steps: Optional[int] = db.Column(db.Integer)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, index=True)
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

    __tablename__ = 'kg_nodes'

    __table_args__ = (
        Index('ix_kg_nodes_node_type', 'node_type'),
        Index('ix_kg_nodes_axis_number', 'axis_number'),
        Index('ix_kg_nodes_type_axis', 'node_type', 'axis_number'),  # Composite
    )

    id: int = db.Column(db.Integer, primary_key=True)
    node_id: str = db.Column(db.String(50), unique=True, nullable=False, index=True)
    node_type: Optional[str] = db.Column(db.String(50), index=True)
    label: Optional[str] = db.Column(db.String(100))
    description: Optional[str] = db.Column(db.Text)
    axis_number: Optional[int] = db.Column(db.Integer, index=True)
    data: Optional[Dict] = db.Column(JSON)

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

    __tablename__ = 'kg_edges'

    __table_args__ = (
        Index('ix_kg_edges_source_id', 'source_id'),
        Index('ix_kg_edges_target_id', 'target_id'),
        Index('ix_kg_edges_edge_type', 'edge_type'),
        Index('ix_kg_edges_source_target', 'source_id', 'target_id'),  # Composite
    )

    id: int = db.Column(db.Integer, primary_key=True)
    edge_id: str = db.Column(db.String(50), unique=True, nullable=False, index=True)
    source_id: int = db.Column(db.Integer, db.ForeignKey('kg_nodes.id'), nullable=False, index=True)
    target_id: int = db.Column(db.Integer, db.ForeignKey('kg_nodes.id'), nullable=False, index=True)
    edge_type: Optional[str] = db.Column(db.String(50), index=True)
    weight: Optional[float] = db.Column(db.Float)
    data: Optional[Dict] = db.Column(JSON)

    source = db.relationship('KnowledgeGraphNode', foreign_keys=[source_id], backref='out_edges')
    target = db.relationship('KnowledgeGraphNode', foreign_keys=[target_id], backref='in_edges')

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
