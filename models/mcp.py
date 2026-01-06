from datetime import datetime, UTC
from extensions import db

def _utcnow():
    """Return current UTC datetime."""
    return datetime.now(UTC)

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
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)
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
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

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
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

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
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

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
