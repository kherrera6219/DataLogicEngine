"""
Universal Knowledge Graph (UKG) System - Database Models

This module defines the database models for the UKG system.
"""

import datetime
import uuid
import json
from typing import Any, Dict, List, Optional, Type, Union
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, Table, MetaData, JSON
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from app import db

# Base model for all entities with common fields
class BaseModel:
    """Base model with common fields for all models."""
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to a dictionary."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime.datetime):
                result[column.name] = value.isoformat()
            elif isinstance(value, (dict, list)):
                result[column.name] = value
            else:
                result[column.name] = str(value) if value is not None else None
        return result

# User model
class User(UserMixin, BaseModel, db.Model):
    """User model representing system users."""
    
    __tablename__ = 'users'
    
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    is_active_status = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    first_name = Column(String(64), nullable=True)
    last_name = Column(String(64), nullable=True)
    profile_image_url = Column(String(256), nullable=True)
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    simulation_sessions = relationship("SimulationSession", back_populates="user", cascade="all, delete-orphan")
    
    @property
    def is_active(self):
        """Check if user is active."""
        return self.is_active_status
    
    def set_password(self, password: str) -> None:
        """Set the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the user's password."""
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        return False
    
    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username
    
    def __repr__(self) -> str:
        return f"<User {self.username}>"

# API Key model
class APIKey(BaseModel, db.Model):
    """API key model for authentication."""
    
    __tablename__ = 'api_keys'
    
    key = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(64), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime, nullable=True)
    allowed_ips = Column(Text, nullable=True)  # Comma-separated list of IPs
    allowed_origins = Column(Text, nullable=True)  # Comma-separated list of origins
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    def is_valid(self) -> bool:
        """Check if the API key is valid."""
        if not self.is_active:
            return False
        
        if self.expires_at and self.expires_at < datetime.datetime.utcnow():
            return False
        
        return True
    
    def get_allowed_ips(self) -> List[str]:
        """Get the list of allowed IPs."""
        if not self.allowed_ips:
            return []
        return [ip.strip() for ip in self.allowed_ips.split(',')]
    
    def get_allowed_origins(self) -> List[str]:
        """Get the list of allowed origins."""
        if not self.allowed_origins:
            return []
        return [origin.strip() for origin in self.allowed_origins.split(',')]
    
    def __repr__(self) -> str:
        return f"<APIKey {self.name}>"

