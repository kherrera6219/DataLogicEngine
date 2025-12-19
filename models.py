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
    role = db.Column(db.String(20), default='user')  # admin, analyst, user, viewer
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


# =============================================================================
# TRUTH ENGINE v7.3 MODELS
# =============================================================================

class TruthSession(db.Model):
    """Track Truth Engine reasoning sessions with 5-tier workflow support"""
    __tablename__ = 'truth_sessions'

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
    
    correlation_id = db.Column(db.String(64), index=True)
    link_session_id = db.Column(db.String(64), index=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    processed_at = db.Column(db.DateTime)
    expires_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'message_id': self.message_id,
            'source_module': self.source_module,
            'target_module': self.target_module,
            'message_type': self.message_type,
            'priority': self.priority,
            'payload': self.payload,
            'status': self.status,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'correlation_id': self.correlation_id,
            'session_id': self.link_session_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }


# =============================================================================
# UNIFIED COORDINATE SYSTEM MODELS (17-AXIS)
# =============================================================================

class UnifiedCoordinate(db.Model):
    """
    Store 17-dimensional knowledge coordinates with Nuremberg-style numbering.
    Each coordinate uniquely identifies a knowledge element in the UKG.
    """
    __tablename__ = 'unified_coordinates'

    id = db.Column(db.Integer, primary_key=True)
    coordinate_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    
    coordinate_string = db.Column(db.String(512), nullable=False, index=True)
    
    axis_1_pillar = db.Column(db.String(64))
    axis_2_sector = db.Column(db.String(64))
    axis_3_honeycomb = db.Column(db.String(64))
    axis_4_branch = db.Column(db.String(64))
    axis_5_node = db.Column(db.String(64))
    axis_6_octopus = db.Column(db.String(64))
    axis_7_spiderweb = db.Column(db.String(64))
    axis_8_knowledge_expert = db.Column(db.String(64))
    axis_9_qualifications = db.Column(db.String(64))
    axis_10_regulatory = db.Column(db.String(64))
    axis_11_compliance = db.Column(db.String(64))
    axis_12_location = db.Column(db.String(64))
    axis_13_temporal = db.Column(db.String(64))
    axis_14_risk = db.Column(db.String(64))
    axis_15_federated = db.Column(db.String(64))
    axis_16_arrows_of_time = db.Column(db.String(64))
    axis_17_observability = db.Column(db.String(64))
    
    meta_tags = db.Column(db.JSON)
    
    label = db.Column(db.String(256))
    description = db.Column(db.Text)
    coordinate_metadata = db.Column(db.JSON)
    
    node_id = db.Column(db.Integer, db.ForeignKey('kg_nodes.id'), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    node = db.relationship('KnowledgeGraphNode', backref=db.backref('coordinates', lazy='dynamic'))

    def get_axis_value(self, axis_number: int) -> str | None:
        """Get value for a specific axis (1-17)"""
        axis_map = {
            1: self.axis_1_pillar, 2: self.axis_2_sector, 3: self.axis_3_honeycomb,
            4: self.axis_4_branch, 5: self.axis_5_node, 6: self.axis_6_octopus,
            7: self.axis_7_spiderweb, 8: self.axis_8_knowledge_expert,
            9: self.axis_9_qualifications, 10: self.axis_10_regulatory,
            11: self.axis_11_compliance, 12: self.axis_12_location,
            13: self.axis_13_temporal, 14: self.axis_14_risk,
            15: self.axis_15_federated, 16: self.axis_16_arrows_of_time,
            17: self.axis_17_observability
        }
        return axis_map.get(axis_number)

    def set_axis_value(self, axis_number: int, value: str):
        """Set value for a specific axis (1-17)"""
        axis_attrs = {
            1: 'axis_1_pillar', 2: 'axis_2_sector', 3: 'axis_3_honeycomb',
            4: 'axis_4_branch', 5: 'axis_5_node', 6: 'axis_6_octopus',
            7: 'axis_7_spiderweb', 8: 'axis_8_knowledge_expert',
            9: 'axis_9_qualifications', 10: 'axis_10_regulatory',
            11: 'axis_11_compliance', 12: 'axis_12_location',
            13: 'axis_13_temporal', 14: 'axis_14_risk',
            15: 'axis_15_federated', 16: 'axis_16_arrows_of_time',
            17: 'axis_17_observability'
        }
        if axis_number in axis_attrs:
            setattr(self, axis_attrs[axis_number], value)

    def to_dict(self):
        return {
            'id': self.id,
            'coordinate_id': self.coordinate_id,
            'coordinate_string': self.coordinate_string,
            'axes': {
                1: self.axis_1_pillar, 2: self.axis_2_sector, 3: self.axis_3_honeycomb,
                4: self.axis_4_branch, 5: self.axis_5_node, 6: self.axis_6_octopus,
                7: self.axis_7_spiderweb, 8: self.axis_8_knowledge_expert,
                9: self.axis_9_qualifications, 10: self.axis_10_regulatory,
                11: self.axis_11_compliance, 12: self.axis_12_location,
                13: self.axis_13_temporal, 14: self.axis_14_risk,
                15: self.axis_15_federated, 16: self.axis_16_arrows_of_time,
                17: self.axis_17_observability
            },
            'meta_tags': self.meta_tags,
            'label': self.label,
            'description': self.description,
            'metadata': self.coordinate_metadata,
            'node_id': self.node_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class CoordinateTraversal(db.Model):
    """
    Store crosswalk relationships between coordinates.
    Supports Honeycomb (hierarchical), Octopus (one-to-many), 
    and Spiderweb (many-to-many) traversal patterns.
    """
    __tablename__ = 'coordinate_traversals'

    id = db.Column(db.Integer, primary_key=True)
    traversal_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    
    source_coordinate_id = db.Column(db.Integer, db.ForeignKey('unified_coordinates.id'), nullable=False)
    target_coordinate_id = db.Column(db.Integer, db.ForeignKey('unified_coordinates.id'), nullable=False)
    
    traversal_type = db.Column(db.String(32), nullable=False, index=True)
    traversal_axis = db.Column(db.Integer)
    pattern_id = db.Column(db.String(64))
    sequence_order = db.Column(db.Integer)
    
    source_axis_value_id = db.Column(db.Integer, db.ForeignKey('axis_values.id'), nullable=True)
    target_axis_value_id = db.Column(db.Integer, db.ForeignKey('axis_values.id'), nullable=True)
    
    edge_id = db.Column(db.Integer, db.ForeignKey('kg_edges.id'), nullable=True)
    
    weight = db.Column(db.Numeric(8, 4), default=1.0)
    confidence = db.Column(db.Numeric(5, 4), default=1.0)
    
    bidirectional = db.Column(db.Boolean, default=False)
    
    traversal_metadata = db.Column(db.JSON)
    hop_details = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    source = db.relationship('UnifiedCoordinate', foreign_keys=[source_coordinate_id], 
                            backref=db.backref('outgoing_traversals', lazy='dynamic'))
    target = db.relationship('UnifiedCoordinate', foreign_keys=[target_coordinate_id], 
                            backref=db.backref('incoming_traversals', lazy='dynamic'))
    source_axis = db.relationship('AxisValue', foreign_keys=[source_axis_value_id])
    target_axis = db.relationship('AxisValue', foreign_keys=[target_axis_value_id])
    edge = db.relationship('KnowledgeGraphEdge', backref=db.backref('traversals', lazy='dynamic'))

    def to_dict(self):
        return {
            'id': self.id,
            'traversal_id': self.traversal_id,
            'source_coordinate_id': self.source_coordinate_id,
            'target_coordinate_id': self.target_coordinate_id,
            'traversal_type': self.traversal_type,
            'traversal_axis': self.traversal_axis,
            'pattern_id': self.pattern_id,
            'sequence_order': self.sequence_order,
            'source_axis_value_id': self.source_axis_value_id,
            'target_axis_value_id': self.target_axis_value_id,
            'edge_id': self.edge_id,
            'weight': float(self.weight) if self.weight else 1.0,
            'confidence': float(self.confidence) if self.confidence else 1.0,
            'bidirectional': self.bidirectional,
            'metadata': self.traversal_metadata,
            'hop_details': self.hop_details,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class MetaTagMapping(db.Model):
    """
    Store meta-tag overlays for SAM.gov compatibility.
    Maps external standards (NAICS, FAR, DFARS, ISO, NIST) to coordinate axes.
    """
    __tablename__ = 'meta_tag_mappings'

    id = db.Column(db.Integer, primary_key=True)
    mapping_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    
    meta_tag = db.Column(db.String(32), nullable=False, index=True)
    external_code = db.Column(db.String(64), nullable=False, index=True)
    
    target_axis = db.Column(db.Integer, nullable=False)
    nuremberg_value = db.Column(db.String(64), nullable=False)
    
    standard_name = db.Column(db.String(128))
    standard_description = db.Column(db.Text)
    
    coordinate_id = db.Column(db.Integer, db.ForeignKey('unified_coordinates.id'), nullable=True)
    
    is_active = db.Column(db.Boolean, default=True)
    mapping_metadata = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    coordinate = db.relationship('UnifiedCoordinate', backref=db.backref('meta_tag_mappings', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('meta_tag', 'external_code', name='unique_meta_tag_code'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'mapping_id': self.mapping_id,
            'meta_tag': self.meta_tag,
            'external_code': self.external_code,
            'target_axis': self.target_axis,
            'nuremberg_value': self.nuremberg_value,
            'standard_name': self.standard_name,
            'standard_description': self.standard_description,
            'coordinate_id': self.coordinate_id,
            'is_active': self.is_active,
            'metadata': self.mapping_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AxisValue(db.Model):
    """
    Normalized storage for individual axis values within a coordinate.
    Preserves full AxisCoordinate semantics including hierarchical levels and meta-tags.
    """
    __tablename__ = 'axis_values'

    id = db.Column(db.Integer, primary_key=True)
    coordinate_id = db.Column(db.Integer, db.ForeignKey('unified_coordinates.id'), nullable=False, index=True)
    
    axis_number = db.Column(db.Integer, nullable=False, index=True)
    
    value = db.Column(db.String(128), nullable=False)
    levels = db.Column(db.JSON)
    depth = db.Column(db.Integer)
    
    meta_tag = db.Column(db.String(32), index=True)
    
    numeric_value = db.Column(db.Numeric(10, 4))
    confidence = db.Column(db.Numeric(5, 4))
    validation_status = db.Column(db.String(32))
    
    axis_metadata = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    coordinate = db.relationship('UnifiedCoordinate', backref=db.backref('axis_values', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('coordinate_id', 'axis_number', name='unique_coordinate_axis'),
        db.Index('ix_axis_values_coord_axis', 'coordinate_id', 'axis_number'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'coordinate_id': self.coordinate_id,
            'axis_number': self.axis_number,
            'value': self.value,
            'levels': self.levels,
            'depth': self.depth,
            'meta_tag': self.meta_tag,
            'numeric_value': float(self.numeric_value) if self.numeric_value else None,
            'confidence': float(self.confidence) if self.confidence else None,
            'validation_status': self.validation_status,
            'metadata': self.axis_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class AxisConfiguration(db.Model):
    """
    Store configuration for each of the 17 axes.
    Defines axis behavior, validation rules, and traversal patterns.
    """
    __tablename__ = 'axis_configurations'

    id = db.Column(db.Integer, primary_key=True)
    axis_number = db.Column(db.Integer, unique=True, nullable=False, index=True)
    
    axis_name = db.Column(db.String(64), nullable=False)
    axis_short_name = db.Column(db.String(32))
    axis_description = db.Column(db.Text)
    
    axis_category = db.Column(db.String(32))
    
    value_type = db.Column(db.String(32), default='hierarchical')
    max_depth = db.Column(db.Integer, default=10)
    separator = db.Column(db.String(4), default='.')
    
    validation_pattern = db.Column(db.String(256))
    validation_rules = db.Column(db.JSON)
    
    traversal_enabled = db.Column(db.Boolean, default=True)
    supported_traversals = db.Column(db.JSON)
    
    is_required = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    axis_metadata = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'axis_number': self.axis_number,
            'axis_name': self.axis_name,
            'axis_short_name': self.axis_short_name,
            'axis_description': self.axis_description,
            'axis_category': self.axis_category,
            'value_type': self.value_type,
            'max_depth': self.max_depth,
            'separator': self.separator,
            'validation_pattern': self.validation_pattern,
            'validation_rules': self.validation_rules,
            'traversal_enabled': self.traversal_enabled,
            'supported_traversals': self.supported_traversals,
            'is_required': self.is_required,
            'is_active': self.is_active,
            'metadata': self.axis_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }