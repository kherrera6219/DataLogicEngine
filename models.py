"""
Database Models for DataLogicEngine.

This module defines the core SQLAlchemy models with:
- Database indexes for performance
- Atomic operations for security
- Type hints for better maintainability
- Proper exception handling
"""

from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any
import logging
import os

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
        Index('ix_users_active', 'active'),
        Index('ix_users_created_at', 'created_at'),
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
    created_at: datetime = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

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
        if not self.locked_until:
            return False
        # locked_until is stored in UTC, but some backends return a naive
        # datetime (e.g. PostgreSQL TIMESTAMP WITHOUT TIME ZONE via psycopg2),
        # which can't be compared to an aware datetime.now(UTC). Normalize to
        # aware-UTC first to avoid a naive/aware TypeError.
        locked_until = self.locked_until
        if locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=UTC)
        return locked_until > datetime.now(UTC)

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

    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary representation."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'active': self.active,
            # Single-mode / OS-level auth: the one OS user is the owner with full
            # access. Roles/admin were removed (auth-deprecation Phase E); these are
            # reported as constants so the frontend owner/admin gating stays stable.
            'is_admin': True,
            'role': 'owner',
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_successful_login.isoformat() if self.last_successful_login else None
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'User':
        """Create user instance from dictionary."""
        user = User()
        for field in ['username', 'email', 'active']:
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
    contract_version: str = db.Column(db.String(32), nullable=False, default='dle-simulation.v1')
    engine_id: str = db.Column(db.String(64), nullable=False, default='multi-agent-debate')
    engine_version: str = db.Column(db.String(32), nullable=False, default='3.0.0')
    scenario_revision: Optional[str] = db.Column(db.String(64))
    seed: int = db.Column(db.Integer, nullable=False, default=0)
    plan: Optional[Dict] = db.Column(JSON)
    budget: Optional[Dict] = db.Column(JSON)
    provider_call_count: int = db.Column(db.Integer, nullable=False, default=0)
    tool_call_count: int = db.Column(db.Integer, nullable=False, default=0)
    checkpoint_sequence: int = db.Column(db.Integer, nullable=False, default=0)
    revision: int = db.Column(db.Integer, nullable=False, default=1)
    trace_id: Optional[str] = db.Column(db.String(36))
    last_error_code: Optional[str] = db.Column(db.String(100))
    last_error_message: Optional[str] = db.Column(db.String(500))
    pause_requested_at: Optional[datetime] = db.Column(db.DateTime)
    cancellation_requested_at: Optional[datetime] = db.Column(db.DateTime)
    artifact_state: str = db.Column(db.String(32), nullable=False, default='pending')

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
            'results': self.results,
            'contract_version': self.contract_version,
            'engine_id': self.engine_id,
            'engine_version': self.engine_version,
            'scenario_revision': self.scenario_revision,
            'seed': self.seed,
            'plan': self.plan or {},
            'budget': self.budget or {},
            'provider_call_count': self.provider_call_count,
            'tool_call_count': self.tool_call_count,
            'checkpoint_sequence': self.checkpoint_sequence,
            'revision': self.revision,
            'trace_id': self.trace_id,
            'last_error_code': self.last_error_code,
            'last_error_message': self.last_error_message,
            'pause_requested_at': self.pause_requested_at.isoformat() if self.pause_requested_at else None,
            'cancellation_requested_at': self.cancellation_requested_at.isoformat() if self.cancellation_requested_at else None,
            'artifact_state': self.artifact_state,
        }

    def __repr__(self) -> str:
        return f'<SimulationSession {self.session_id}>'


class SimulationStep(db.Model):
    """Durable, retryable workflow step for one simulation revision."""

    __tablename__ = 'simulation_steps'
    __table_args__ = (
        db.UniqueConstraint('session_id', 'sequence', 'attempt_number', name='uq_simulation_step_attempt'),
        Index('ix_simulation_steps_session_status', 'session_id', 'status'),
        Index('ix_simulation_steps_session_sequence', 'session_id', 'sequence'),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = db.Column(db.String(36), db.ForeignKey('simulation_sessions.session_id', ondelete='CASCADE'), nullable=False)
    step_key = db.Column(db.String(64), nullable=False)
    sequence = db.Column(db.Integer, nullable=False)
    attempt_number = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(32), nullable=False, default='pending')
    input_hash = db.Column(db.String(64), nullable=False)
    output_hash = db.Column(db.String(64))
    output_summary = db.Column(db.Text)
    validation = db.Column(JSON)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))


class SimulationEventRecord(db.Model):
    """Content-free durable progress/audit event."""

    __tablename__ = 'simulation_events'
    __table_args__ = (
        db.UniqueConstraint('session_id', 'sequence', name='uq_simulation_event_sequence'),
        Index('ix_simulation_events_session_created', 'session_id', 'created_at'),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = db.Column(db.String(36), db.ForeignKey('simulation_sessions.session_id', ondelete='CASCADE'), nullable=False)
    sequence = db.Column(db.Integer, nullable=False)
    event_type = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(32), nullable=False)
    step_key = db.Column(db.String(64))
    progress_current = db.Column(db.Integer)
    progress_total = db.Column(db.Integer)
    details = db.Column(JSON)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))


