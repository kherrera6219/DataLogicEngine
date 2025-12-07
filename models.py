from datetime import datetime, timedelta
from datetime import datetime, timedelta

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class APIKey(db.Model):
    """API key used for authenticating programmatic requests."""

    __tablename__ = 'api_keys'

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

class PasswordHistory(db.Model):
    """Password history for preventing password reuse"""
    __tablename__ = 'password_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    user = db.relationship('User', backref=db.backref('password_history', lazy='dynamic', order_by='PasswordHistory.created_at.desc()'))

    def __repr__(self):
        return f'<PasswordHistory user_id={self.user_id} created={self.created_at}>'


class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    active = db.Column(db.Boolean, default=True)  # Renamed from is_active to avoid conflict
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    # Phase 1: Enhanced password security
    password_changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    password_expires_at = db.Column(db.DateTime)
    force_password_change = db.Column(db.Boolean, default=False)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)

    # Phase 1: Multi-Factor Authentication
    mfa_enabled = db.Column(db.Boolean, default=False)
    mfa_secret = db.Column(db.String(32))
    mfa_backup_codes = db.Column(db.JSON)  # Hashed backup codes

    # Override UserMixin's is_active property
    @property
    def is_active(self):
        return self.active

    # Relationships can be added here

    def check_password_history(self, password):
        """Check if password was used in the last N passwords"""
        from backend.security.password_security import PasswordSecurity

        # Get last N passwords from history
        history_count = PasswordSecurity.PASSWORD_HISTORY_COUNT
        recent_passwords = self.password_history.limit(history_count).all()

        # Check against each historical password
        for history in recent_passwords:
            if check_password_hash(history.password_hash, password):
                return False  # Password was recently used

        return True  # Password is new

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

        # Save current password to history before changing (if user exists)
        if self.id and self.password_hash:
            history_entry = PasswordHistory(
                user_id=self.id,
                password_hash=self.password_hash
            )
            db.session.add(history_entry)

            # Keep only last N passwords in history
            old_entries = self.password_history.offset(PasswordSecurity.PASSWORD_HISTORY_COUNT).all()
            for old_entry in old_entries:
                db.session.delete(old_entry)

        # Set the password hash
        self.password_hash = generate_password_hash(password)
        self.password_changed_at = datetime.utcnow()

        # Set expiration date (90 days from now)
        self.password_expires_at = datetime.utcnow() + timedelta(days=PasswordSecurity.PASSWORD_EXPIRY_DAYS)

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
        if self.locked_until and datetime.utcnow() < self.locked_until:
            return True
        return False

    def record_failed_login(self):
        """Record a failed login attempt and lock account if threshold exceeded"""
        self.failed_login_attempts += 1

        # Lock account after 5 failed attempts for 30 minutes
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)

    def record_successful_login(self):
        """Record a successful login"""
        self.last_login = datetime.utcnow()
        self.failed_login_attempts = 0
        self.locked_until = None

    def to_dict(self):
        """Convert user to dictionary (excluding sensitive data)"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'mfa_enabled': self.mfa_enabled,
            'password_expires_in_days': self.days_until_password_expiry(),
            'force_password_change': self.force_password_change
        }

    def __repr__(self):
        return f'<User {self.username}>'


class SimulationSession(db.Model):
    """Model for tracking simulation sessions"""
    __tablename__ = 'simulation_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String(128))
    description = db.Column(db.Text)
    parameters = db.Column(db.JSON)
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    current_step = db.Column(db.Integer, default=0)
    total_steps = db.Column(db.Integer, default=8)
    results = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Define relationship with User
    user = db.relationship('User', backref=db.backref('simulations', lazy='dynamic'))
    
    def to_dict(self):
        """Convert session to dictionary"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'parameters': self.parameters,
            'status': self.status,
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'results': self.results,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class KnowledgeGraphNode(db.Model):
    """Basic model for knowledge graph nodes"""
    __tablename__ = 'kg_nodes'
    
    id = db.Column(db.Integer, primary_key=True)
    node_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    node_type = db.Column(db.String(32), nullable=False)
    label = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    data = db.Column(db.JSON)
    axis_number = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert node to dictionary"""
        return {
            'id': self.id,
            'node_id': self.node_id,
            'node_type': self.node_type,
            'label': self.label,
            'description': self.description,
            'data': self.data,
            'axis_number': self.axis_number,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class KnowledgeGraphEdge(db.Model):
    """Basic model for knowledge graph edges"""
    __tablename__ = 'kg_edges'
    
    id = db.Column(db.Integer, primary_key=True)
    edge_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    source_id = db.Column(db.Integer, db.ForeignKey('kg_nodes.id'), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('kg_nodes.id'), nullable=False)
    edge_type = db.Column(db.String(32), nullable=False)
    weight = db.Column(db.Float, default=1.0)
    data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define relationships
    source = db.relationship('KnowledgeGraphNode', foreign_keys=[source_id], backref='outgoing_edges')
    target = db.relationship('KnowledgeGraphNode', foreign_keys=[target_id], backref='incoming_edges')
    
    def to_dict(self):
        """Convert edge to dictionary"""
        return {
            'id': self.id,
            'edge_id': self.edge_id,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'edge_type': self.edge_type,
            'weight': self.weight,
            'data': self.data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class MCPServer(db.Model):
    """Model for MCP server configurations"""
    __tablename__ = 'mcp_servers'

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
            },
            'config': self.config,
            'metadata': self.server_metadata,
            'stats': {
                'total_requests': self.total_requests,
                'successful_requests': self.successful_requests,
                'failed_requests': self.failed_requests
            },
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_active': self.last_active.isoformat() if self.last_active else None
        }


class MCPResource(db.Model):
    """Model for MCP resources"""
    __tablename__ = 'mcp_resources'

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
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class MCPTool(db.Model):
    """Model for MCP tools"""
    __tablename__ = 'mcp_tools'

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
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class MCPPrompt(db.Model):
    """Model for MCP prompt templates"""
    __tablename__ = 'mcp_prompts'

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
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }