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
from sqlalchemy import Index, event
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.exc import SQLAlchemyError

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
    backup_codes: Optional[List] = db.Column(JSONB)  # Encrypted list of backup codes

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

    parameters: Optional[Dict] = db.Column(JSONB)
    status: Optional[str] = db.Column(db.String(20), index=True)
    current_step: Optional[int] = db.Column(db.Integer)
    total_steps: Optional[int] = db.Column(db.Integer)
    created_at: datetime = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    started_at: Optional[datetime] = db.Column(db.DateTime)
    completed_at: Optional[datetime] = db.Column(db.DateTime)
    results: Optional[Dict] = db.Column(JSONB)

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
    data: Optional[Dict] = db.Column(JSONB)

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
    data: Optional[Dict] = db.Column(JSONB)

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