# Node base model
class Node(BaseModel, db.Model):
    """Base node model for knowledge graph."""
    
    __tablename__ = 'nodes'
    
    node_type = Column(String(50), nullable=False, index=True)
    label = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    axis_number = Column(Integer, nullable=False, index=True)  # 1-13 axis system
    metadata = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # SQLAlchemy polymorphic support
    __mapper_args__ = {
        'polymorphic_identity': 'node',
        'polymorphic_on': node_type
    }
    
    # Relationships
    outgoing_edges = relationship("Edge", foreign_keys="Edge.source_node_id", back_populates="source_node", cascade="all, delete-orphan")
    incoming_edges = relationship("Edge", foreign_keys="Edge.target_node_id", back_populates="target_node", cascade="all, delete-orphan")
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get the node metadata."""
        if not self.metadata:
            return {}
        return self.metadata
    
    def set_metadata(self, metadata: Dict[str, Any]) -> None:
        """Set the node metadata."""
        self.metadata = metadata
    
    def add_metadata(self, key: str, value: Any) -> None:
        """Add a key-value pair to the metadata."""
        metadata = self.get_metadata()
        metadata[key] = value
        self.set_metadata(metadata)
    
    def __repr__(self) -> str:
        return f"<Node {self.label} (Axis {self.axis_number})>"

# Specific node types for the 13 axes

# Axis 1: Knowledge
class KnowledgeNode(Node):
    """Knowledge node (Axis 1)."""
    
    __mapper_args__ = {
        'polymorphic_identity': 'knowledge'
    }
    
    def __init__(self, **kwargs):
        kwargs['axis_number'] = 1
        super().__init__(**kwargs)

# Axis 2: Sectors
class SectorNode(Node):
    """Sector node (Axis 2)."""
    
    __mapper_args__ = {
        'polymorphic_identity': 'sector'
    }
    
    def __init__(self, **kwargs):
        kwargs['axis_number'] = 2
        super().__init__(**kwargs)

# Axis 3: Domains
class DomainNode(Node):
    """Domain node (Axis 3)."""
    
    __mapper_args__ = {
        'polymorphic_identity': 'domain'
    }
    
    def __init__(self, **kwargs):
        kwargs['axis_number'] = 3
        super().__init__(**kwargs)

# Axis 4: Methods
class MethodNode(Node):
    """Method node (Axis 4)."""
    
    __mapper_args__ = {
        'polymorphic_identity': 'method'
    }
    
    def __init__(self, **kwargs):
        kwargs['axis_number'] = 4
        super().__init__(**kwargs)

# Axis 5: Contexts
class ContextNode(Node):
    """Context node (Axis 5)."""
    
    __mapper_args__ = {
        'polymorphic_identity': 'context'
    }
    
    def __init__(self, **kwargs):
        kwargs['axis_number'] = 5
        super().__init__(**kwargs)

# Axis 6: Problems
class ProblemNode(Node):
    """Problem node (Axis 6)."""
    
    __mapper_args__ = {
        'polymorphic_identity': 'problem'
    }
    
    def __init__(self, **kwargs):
        kwargs['axis_number'] = 6
        super().__init__(**kwargs)

# Axis 7: Solutions
class SolutionNode(Node):
    """Solution node (Axis 7)."""
    
    __mapper_args__ = {
        'polymorphic_identity': 'solution'
    }
    
    def __init__(self, **kwargs):
        kwargs['axis_number'] = 7
        super().__init__(**kwargs)

# Axis 8: Roles
class RoleNode(Node):
    """Role node (Axis 8)."""
    
    __mapper_args__ = {
        'polymorphic_identity': 'role'
    }
    
    def __init__(self, **kwargs):
        kwargs['axis_number'] = 8
        super().__init__(**kwargs)

# Axis 9: Experts
class ExpertNode(Node):
    """Expert node (Axis 9)."""
    
    __mapper_args__ = {
        'polymorphic_identity': 'expert'
    }
    
    def __init__(self, **kwargs):
        kwargs['axis_number'] = 9
        super().__init__(**kwargs)

# Axis 10: Regulations
class RegulationNode(Node):
    """Regulation node (Axis 10)."""
    
    __mapper_args__ = {
        'polymorphic_identity': 'regulation'
    }
    
    def __init__(self, **kwargs):
        kwargs['axis_number'] = 10
        super().__init__(**kwargs)

# Axis 11: Compliance
class ComplianceNode(Node):
    """Compliance node (Axis 11)."""
    
    __mapper_args__ = {
        'polymorphic_identity': 'compliance'
    }
    
    def __init__(self, **kwargs):
        kwargs['axis_number'] = 11
        super().__init__(**kwargs)

# Axis 12: Location
class LocationNode(Node):
    """Location node (Axis 12)."""
    
    __mapper_args__ = {
        'polymorphic_identity': 'location'
    }
    
    def __init__(self, **kwargs):
        kwargs['axis_number'] = 12
        super().__init__(**kwargs)

# Axis 13: Time
class TimeNode(Node):
    """Time node (Axis 13)."""
    
    __mapper_args__ = {
        'polymorphic_identity': 'time'
    }
    
    def __init__(self, **kwargs):
        kwargs['axis_number'] = 13
        super().__init__(**kwargs)

# Edge model for connecting nodes
class Edge(BaseModel, db.Model):
    """Edge model for connecting nodes in the knowledge graph."""
    
    __tablename__ = 'edges'
    
    source_node_id = Column(Integer, ForeignKey('nodes.id'), nullable=False, index=True)
    target_node_id = Column(Integer, ForeignKey('nodes.id'), nullable=False, index=True)
    label = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    edge_type = Column(String(50), nullable=False, index=True)
    weight = Column(Float, default=1.0, nullable=False)
    metadata = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Relationships
    source_node = relationship("Node", foreign_keys=[source_node_id], back_populates="outgoing_edges")
    target_node = relationship("Node", foreign_keys=[target_node_id], back_populates="incoming_edges")
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get the edge metadata."""
        if not self.metadata:
            return {}
        return self.metadata
    
    def set_metadata(self, metadata: Dict[str, Any]) -> None:
        """Set the edge metadata."""
        self.metadata = metadata
    
    def __repr__(self) -> str:
        return f"<Edge {self.label} ({self.source_node_id} -> {self.target_node_id})>"