class SimulationProviderCall(db.Model):
    """Secret/content-free provider attempt ledger for a simulation turn."""

    __tablename__ = 'simulation_provider_calls'
    __table_args__ = (
        db.UniqueConstraint(
            'session_id',
            'call_index',
            'attempt_number',
            name='uq_simulation_provider_call_attempt',
        ),
        Index('ix_simulation_provider_calls_session_status', 'session_id', 'status'),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = db.Column(db.String(36), db.ForeignKey('simulation_sessions.session_id', ondelete='CASCADE'), nullable=False)
    step_id = db.Column(UUID(as_uuid=True), db.ForeignKey('simulation_steps.id', ondelete='SET NULL'))
    call_index = db.Column(db.Integer, nullable=False)
    attempt_number = db.Column(db.Integer, nullable=False, default=1)
    purpose = db.Column(db.String(64), nullable=False)
    persona_id = db.Column(db.String(64))
    provider_type = db.Column(db.String(32), nullable=False)
    model = db.Column(db.String(128), nullable=False)
    status = db.Column(db.String(32), nullable=False)
    tokens_in = db.Column(db.Integer, nullable=False, default=0)
    tokens_out = db.Column(db.Integer, nullable=False, default=0)
    estimated_cost_usd = db.Column(db.Numeric(12, 8))
    pricing_status = db.Column(db.String(32), nullable=False, default='unknown')
    disclosed_categories = db.Column(JSON)
    latency_ms = db.Column(db.Integer)
    error_code = db.Column(db.String(100))
    started_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    completed_at = db.Column(db.DateTime)


class SimulationEvidenceRecord(db.Model):
    """Stable evidence/provenance reference used by a simulation validator."""

    __tablename__ = 'simulation_evidence'
    __table_args__ = (
        Index('ix_simulation_evidence_session_step', 'session_id', 'step_id'),
        Index('ix_simulation_evidence_source', 'source_uid', 'source_revision'),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = db.Column(db.String(36), db.ForeignKey('simulation_sessions.session_id', ondelete='CASCADE'), nullable=False)
    step_id = db.Column(UUID(as_uuid=True), db.ForeignKey('simulation_steps.id', ondelete='CASCADE'))
    evidence_type = db.Column(db.String(64), nullable=False)
    source_uid = db.Column(db.String(255), nullable=False)
    source_revision = db.Column(db.String(64), nullable=False)
    content_hash = db.Column(db.String(64), nullable=False)
    summary = db.Column(db.Text)
    validation_state = db.Column(db.String(32), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))


class SimulationCheckpoint(db.Model):
    """Restart/pause checkpoint anchored to an immutable state hash."""

    __tablename__ = 'simulation_checkpoints'
    __table_args__ = (
        db.UniqueConstraint('session_id', 'sequence', name='uq_simulation_checkpoint_sequence'),
        Index('ix_simulation_checkpoints_session_created', 'session_id', 'created_at'),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = db.Column(db.String(36), db.ForeignKey('simulation_sessions.session_id', ondelete='CASCADE'), nullable=False)
    sequence = db.Column(db.Integer, nullable=False)
    step_key = db.Column(db.String(64))
    state_hash = db.Column(db.String(64), nullable=False)
    state = db.Column(JSON, nullable=False)
    object_key = db.Column(db.String(1024))
    object_hash = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))


class SimulationArtifact(db.Model):
    """PostgreSQL reference to a required simulation object-store artifact."""

    __tablename__ = 'simulation_artifacts'
    __table_args__ = (
        db.UniqueConstraint('session_id', 'artifact_type', 'revision', name='uq_simulation_artifact_revision'),
        Index('ix_simulation_artifacts_session_state', 'session_id', 'state'),
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = db.Column(db.String(36), db.ForeignKey('simulation_sessions.session_id', ondelete='CASCADE'), nullable=False)
    artifact_type = db.Column(db.String(64), nullable=False)
    schema_version = db.Column(db.String(64), nullable=False)
    revision = db.Column(db.String(64), nullable=False)
    object_key = db.Column(db.String(1024), nullable=False)
    sha256 = db.Column(db.String(64), nullable=False)
    size_bytes = db.Column(db.BigInteger, nullable=False)
    state = db.Column(db.String(32), nullable=False, default='pending')
    metadata_json = db.Column(JSON)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    verified_at = db.Column(db.DateTime)


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
        from backend.security.dpapi_store import encrypt_data, is_available

        if is_available():
            protected = encrypt_data(api_key)
            if protected:
                self.api_key_encrypted = f"dpapi:v1:{protected}".encode("utf-8")
                return
        if (
            os.environ.get("FLASK_ENV", "").lower() == "production"
            and os.environ.get("IS_DESKTOP_APP", "false").lower() == "true"
        ):
            raise RuntimeError("DPAPI is required for provider credentials in desktop production")
        key = current_app.config.get('ENCRYPTION_KEY')
        if not key:
            import hashlib
            import base64
            secret = current_app.config.get('SECRET_KEY')
            if not secret:
                raise RuntimeError("SECRET_KEY is required for provider credential fallback encryption")
            key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
        f = Fernet(key)
        self.api_key_encrypted = f.encrypt(api_key.encode())
    
    def get_api_key(self) -> Optional[str]:
        if not self.api_key_encrypted:
            return None
        try:
            encoded = (
                self.api_key_encrypted.decode("utf-8")
                if isinstance(self.api_key_encrypted, bytes)
                else str(self.api_key_encrypted)
            )
            if encoded.startswith("dpapi:v1:"):
                from backend.security.dpapi_store import decrypt_data

                decrypted = decrypt_data(encoded.removeprefix("dpapi:v1:"))
                if not decrypted:
                    raise ValueError("DPAPI provider credential could not be decrypted")
                return decrypted
            key = current_app.config.get('ENCRYPTION_KEY')
            if not key:
                import hashlib
                import base64
                secret = current_app.config.get('SECRET_KEY')
                if not secret:
                    raise RuntimeError("SECRET_KEY is required for provider credential fallback decryption")
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
            'model': self.model_id,
            'is_active': self.is_active,
            'is_default': self.is_default,
            'has_api_key': self.api_key_encrypted is not None,
            'status': str((self.config or {}).get('availability_status') or ('stored' if self.api_key_encrypted else 'not_configured')),
            'status_checked_at': (self.config or {}).get('availability_checked_at'),
        }
        return result