# Knowledge Algorithm model
class KnowledgeAlgorithm(BaseModel, db.Model):
    """Knowledge Algorithm model representing system algorithms."""
    
    __tablename__ = 'knowledge_algorithms'
    
    code = Column(String(20), nullable=False, unique=True, index=True)
    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False, index=True)
    implementation = Column(Text, nullable=False)  # The actual algorithm code or reference
    parameters = Column(JSON, nullable=True)  # Default parameters
    version = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    dependencies = Column(JSON, nullable=True)  # List of dependencies
    average_runtime = Column(Float, nullable=True)  # Average runtime in seconds
    
    # Relationships
    executions = relationship("KnowledgeAlgorithmExecution", back_populates="algorithm", cascade="all, delete-orphan")
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get the algorithm parameters."""
        if not self.parameters:
            return {}
        return self.parameters
    
    def get_dependencies(self) -> List[str]:
        """Get the algorithm dependencies."""
        if not self.dependencies:
            return []
        return self.dependencies
    
    def __repr__(self) -> str:
        return f"<KnowledgeAlgorithm {self.code}: {self.name}>"

# Knowledge Algorithm Execution model
class KnowledgeAlgorithmExecution(BaseModel, db.Model):
    """Knowledge Algorithm Execution model representing algorithm runs."""
    
    __tablename__ = 'knowledge_algorithm_executions'
    
    algorithm_id = Column(Integer, ForeignKey('knowledge_algorithms.id'), nullable=False, index=True)
    session_id = Column(String(64), ForeignKey('simulation_sessions.session_id'), nullable=False, index=True)
    parameters = Column(JSON, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default='running')  # running, completed, failed
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    runtime = Column(Float, nullable=True)  # Runtime in seconds
    layer = Column(Integer, nullable=False)  # The layer in which this algorithm was executed
    
    # Relationships
    algorithm = relationship("KnowledgeAlgorithm", back_populates="executions")
    simulation_session = relationship("SimulationSession", back_populates="algorithm_executions")
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get the execution parameters."""
        if not self.parameters:
            return {}
        return self.parameters
    
    def get_result(self) -> Any:
        """Get the execution result."""
        if not self.result:
            return None
        return self.result
    
    def __repr__(self) -> str:
        return f"<KnowledgeAlgorithmExecution {self.id} ({self.algorithm_id}, {self.session_id})>"

# Simulation Session model
class SimulationSession(BaseModel, db.Model):
    """Simulation Session model representing simulation runs."""
    
    __tablename__ = 'simulation_sessions'
    
    session_id = Column(String(64), primary_key=True, unique=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    name = Column(String(256), nullable=True)
    description = Column(Text, nullable=True)
    parameters = Column(JSON, nullable=True)
    status = Column(String(20), nullable=False, default='pending')  # pending, running, completed, failed, cancelled
    current_step = Column(Integer, nullable=False, default=0)
    total_steps = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    last_step_at = Column(DateTime, nullable=True)
    active_layer = Column(Integer, nullable=True)
    confidence_score = Column(Float, nullable=True)
    max_layer_reached = Column(Integer, nullable=True)
    results = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="simulation_sessions")
    algorithm_executions = relationship("KnowledgeAlgorithmExecution", back_populates="simulation_session", cascade="all, delete-orphan")
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get the simulation parameters."""
        if not self.parameters:
            return {}
        return self.parameters
    
    def get_results(self) -> Any:
        """Get the simulation results."""
        if not self.results:
            return None
        return self.results
    
    def __repr__(self) -> str:
        return f"<SimulationSession {self.session_id}>"