class LLMProviderUsage(db.Model):
    """Secret-free provider egress, usage, retry, and privacy ledger."""
    __tablename__ = 'llm_provider_usage'
    __table_args__ = (
        Index('ix_llm_provider_usage_run_stage', 'run_id', 'request_stage'),
        Index('ix_llm_provider_usage_session_created', 'session_id', 'created_at'),
        Index('ix_llm_provider_usage_status_created', 'status', 'created_at'),
        {'extend_existing': True},
    )

    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider_id = db.Column(UUID(as_uuid=True), db.ForeignKey('llm_providers.id'), nullable=True)
    provider_type = db.Column(db.String(32), nullable=False, default='unknown')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    api_key_id = db.Column(UUID(as_uuid=True), db.ForeignKey('external_api_keys.id'), nullable=True)
    run_id = db.Column(UUID(as_uuid=True), nullable=True)
    session_id = db.Column(db.String(255), nullable=True)
    model = db.Column(db.String(100), nullable=True)
    purpose = db.Column(db.String(64), nullable=False, default='answer')
    request_stage = db.Column(db.String(64), nullable=False, default='provider_execution')
    attempt_number = db.Column(db.Integer, nullable=False, default=1)
    retry_index = db.Column(db.Integer, nullable=False, default=0)
    tokens_in = db.Column(db.Integer, default=0)
    tokens_out = db.Column(db.Integer, default=0)
    latency_ms = db.Column(db.Integer, nullable=True)
    estimated_cost_usd = db.Column(db.Float, nullable=True)
    pricing_status = db.Column(db.String(32), nullable=False, default='unknown')
    status = db.Column(db.String(32), nullable=False, default='completed')
    success = db.Column(db.Boolean, default=True)
    error_class = db.Column(db.String(64), nullable=True)
    error_code = db.Column(db.String(100), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    disclosed_categories = db.Column(JSON, nullable=False, default=list)
    idempotency_key = db.Column(db.String(128), nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    ended_at = db.Column(db.DateTime, nullable=True)
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


class GatewayVirtualModel(db.Model):
    """PostgreSQL authority for one published gateway virtual-model policy."""

    __tablename__ = 'gateway_virtual_models'
    __table_args__ = (
        Index('ix_gateway_virtual_models_active', 'is_active'),
        {'extend_existing': True},
    )

    id = db.Column(db.String(64), primary_key=True)
    label = db.Column(db.String(120), nullable=False)
    mode = db.Column(db.String(32), nullable=False)
    max_provider_calls = db.Column(db.Integer, nullable=False)
    provider_backed = db.Column(db.Boolean, nullable=False, default=True)
    description = db.Column(db.String(500), nullable=False)
    policy = db.Column(JSON, nullable=False, default=dict)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'label': self.label,
            'mode': self.mode,
            'max_provider_calls': self.max_provider_calls,
            'provider_backed': self.provider_backed,
            'description': self.description,
            'policy': self.policy or {},
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
    max_concurrent_requests = db.Column(db.Integer, default=2)
    permissions = db.Column(db.JSON)
    allowed_providers = db.Column(db.JSON)
    allowed_models = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    expires_at = db.Column(db.DateTime, nullable=True)
    revoked_at = db.Column(db.DateTime, nullable=True)
    revoked_reason = db.Column(db.String(240), nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    rotated_from_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('external_api_keys.id'),
        nullable=True,
    )
    
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
        key_record = cls.query.filter_by(
            key_hash=key_hash,
            is_active=True,
            deleted_at=None,
        ).first()
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
        from backend.llm_gateway.external_contract import normalize_client_scopes

        return {
            'id': str(self.id),
            'name': self.name,
            # Retain the original public field while exposing the explicit
            # storage-column name used by the Phase 8 administration contract.
            'prefix': self.key_prefix,
            'key_prefix': self.key_prefix,
            'is_active': self.is_active,
            'total_requests': self.total_requests,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'revoked_at': self.revoked_at.isoformat() if self.revoked_at else None,
            'revoked_reason': self.revoked_reason,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'rotated_from_id': str(self.rotated_from_id) if self.rotated_from_id else None,
            'scopes': sorted(normalize_client_scopes(self.permissions)),
            'allowed_providers': self.allowed_providers or [],
            'allowed_models': self.allowed_models or [],
            'rate_limit_rpm': self.rate_limit_rpm,
            'rate_limit_daily': self.rate_limit_daily,
            'max_tokens_per_request': self.max_tokens_per_request,
            'max_concurrent_requests': self.max_concurrent_requests,
        }


class GatewayIdempotencyRecord(db.Model):
    """Durable authority preventing duplicate external gateway execution."""

    __tablename__ = 'gateway_idempotency_records'
    __table_args__ = (
        db.UniqueConstraint(
            'api_key_id',
            'idempotency_key',
            name='uq_gateway_idempotency_client_key',
        ),
        Index('ix_gateway_idempotency_state_expiry', 'state', 'expires_at'),
        {'extend_existing': True},
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_key_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('external_api_keys.id'),
        nullable=False,
    )
    idempotency_key = db.Column(db.String(128), nullable=False)
    request_sha256 = db.Column(db.String(64), nullable=False)
    request_id = db.Column(db.String(128), nullable=False)
    state = db.Column(db.String(24), nullable=False, default='pending')
    response_status = db.Column(db.Integer, nullable=True)
    response_payload = db.Column(JSON, nullable=True)
    run_id = db.Column(db.String(36), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    expires_at = db.Column(db.DateTime, nullable=False)

    def to_dict(self, *, include_response: bool = False) -> Dict[str, Any]:
        payload = {
            'id': str(self.id),
            'api_key_id': str(self.api_key_id),
            'idempotency_key': self.idempotency_key,
            'request_id': self.request_id,
            'state': self.state,
            'response_status': self.response_status,
            'run_id': self.run_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
        }
        if include_response:
            payload['response_payload'] = self.response_payload
        return payload


class GatewayAsyncRun(db.Model):
    """Durable authority for one bounded external gateway job."""

    __tablename__ = 'gateway_async_runs'
    __table_args__ = (
        db.UniqueConstraint(
            'api_key_id',
            'idempotency_key',
            name='uq_gateway_async_run_client_idempotency',
        ),
        Index('ix_gateway_async_run_state_created', 'status', 'created_at'),
        Index('ix_gateway_async_run_request_id', 'request_id'),
        {'extend_existing': True},
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = db.Column(db.String(128), nullable=False)
    idempotency_key = db.Column(db.String(128), nullable=False)
    request_sha256 = db.Column(db.String(64), nullable=False)
    api_key_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('external_api_keys.id', ondelete='SET NULL'),
        nullable=True,
    )
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(24), nullable=False, default='queued')
    virtual_model = db.Column(db.String(64), nullable=False)
    request_encryption = db.Column(db.String(32), nullable=False)
    request_ciphertext = db.Column(db.Text, nullable=False)
    response_encryption = db.Column(db.String(32), nullable=True)
    response_ciphertext = db.Column(db.Text, nullable=True)
    response_storage = db.Column(db.String(32), nullable=False, default='postgresql_ciphertext')
    response_object_bucket = db.Column(db.String(100), nullable=True)
    response_object_key = db.Column(db.String(500), nullable=True)
    response_sha256 = db.Column(db.String(64), nullable=True)
    response_size_bytes = db.Column(db.Integer, nullable=True)
    response_status = db.Column(db.Integer, nullable=True)
    run_id = db.Column(db.String(36), nullable=True)
    error_code = db.Column(db.String(100), nullable=True)
    error_message = db.Column(db.String(500), nullable=True)
    cancellation_requested = db.Column(db.Boolean, nullable=False, default=False)
    attempt_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        """Return content-free job metadata safe for the client principal."""
        return {
            'job_id': str(self.id),
            'request_id': self.request_id,
            'status': self.status,
            'virtual_model': self.virtual_model,
            'run_id': self.run_id,
            'response_status': self.response_status,
            'result_storage': self.response_storage,
            'result_size_bytes': self.response_size_bytes,
            'error_code': self.error_code,
            'error_message': self.error_message,
            'cancellation_requested': bool(self.cancellation_requested),
            'attempt_count': int(self.attempt_count or 0),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
        }


class IngestionJob(db.Model):
    """PostgreSQL authority for one bounded local ingestion lifecycle."""

    __tablename__ = 'ingestion_jobs'
    __table_args__ = (
        Index('ix_ingestion_jobs_status_created', 'status', 'created_at'),
        Index('ix_ingestion_jobs_user_created', 'user_id', 'created_at'),
        {'extend_existing': True},
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    tenant_id = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(32), nullable=False, default='queued')
    source_path = db.Column(db.Text, nullable=False)
    source_label = db.Column(db.String(200), nullable=True)
    source_digest = db.Column(db.String(64), nullable=False)
    recursive = db.Column(db.Boolean, nullable=False, default=True)
    chunk_size = db.Column(db.Integer, nullable=False)
    max_file_bytes = db.Column(db.Integer, nullable=False)
    max_total_bytes = db.Column(db.Integer, nullable=False)
    max_files = db.Column(db.Integer, nullable=False)
    max_pages = db.Column(db.Integer, nullable=False, default=500)
    max_archive_entries = db.Column(db.Integer, nullable=False, default=10000)
    max_decompressed_bytes = db.Column(db.Integer, nullable=False, default=100 * 1024 * 1024)
    max_archive_depth = db.Column(db.Integer, nullable=False, default=1)
    parser_timeout_seconds = db.Column(db.Integer, nullable=False, default=60)
    files_scanned = db.Column(db.Integer, nullable=False, default=0)
    files_ingested = db.Column(db.Integer, nullable=False, default=0)
    files_rejected = db.Column(db.Integer, nullable=False, default=0)
    chunks_created = db.Column(db.Integer, nullable=False, default=0)
    chunks_indexed = db.Column(db.Integer, nullable=False, default=0)
    materializations_pending = db.Column(db.Integer, nullable=False, default=0)
    cancellation_requested = db.Column(db.Boolean, nullable=False, default=False)
    pause_requested = db.Column(db.Boolean, nullable=False, default=False)
    current_checkpoint = db.Column(db.String(80), nullable=False, default='queued')
    last_error_code = db.Column(db.String(120), nullable=True)
    last_error_message = db.Column(db.String(240), nullable=True)
    result_summary = db.Column(JSON, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def to_status_dict(self) -> Dict[str, Any]:
        result = dict(self.result_summary or {}) if self.result_summary else None
        return {
            'ingestion_id': str(self.id),
            'status': self.status,
            'source': self.source_label or self.source_path,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'checkpoint': self.current_checkpoint,
            'cancellation_requested': bool(self.cancellation_requested),
            'pause_requested': bool(self.pause_requested),
            'files_scanned': int(self.files_scanned or 0),
            'files_ingested': int(self.files_ingested or 0),
            'files_rejected': int(self.files_rejected or 0),
            'chunks_created': int(self.chunks_created or 0),
            'materializations_pending': int(self.materializations_pending or 0),
            'result': result,
            'neo4j_sync': result.get('neo4j_sync') if result else None,
            'error': self.last_error_message,
            'error_code': self.last_error_code,
        }

    def to_history_dict(self) -> Dict[str, Any]:
        payload = dict(self.result_summary or {})
        payload.setdefault('ingestion_id', str(self.id))
        payload.setdefault('source', self.source_label or self.source_path)
        payload['status'] = self.status
        payload['checkpoint'] = self.current_checkpoint
        payload['cancellation_requested'] = bool(self.cancellation_requested)
        payload['pause_requested'] = bool(self.pause_requested)
        payload['created_at'] = self.created_at.isoformat() if self.created_at else None
        payload['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return payload


class IngestionFile(db.Model):
    """One acquired or rejected file within an ingestion job."""

    __tablename__ = 'ingestion_files'
    __table_args__ = (
        db.UniqueConstraint('job_id', 'relative_path', name='uq_ingestion_file_job_path'),
        Index('ix_ingestion_files_job_status', 'job_id', 'status'),
        Index('ix_ingestion_files_document_status', 'document_uid', 'status'),
        Index('ix_ingestion_files_source_sha', 'source_sha256'),
        {'extend_existing': True},
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('ingestion_jobs.id', ondelete='CASCADE'),
        nullable=False,
    )
    relative_path = db.Column(db.String(1000), nullable=False)
    source_path = db.Column(db.Text, nullable=False)
    document_uid = db.Column(db.String(80), nullable=True)
    source_revision = db.Column(db.String(100), nullable=True)
    source_sha256 = db.Column(db.String(64), nullable=True)
    size_bytes = db.Column(db.Integer, nullable=True)
    detected_type = db.Column(db.String(32), nullable=True)
    parser_result = db.Column(JSON, nullable=True)
    defense_result = db.Column(JSON, nullable=True)
    status = db.Column(db.String(32), nullable=False, default='acquired')
    error_code = db.Column(db.String(120), nullable=True)
    content_sha256 = db.Column(db.String(64), nullable=True)
    chunk_count = db.Column(db.Integer, nullable=False, default=0)
    object_bucket = db.Column(db.String(100), nullable=True)
    object_key = db.Column(db.String(500), nullable=True)
    object_sha256 = db.Column(db.String(64), nullable=True)
    object_status = db.Column(db.String(24), nullable=True)
    normalized_object_bucket = db.Column(db.String(100), nullable=True)
    normalized_object_key = db.Column(db.String(500), nullable=True)
    normalized_object_sha256 = db.Column(db.String(64), nullable=True)
    normalized_object_status = db.Column(db.String(24), nullable=True)
    embedding_revision = db.Column(db.String(255), nullable=True)
    last_retrieved_at = db.Column(db.DateTime, nullable=True)
    last_retrieval_trace_id = db.Column(db.String(36), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class IngestionChunk(db.Model):
    """Stable document-scoped chunk and its materialization checkpoint."""

    __tablename__ = 'ingestion_chunks'
    __table_args__ = (
        db.UniqueConstraint('file_id', 'chunk_index', name='uq_ingestion_chunk_file_index'),
        Index('ix_ingestion_chunks_job_materialization', 'job_id', 'materialization_state'),
        Index('ix_ingestion_chunks_node_uid', 'node_uid'),
        {'extend_existing': True},
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('ingestion_jobs.id', ondelete='CASCADE'),
        nullable=False,
    )
    file_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('ingestion_files.id', ondelete='CASCADE'),
        nullable=False,
    )
    node_uid = db.Column(db.String(80), nullable=False)
    chunk_index = db.Column(db.Integer, nullable=False)
    chunk_count = db.Column(db.Integer, nullable=False)
    content_sha256 = db.Column(db.String(64), nullable=False)
    chunk_sha256 = db.Column(db.String(64), nullable=False)
    source_revision = db.Column(db.String(255), nullable=False)
    materialization_state = db.Column(db.String(32), nullable=False, default='pending')
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class IngestionAttempt(db.Model):
    """One durable processing attempt and checkpoint for an ingestion job."""

    __tablename__ = 'ingestion_attempts'
    __table_args__ = (
        db.UniqueConstraint('job_id', 'attempt_number', name='uq_ingestion_attempt_number'),
        Index('ix_ingestion_attempts_job_status', 'job_id', 'status'),
        {'extend_existing': True},
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = db.Column(
        UUID(as_uuid=True),
        db.ForeignKey('ingestion_jobs.id', ondelete='CASCADE'),
        nullable=False,
    )
    attempt_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(32), nullable=False, default='running')
    worker_instance_id = db.Column(db.String(100), nullable=True)
    checkpoint = db.Column(db.String(80), nullable=False, default='acquisition')
    error_code = db.Column(db.String(120), nullable=True)
    error_message = db.Column(db.String(240), nullable=True)
    started_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    completed_at = db.Column(db.DateTime, nullable=True)


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
    status = db.Column(db.String(32), default='running')
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
    confidence = db.Column(db.Float, nullable=True)
    entropy = db.Column(db.Float, default=0.0)
    bias_risk = db.Column(db.Float, default=0.0)

    # Input/Output
    input_message = db.Column(db.Text, nullable=True)
    final_answer = db.Column(db.Text, nullable=True)

    # AuditBundle fields (spec Section 12.1)
    tier = db.Column(db.String(10), nullable=True)  # 1, 2, 3
    coordinate17_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_axis_vectors.vector_id', use_alter=True, name='fk_trace_runs_axis_vector'), nullable=True)
    evidence_pack_hash = db.Column(db.String(64), nullable=True)  # SHA-256 of sealed evidence set
    layers_executed = db.Column(JSONB, nullable=True)  # list of layer indices that fired
    refinement_cycles = db.Column(db.Integer, default=0)
    regulatory_pass = db.Column(db.Boolean, nullable=True)
    security_pass = db.Column(db.Boolean, nullable=True)
    truthgate_decision = db.Column(db.String(16), nullable=True)  # allow/block/escalate/hitl
    token_cost = db.Column(db.Integer, nullable=True)
    latency_ms = db.Column(db.Integer, nullable=True)
    frost_depth = db.Column(db.Integer, nullable=True)
    truth_engine_mode = db.Column(db.String(50), nullable=True)

    # Relationships
    stages = db.relationship('TraceStage', backref='run', lazy='dynamic', cascade='all, delete-orphan')
    evidence_items = db.relationship('TraceEvidence', backref='run', lazy='dynamic', cascade='all, delete-orphan')
    claims = db.relationship('TraceClaim', backref='run', lazy='dynamic', cascade='all, delete-orphan')
    personas = db.relationship('TracePersona', backref='run', lazy='dynamic', cascade='all, delete-orphan')
    ka_invocations = db.relationship('TraceKAInvocation', backref='run', lazy='dynamic', cascade='all, delete-orphan')
    policy_decisions = db.relationship('TracePolicyDecision', backref='run', lazy='dynamic', cascade='all, delete-orphan')
    memory_events = db.relationship('TraceMemoryEvent', backref='run', lazy='dynamic', cascade='all, delete-orphan')
    citations = db.relationship('TraceCitation', backref='run', lazy='dynamic', cascade='all, delete-orphan')
    validators = db.relationship('TraceValidator', backref='run', lazy='dynamic', cascade='all, delete-orphan')
    quality_decisions = db.relationship('TraceQualityDecision', backref='run', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        snapshot = self.data_snapshot if isinstance(self.data_snapshot, dict) else {}
        return {
            'run_id': str(self.run_id),
            'session_id': str(self.session_id) if self.session_id else None,
            'tenant_id': self.tenant_id,
            'user_id': self.user_id,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'model_name': self.model_name,
            'model_version': self.model_version,
            'provider_used': snapshot.get('provider_used'),
            'model': {'name': self.model_name, 'version': self.model_version},
            'policy_pack': {'id': self.policy_pack_id, 'version': self.policy_pack_version},
            'data_snapshot': self.data_snapshot,
            'scores': {
                'confidence': self.confidence,
                'entropy': self.entropy,
                'bias_risk': self.bias_risk
            },
            'input_message': self.input_message,
            'final_answer': self.final_answer,
            'audit_bundle': {
                'tier': self.tier,
                'coordinate17_id': str(self.coordinate17_id) if self.coordinate17_id else None,
                'evidence_pack_hash': self.evidence_pack_hash,
                'layers_executed': self.layers_executed,
                'refinement_cycles': self.refinement_cycles,
                'regulatory_pass': self.regulatory_pass,
                'security_pass': self.security_pass,
                'truthgate_decision': self.truthgate_decision,
                'token_cost': self.token_cost,
                'latency_ms': self.latency_ms,
                'frost_depth': self.frost_depth,
                'truth_engine_mode': self.truth_engine_mode,
            },
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
            'stage_type': self.stage_type,
            'layer_index': self.layer_index,
            'step_index': self.step_index,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_ms': self.duration_ms,
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
    origin = db.Column(db.Text, nullable=True)
    author_publisher = db.Column(db.String(500), nullable=True)
    captured_at = db.Column(db.DateTime, nullable=True)
    effective_at = db.Column(db.DateTime, nullable=True)
    retrieved_at = db.Column(db.DateTime, nullable=True)
    permissions = db.Column(JSONB, nullable=True)
    transformation_chain = db.Column(JSONB, nullable=True)
    embedding_revision = db.Column(db.String(255), nullable=True)

    # Location within source
    locator = db.Column(JSONB, nullable=True)  # page, section, line_range, url

    # Content
    snippet = db.Column(db.Text, nullable=True)
    content_hash = db.Column(db.String(100), nullable=True)  # sha256

    # Retrieval metadata
    retrieval_method = db.Column(db.String(50), nullable=True)  # vector, graph, rules, manual
    relevance_score = db.Column(db.Float, nullable=True)
    axis_match_score = db.Column(db.Float, nullable=True)
    quality_score = db.Column(db.Float, nullable=True)
    freshness_score = db.Column(db.Float, nullable=True)
    provenance_completeness = db.Column(db.Float, nullable=True)

    # Usage tracking
    used_by_claims = db.Column(JSONB, nullable=True)    # [claim_id]
    used_by_personas = db.Column(JSONB, nullable=True)  # [persona_id]
    used_by_stages = db.Column(JSONB, nullable=True)    # [stage_id]

    # Conflicts
    conflicts_with = db.Column(JSONB, nullable=True)  # [evidence_id]

    def to_dict(self):
        authority_to_tier = {
            'high': 'GOLD',
            'medium': 'SILVER',
            'low': 'BRONZE',
        }
        claims_supported = self.used_by_claims or []
        stages = self.used_by_stages or []
        return {
            'evidence_id': str(self.evidence_id),
            'run_id': str(self.run_id),
            'source_id': self.source_id,
            'source_type': self.source_type,
            'title': self.source_title,
            'credibility_score': self.relevance_score,
            'evidence_tier': authority_to_tier.get((self.authority or '').lower(), 'UNVERIFIED'),
            'claims_supported': claims_supported,
            'layer_retrieved': stages[0] if isinstance(stages, list) and stages else None,
            'ka_that_invoked': (self.retrieval_method or '').upper() if self.retrieval_method else None,
            'source': {
                'type': self.source_type,
                'id': self.source_id,
                'title': self.source_title,
                'authority': self.authority,
                'origin': self.origin,
                'author_publisher': self.author_publisher,
                'captured_at': self.captured_at.isoformat() if self.captured_at else None,
                'effective_at': self.effective_at.isoformat() if self.effective_at else None,
                'permissions': self.permissions,
                'transformation_chain': self.transformation_chain,
                'embedding_revision': self.embedding_revision,
            },
            'locator': self.locator,
            'snippet': self.snippet,
            'hash': self.content_hash,
            'retrieval': {
                'method': self.retrieval_method,
                'relevance_score': self.relevance_score,
                'axis_match': self.axis_match_score,
                'retrieved_at': self.retrieved_at.isoformat() if self.retrieved_at else None,
                'quality_score': self.quality_score,
                'freshness_score': self.freshness_score,
                'provenance_completeness': self.provenance_completeness,
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
    confidence = db.Column(db.Float, nullable=True)
    claim_type = db.Column(db.String(32), nullable=True)

    # Evidence links
    evidence_ids = db.Column(JSONB, nullable=True)  # [evidence_id]
    stage_ids = db.Column(JSONB, nullable=True)     # [stage_id]
    citation_ids = db.Column(JSONB, nullable=True)

    def to_dict(self):
        return {
            'claim_id': str(self.claim_id),
            'run_id': str(self.run_id),
            'text': self.text,
            'claim_type': self.claim_type,
            'answer_span': {'start': self.answer_span_start, 'end': self.answer_span_end},
            'support': {
                'status': self.status,
                'confidence': self.confidence,
                'evidence_ids': self.evidence_ids,
                'stage_ids': self.stage_ids,
                'citation_ids': self.citation_ids,
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
    confidence = db.Column(db.Float, nullable=True)

    # Objections and consensus
    objections = db.Column(JSONB, nullable=True)  # [{type, detail}]
    consensus_impact = db.Column(JSONB, nullable=True)  # {changed_answer, delta_summary}

    def to_dict(self):
        consensus = self.consensus_impact if isinstance(self.consensus_impact, dict) else {}
        objections = self.objections if isinstance(self.objections, list) else []
        return {
            'persona_id': str(self.persona_id),
            'run_id': str(self.run_id),
            'initial_position': self.draft_text,
            'critique_of_others': consensus.get('critique_of_others') or consensus.get('delta_summary'),
            'final_position': consensus.get('final_position') or self.draft_text,
            'synthesis_weight': consensus.get('synthesis_weight'),
            'flagged_conflicts': [
                item.get('detail') if isinstance(item, dict) else str(item)
                for item in objections
            ],
            'confidence': self.confidence,
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

    confidence = db.Column(db.Float, nullable=True)
    relationship = db.Column(db.String(32), nullable=False, default='insufficient')
    rationale = db.Column(db.Text, nullable=True)
    validator_id = db.Column(db.String(100), nullable=True)


class TraceCitation(db.Model):
    """A rendered answer citation resolved to persisted evidence."""
    __tablename__ = 'trace_citations'

    citation_id = db.Column(db.String(100), primary_key=True)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False, index=True)
    claim_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_claims.claim_id'), nullable=True)
    evidence_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_evidence.evidence_id'), nullable=False)
    source_id = db.Column(db.String(255), nullable=False)
    label = db.Column(db.String(32), nullable=False)
    answer_span_start = db.Column(db.Integer, nullable=True)
    answer_span_end = db.Column(db.Integer, nullable=True)

    def to_dict(self):
        return {
            'citation_id': self.citation_id.split(':', 1)[-1],
            'run_id': str(self.run_id),
            'claim_id': str(self.claim_id) if self.claim_id else None,
            'evidence_id': str(self.evidence_id),
            'source_id': self.source_id,
            'label': self.label,
            'answer_span_start': self.answer_span_start,
            'answer_span_end': self.answer_span_end,
        }


class TraceValidator(db.Model):
    """One versioned validator observation used by a governed decision."""
    __tablename__ = 'trace_validators'

    validator_id = db.Column(db.String(100), primary_key=True)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False, index=True)
    claim_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_claims.claim_id'), nullable=True)
    validator_type = db.Column(db.String(64), nullable=False)
    version = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(32), nullable=False)
    inputs = db.Column(JSONB, nullable=True)
    outputs = db.Column(JSONB, nullable=True)
    missing_inputs = db.Column(JSONB, nullable=True)
    duration_ms = db.Column(db.Integer, nullable=True)

    def to_dict(self):
        return {
            'validator_id': self.validator_id.split(':', 1)[-1],
            'run_id': str(self.run_id),
            'claim_id': str(self.claim_id) if self.claim_id else None,
            'validator_type': self.validator_type,
            'version': self.version,
            'status': self.status,
            'inputs': self.inputs,
            'outputs': self.outputs,
            'missing_inputs': self.missing_inputs,
            'duration_ms': self.duration_ms,
        }


class TraceQualityDecision(db.Model):
    """Versioned confidence measurement or convergence decision."""
    __tablename__ = 'trace_quality_decisions'

    decision_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trace_runs.run_id'), nullable=False, index=True)
    decision_type = db.Column(db.String(32), nullable=False)
    version = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(32), nullable=False)
    value = db.Column(db.Float, nullable=True)
    components = db.Column(JSONB, nullable=True)
    missing_inputs = db.Column(JSONB, nullable=True)
    rationale = db.Column(db.Text, nullable=True)
    iteration = db.Column(db.Integer, nullable=True)
    terminal = db.Column(db.Boolean, nullable=True)

    def to_dict(self):
        return {
            'decision_id': str(self.decision_id),
            'run_id': str(self.run_id),
            'decision_type': self.decision_type,
            'version': self.version,
            'status': self.status,
            'value': self.value,
            'components': self.components,
            'missing_inputs': self.missing_inputs,
            'rationale': self.rationale,
            'iteration': self.iteration,
            'terminal': self.terminal,
        }


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
    status = db.Column(db.String(20), default='ready')
    exported_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    bundle_ref = db.Column(db.String(512), nullable=True)
    manifest_hash = db.Column(db.String(128), nullable=True)
    file_size_bytes = db.Column(db.Integer, nullable=True)
    payload = db.Column(JSONB, nullable=True)
    options = db.Column(JSONB, nullable=True)
    encrypted = db.Column(db.Boolean, default=False)
    signed = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'export_id': str(self.export_id),
            'run_id': str(self.run_id),
            'format': self.format,
            'destination': self.destination,
            'status': self.status,
            'exported_at': self.exported_at.isoformat() if self.exported_at else None,
            'user_id': self.user_id,
            'bundle_ref': self.bundle_ref,
            'download_url': self.bundle_ref,
            'manifest_hash': self.manifest_hash,
            'file_size_bytes': self.file_size_bytes,
            'options': self.options,
            'encrypted': self.encrypted,
            'signed': self.signed,
        }


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
    protocol_version = db.Column(db.String(32), default='2025-11-25')
    transport = db.Column(db.String(32), nullable=False, default='stdio')
    enabled = db.Column(db.Boolean, nullable=False, default=False)
    consent_state = db.Column(db.String(32), nullable=False, default='pending')
    requested_scopes = db.Column(db.JSON)
    approved_scopes = db.Column(db.JSON)
    command_fingerprint = db.Column(db.String(64), index=True)
    containment_status = db.Column(db.String(32), nullable=False, default='not_qualified')
    health_status = db.Column(db.String(32), nullable=False, default='not_started')
    last_error_code = db.Column(db.String(100))
    last_error_message = db.Column(db.String(500))
    config_revision = db.Column(db.Integer, nullable=False, default=1)

    # Capabilities
    supports_resources = db.Column(db.Boolean, default=True)
    supports_tools = db.Column(db.Boolean, default=True)
    supports_prompts = db.Column(db.Boolean, default=True)
    supports_logging = db.Column(db.Boolean, default=True)

    # Configuration
    config = db.Column(db.JSON)
    server_metadata = db.Column(db.JSON)
    # DPAPI ciphertext only. This field is intentionally never serialized.
    credential_blobs = db.Column(db.JSON)

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
    consent_grants = db.relationship('MCPConsentGrant', backref='server', lazy='dynamic', cascade='all, delete-orphan')
    lifecycle_events = db.relationship('MCPLifecycleEvent', backref='server', lazy='dynamic', cascade='all, delete-orphan')
    executions = db.relationship('MCPExecutionRecord', backref='server', lazy='dynamic', cascade='all, delete-orphan')

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
            'transport': self.transport,
            'enabled': self.enabled,
            'consent_state': self.consent_state,
            'requested_scopes': sorted(self.requested_scopes or []),
            'approved_scopes': sorted(self.approved_scopes or []),
            'command_fingerprint': self.command_fingerprint,
            'containment_status': self.containment_status,
            'health_status': self.health_status,
            'last_error_code': self.last_error_code,
            'last_error_message': self.last_error_message,
            'config_revision': self.config_revision,
            'capabilities': {
                'resources': self.supports_resources,
                'tools': self.supports_tools,
                'prompts': self.supports_prompts,
                'logging': self.supports_logging
            }
        ,
            'config': self._renderer_safe_config(),
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

    def _renderer_safe_config(self) -> dict:
        """Return exact non-secret launch policy without env values or DPAPI blobs."""
        config = self.config if isinstance(self.config, dict) else {}
        safe_keys = {
            'schema_version', 'name', 'transport', 'protocol_version', 'command',
            'args', 'cwd', 'file_roots', 'network_destinations',
            'requested_scopes', 'limits',
        }
        safe = {key: config.get(key) for key in safe_keys if key in config}
        env = config.get('env') if isinstance(config.get('env'), dict) else {}
        credential_env = config.get('credential_env') if isinstance(config.get('credential_env'), dict) else {}
        safe['env_keys'] = sorted(env)
        safe['credential_keys'] = sorted(credential_env)
        return safe


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
    input_embedding = db.Column(db.Text)
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
            'input_embedding': self.input_embedding,
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
    object_store_bucket = db.Column(db.String(128))
    object_store_key = db.Column(db.String(512), index=True)
    merkle_root = db.Column(db.String(64), index=True)
    blockchain_anchor_tx = db.Column(db.String(128))
    blockchain_anchor_status = db.Column(db.String(32))

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
            'object_store_bucket': self.object_store_bucket,
            'object_store_key': self.object_store_key,
            'merkle_root': self.merkle_root,
            'blockchain_anchor_tx': self.blockchain_anchor_tx,
            'blockchain_anchor_status': self.blockchain_anchor_status,
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

# Alias — KnowledgeNode and KnowledgeGraphNode are the same merged model.
KnowledgeNode = KnowledgeGraphNode

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

class UserNotificationPreference(db.Model):
    """Per-user notification delivery preferences — one row per user."""
    __tablename__ = 'user_notification_preferences'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'),
        nullable=False, unique=True, index=True,
    )

    # Email channel
    email_on_run_complete = db.Column(db.Boolean, nullable=False, default=True)
    email_on_run_failed = db.Column(db.Boolean, nullable=False, default=True)
    email_on_simulation_complete = db.Column(db.Boolean, nullable=False, default=False)

    # In-app channel
    inapp_run_complete = db.Column(db.Boolean, nullable=False, default=True)
    inapp_run_failed = db.Column(db.Boolean, nullable=False, default=True)
    inapp_simulation_complete = db.Column(db.Boolean, nullable=False, default=True)
    inapp_system_alerts = db.Column(db.Boolean, nullable=False, default=True)

    # Digest schedule: none | daily | weekly
    digest_frequency = db.Column(db.String(20), nullable=False, default='none')

    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def to_dict(self) -> dict:
        return {
            'email_on_run_complete': self.email_on_run_complete,
            'email_on_run_failed': self.email_on_run_failed,
            'email_on_simulation_complete': self.email_on_simulation_complete,
            'inapp_run_complete': self.inapp_run_complete,
            'inapp_run_failed': self.inapp_run_failed,
            'inapp_simulation_complete': self.inapp_simulation_complete,
            'inapp_system_alerts': self.inapp_system_alerts,
            'digest_frequency': self.digest_frequency,
        }


class UserAIPreferences(db.Model):
    """Per-user AI processing and privacy preferences."""
    __tablename__ = 'user_ai_preferences'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, index=True)
    # Which provider to prefer (None = auto)
    preferred_provider = db.Column(db.String(64), nullable=True)
    preferred_model = db.Column(db.String(128), nullable=True)
    # Toggle to completely disable AI processing for this user
    ai_processing_enabled = db.Column(db.Boolean, default=True, nullable=False)
    # Whether to persist chat history for this user
    store_chat_history = db.Column(db.Boolean, default=True, nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    def to_dict(self):
        return {
            'preferred_provider': self.preferred_provider,
            'preferred_model': self.preferred_model,
            'ai_processing_enabled': self.ai_processing_enabled,
            'store_chat_history': self.store_chat_history,
        }


class MCPConsentGrant(db.Model):
    """Owner approval for one exact connector command and scope fingerprint."""

    __tablename__ = 'mcp_consent_grants'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    server_id = db.Column(db.Integer, db.ForeignKey('mcp_servers.id', ondelete='CASCADE'), nullable=False)
    principal_id = db.Column(db.String(64), nullable=False, index=True)
    command_fingerprint = db.Column(db.String(64), nullable=False, index=True)
    requested_scopes = db.Column(db.JSON, nullable=False)
    approved_scopes = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(32), nullable=False, default='approved')
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    approved_at = db.Column(db.DateTime)
    revoked_at = db.Column(db.DateTime)

    __table_args__ = (
        Index('ix_mcp_consent_server_status', 'server_id', 'status'),
    )

    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'server_id': self.server_id,
            'principal_id': self.principal_id,
            'command_fingerprint': self.command_fingerprint,
            'requested_scopes': sorted(self.requested_scopes or []),
            'approved_scopes': sorted(self.approved_scopes or []),
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'revoked_at': self.revoked_at.isoformat() if self.revoked_at else None,
        }


class MCPLifecycleEvent(db.Model):
    """Content-free durable MCP configuration and process lifecycle record."""

    __tablename__ = 'mcp_lifecycle_events'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    server_id = db.Column(db.Integer, db.ForeignKey('mcp_servers.id', ondelete='CASCADE'), nullable=False)
    principal_id = db.Column(db.String(64), nullable=False, index=True)
    event_type = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(32), nullable=False)
    details = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))

    __table_args__ = (
        Index('ix_mcp_lifecycle_server_created', 'server_id', 'created_at'),
    )

    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'server_id': self.server_id,
            'principal_id': self.principal_id,
            'event_type': self.event_type,
            'status': self.status,
            'details': self.details or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class MCPExecutionRecord(db.Model):
    """Content-bounded durable MCP tool/resource/prompt execution ledger."""

    __tablename__ = 'mcp_execution_records'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = db.Column(db.String(36), nullable=False, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    server_id = db.Column(db.Integer, db.ForeignKey('mcp_servers.id', ondelete='CASCADE'), nullable=False)
    tool_id = db.Column(db.Integer, db.ForeignKey('mcp_tools.id', ondelete='SET NULL'))
    principal_id = db.Column(db.String(64), nullable=False, index=True)
    operation = db.Column(db.String(128), nullable=False)
    status = db.Column(db.String(32), nullable=False, default='running')
    required_scopes = db.Column(db.JSON)
    request_sha256 = db.Column(db.String(64), nullable=False)
    result_sha256 = db.Column(db.String(64))
    result_size_bytes = db.Column(db.BigInteger)
    result_content = db.Column(db.Text)
    result_trust = db.Column(db.String(64))
    artifact_object_key = db.Column(db.String(1024))
    prompt_injection_risk = db.Column(db.Boolean, nullable=False, default=False)
    error_code = db.Column(db.String(100))
    error_message = db.Column(db.String(500))
    duration_ms = db.Column(db.Integer)
    trace_id = db.Column(db.String(36), index=True)
    started_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    completed_at = db.Column(db.DateTime)

    __table_args__ = (
        Index('ix_mcp_execution_server_status', 'server_id', 'status'),
        Index('ix_mcp_execution_server_started', 'server_id', 'started_at'),
    )

    def to_dict(self) -> dict:
        return {
            'execution_id': self.execution_id,
            'server_id': self.server_id,
            'tool_id': self.tool_id,
            'principal_id': self.principal_id,
            'operation': self.operation,
            'status': self.status,
            'required_scopes': sorted(self.required_scopes or []),
            'request_sha256': self.request_sha256,
            'result_sha256': self.result_sha256,
            'result_size_bytes': self.result_size_bytes,
            'result_trust': self.result_trust,
            'artifact_object_key': self.artifact_object_key,
            'prompt_injection_risk': self.prompt_injection_risk,
            'error_code': self.error_code,
            'error_message': self.error_message,
            'duration_ms': self.duration_ms,
            'trace_id': self.trace_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }


class CrossStoreOutboxEvent(db.Model):
    """Durable authority-to-materialization delivery request."""

    __tablename__ = 'cross_store_outbox_events'
    __table_args__ = (
        db.UniqueConstraint(
            'entity_type',
            'entity_id',
            'destination',
            'operation',
            'source_revision',
            name='uq_cross_store_outbox_source_delivery',
        ),
        Index('ix_cross_store_outbox_pending', 'status', 'available_at'),
        Index('ix_cross_store_outbox_destination', 'destination', 'status'),
        Index('ix_cross_store_outbox_entity', 'entity_type', 'entity_id'),
        {'extend_existing': True},
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = db.Column(db.String(120), nullable=False)
    entity_id = db.Column(db.String(255), nullable=False)
    destination = db.Column(db.String(32), nullable=False)
    operation = db.Column(db.String(80), nullable=False)
    schema_version = db.Column(db.String(80), nullable=False)
    source_revision = db.Column(db.String(255), nullable=False)
    correlation_id = db.Column(db.String(128), nullable=False)
    payload = db.Column(JSONB, nullable=False)
    payload_sha256 = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(24), nullable=False, default='pending')
    attempts = db.Column(db.Integer, nullable=False, default=0)
    available_at = db.Column(db.DateTime, nullable=True)
    locked_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    safe_reason = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class CrossStoreMaterializationState(db.Model):
    """Latest required destination revision for a logical authority record."""

    __tablename__ = 'cross_store_materialization_states'
    __table_args__ = (
        db.UniqueConstraint(
            'entity_type',
            'entity_id',
            'destination',
            name='uq_cross_store_materialization_entity_destination',
        ),
        Index('ix_cross_store_materialization_state', 'destination', 'state'),
        {'extend_existing': True},
    )

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = db.Column(db.String(120), nullable=False)
    entity_id = db.Column(db.String(255), nullable=False)
    destination = db.Column(db.String(32), nullable=False)
    schema_version = db.Column(db.String(80), nullable=False)
    source_revision = db.Column(db.String(255), nullable=False)
    observed_revision = db.Column(db.String(255), nullable=True)
    payload_sha256 = db.Column(db.String(64), nullable=False)
    state = db.Column(db.String(24), nullable=False, default='pending')
    attempts = db.Column(db.Integer, nullable=False, default=0)
    safe_reason = db.Column(db.String(120), nullable=True)
    last_attempt_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class DataDeletionTombstone(db.Model):
    """Non-PII record proving cross-store deletion/reconciliation state."""

    __tablename__ = 'data_deletion_tombstones'
    __table_args__ = (
        Index('ix_data_deletion_tombstone_status', 'status', 'requested_at'),
        {'extend_existing': True},
    )

    deletion_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_type = db.Column(db.String(40), nullable=False)
    subject_digest = db.Column(db.String(64), nullable=False, index=True)
    policy_version = db.Column(db.String(40), nullable=False)
    status = db.Column(db.String(24), nullable=False, default='pending')
    store_status = db.Column(JSONB, nullable=False, default=dict)
    safe_reason = db.Column(db.String(120), nullable=True)
    attempts = db.Column(db.Integer, nullable=False, default=0)
    requested_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    completed_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
