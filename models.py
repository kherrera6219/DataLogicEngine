"""
Universal Knowledge Graph (UKG) Database Models

This module defines the database models for the UKG system.
"""

import uuid
import datetime
import json
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship, backref
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db

class User(UserMixin, db.Model):
    """User model for authentication and authorization."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    first_name = Column(String(64))
    last_name = Column(String(64))
    profile_image = Column(String(256))
    is_admin = Column(Boolean, default=False)
    is_active_status = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    simulation_sessions = relationship("SimulationSession", back_populates="user")
    
    @property
    def is_active(self):
        """Return whether the user is active or not."""
        return self.is_active_status
    
    def set_password(self, password):
        """Set the user password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check the user password."""
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        return False
    
    def to_dict(self):
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'profile_image': self.profile_image,
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class APIKey(db.Model):
    """API Key model for service authentication."""
    __tablename__ = 'api_keys'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    key = Column(String(64), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(Text)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime)
    last_used_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    def to_dict(self):
        """Convert API key to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'key': self.key,
            'name': self.name,
            'description': self.description,
            'user_id': self.user_id,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None
        }


class Node(db.Model):
    """Base model for all nodes in the UKG system."""
    __tablename__ = 'ukg_nodes'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    node_type = Column(String(100), nullable=False)
    label = Column(String(255), nullable=False)
    axis_number = Column(Integer, nullable=False)
    description = Column(Text)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    active = Column(Boolean, default=True)
    
    # Relationships
    outgoing_edges = relationship("Edge", foreign_keys="Edge.source_node_id", back_populates="source_node")
    incoming_edges = relationship("Edge", foreign_keys="Edge.target_node_id", back_populates="target_node")
    
    __mapper_args__ = {
        'polymorphic_identity': 'node',
        'polymorphic_on': node_type
    }
    
    def to_dict(self):
        """Convert node to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'node_type': self.node_type,
            'label': self.label,
            'axis_number': self.axis_number,
            'description': self.description,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'active': self.active
        }


class Edge(db.Model):
    """Base model for all edges in the UKG system."""
    __tablename__ = 'ukg_edges'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    edge_type = Column(String(100), nullable=False)
    label = Column(String(255))
    weight = Column(Float, default=1.0)
    source_node_id = Column(Integer, ForeignKey('ukg_nodes.id'), nullable=False)
    target_node_id = Column(Integer, ForeignKey('ukg_nodes.id'), nullable=False)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    active = Column(Boolean, default=True)
    
    # Relationships
    source_node = relationship("Node", foreign_keys=[source_node_id], back_populates="outgoing_edges")
    target_node = relationship("Node", foreign_keys=[target_node_id], back_populates="incoming_edges")
    
    def to_dict(self):
        """Convert edge to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'edge_type': self.edge_type,
            'label': self.label,
            'weight': self.weight,
            'source_node_id': self.source_node_id,
            'target_node_id': self.target_node_id,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'active': self.active
        }


class KnowledgeNode(Node):
    """Node representing knowledge content (Axis 1)."""
    __tablename__ = 'ukg_knowledge_nodes'
    
    id = Column(Integer, ForeignKey('ukg_nodes.id'), primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String(50), default='text')  # text, markdown, code, etc.
    confidence_score = Column(Float, default=0.85)
    source = Column(String(255))
    
    __mapper_args__ = {
        'polymorphic_identity': 'knowledge',
    }
    
    def to_dict(self):
        """Convert knowledge node to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'title': self.title,
            'content': self.content,
            'content_type': self.content_type,
            'confidence_score': self.confidence_score,
            'source': self.source
        })
        return base_dict


class SectorNode(Node):
    """Node representing sectors (Axis 2)."""
    __tablename__ = 'ukg_sector_nodes'
    
    id = Column(Integer, ForeignKey('ukg_nodes.id'), primary_key=True)
    sector_code = Column(String(20), unique=True)
    parent_sector_id = Column(Integer, ForeignKey('ukg_sector_nodes.id'))
    
    # Relationships
    parent_sector = relationship("SectorNode", remote_side=[id], backref="subsectors")
    
    __mapper_args__ = {
        'polymorphic_identity': 'sector',
    }
    
    def to_dict(self):
        """Convert sector node to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'sector_code': self.sector_code,
            'parent_sector_id': self.parent_sector_id
        })
        return base_dict


class DomainNode(Node):
    """Node representing domains (Axis 3)."""
    __tablename__ = 'ukg_domain_nodes'
    
    id = Column(Integer, ForeignKey('ukg_nodes.id'), primary_key=True)
    domain_code = Column(String(20), unique=True)
    sector_id = Column(Integer, ForeignKey('ukg_sector_nodes.id'))
    parent_domain_id = Column(Integer, ForeignKey('ukg_domain_nodes.id'))
    
    # Relationships
    sector = relationship("SectorNode")
    parent_domain = relationship("DomainNode", remote_side=[id], backref="subdomains")
    
    __mapper_args__ = {
        'polymorphic_identity': 'domain',
    }
    
    def to_dict(self):
        """Convert domain node to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'domain_code': self.domain_code,
            'sector_id': self.sector_id,
            'parent_domain_id': self.parent_domain_id
        })
        return base_dict


class MethodNode(Node):
    """Node representing methods (Axis 4)."""
    __tablename__ = 'ukg_method_nodes'
    
    id = Column(Integer, ForeignKey('ukg_nodes.id'), primary_key=True)
    method_code = Column(String(20), unique=True)
    parent_method_id = Column(Integer, ForeignKey('ukg_method_nodes.id'))
    
    # Relationships
    parent_method = relationship("MethodNode", remote_side=[id], backref="submethods")
    
    __mapper_args__ = {
        'polymorphic_identity': 'method',
    }
    
    def to_dict(self):
        """Convert method node to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'method_code': self.method_code,
            'parent_method_id': self.parent_method_id
        })
        return base_dict


class ContextNode(Node):
    """Node representing contexts (Axis 5)."""
    __tablename__ = 'ukg_context_nodes'
    
    id = Column(Integer, ForeignKey('ukg_nodes.id'), primary_key=True)
    context_type = Column(String(50))  # e.g., business, technical, social
    parent_context_id = Column(Integer, ForeignKey('ukg_context_nodes.id'))
    
    # Relationships
    parent_context = relationship("ContextNode", remote_side=[id], backref="subcontexts")
    
    __mapper_args__ = {
        'polymorphic_identity': 'context',
    }
    
    def to_dict(self):
        """Convert context node to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'context_type': self.context_type,
            'parent_context_id': self.parent_context_id
        })
        return base_dict


class ProblemNode(Node):
    """Node representing problems (Axis 6)."""
    __tablename__ = 'ukg_problem_nodes'
    
    id = Column(Integer, ForeignKey('ukg_nodes.id'), primary_key=True)
    problem_type = Column(String(50))  # e.g., technical, business, compliance
    severity = Column(Integer)  # e.g., 1-5
    parent_problem_id = Column(Integer, ForeignKey('ukg_problem_nodes.id'))
    
    # Relationships
    parent_problem = relationship("ProblemNode", remote_side=[id], backref="subproblems")
    
    __mapper_args__ = {
        'polymorphic_identity': 'problem',
    }
    
    def to_dict(self):
        """Convert problem node to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'problem_type': self.problem_type,
            'severity': self.severity,
            'parent_problem_id': self.parent_problem_id
        })
        return base_dict


class SolutionNode(Node):
    """Node representing solutions (Axis 7)."""
    __tablename__ = 'ukg_solution_nodes'
    
    id = Column(Integer, ForeignKey('ukg_nodes.id'), primary_key=True)
    solution_type = Column(String(50))  # e.g., technical, business, compliance
    effectiveness = Column(Float)  # e.g., 0-1.0
    parent_solution_id = Column(Integer, ForeignKey('ukg_solution_nodes.id'))
    
    # Relationships
    parent_solution = relationship("SolutionNode", remote_side=[id], backref="subsolutions")
    
    __mapper_args__ = {
        'polymorphic_identity': 'solution',
    }
    
    def to_dict(self):
        """Convert solution node to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'solution_type': self.solution_type,
            'effectiveness': self.effectiveness,
            'parent_solution_id': self.parent_solution_id
        })
        return base_dict


class RoleNode(Node):
    """Node representing roles (Axis 8)."""
    __tablename__ = 'ukg_role_nodes'
    
    id = Column(Integer, ForeignKey('ukg_nodes.id'), primary_key=True)
    role_code = Column(String(20), unique=True)
    responsibilities = Column(Text)
    parent_role_id = Column(Integer, ForeignKey('ukg_role_nodes.id'))
    
    # Relationships
    parent_role = relationship("RoleNode", remote_side=[id], backref="subroles")
    
    __mapper_args__ = {
        'polymorphic_identity': 'role',
    }
    
    def to_dict(self):
        """Convert role node to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'role_code': self.role_code,
            'responsibilities': self.responsibilities,
            'parent_role_id': self.parent_role_id
        })
        return base_dict


class ExpertNode(Node):
    """Node representing experts (Axis 9)."""
    __tablename__ = 'ukg_expert_nodes'
    
    id = Column(Integer, ForeignKey('ukg_nodes.id'), primary_key=True)
    expertise_areas = Column(Text)
    expertise_level = Column(Float)  # e.g., 0-1.0
    certifications = Column(Text)
    education = Column(Text)
    
    __mapper_args__ = {
        'polymorphic_identity': 'expert',
    }
    
    def to_dict(self):
        """Convert expert node to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'expertise_areas': self.expertise_areas,
            'expertise_level': self.expertise_level,
            'certifications': self.certifications,
            'education': self.education
        })
        return base_dict


class RegulationNode(Node):
    """Node representing regulations (Axis 10)."""
    __tablename__ = 'ukg_regulation_nodes'
    
    id = Column(Integer, ForeignKey('ukg_nodes.id'), primary_key=True)
    regulation_code = Column(String(50), unique=True)
    issuing_authority = Column(String(255))
    effective_date = Column(DateTime)
    text = Column(Text)
    parent_regulation_id = Column(Integer, ForeignKey('ukg_regulation_nodes.id'))
    
    # Relationships
    parent_regulation = relationship("RegulationNode", remote_side=[id], backref="subregulations")
    
    __mapper_args__ = {
        'polymorphic_identity': 'regulation',
    }
    
    def to_dict(self):
        """Convert regulation node to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'regulation_code': self.regulation_code,
            'issuing_authority': self.issuing_authority,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'text': self.text,
            'parent_regulation_id': self.parent_regulation_id
        })
        return base_dict


class ComplianceNode(Node):
    """Node representing compliance (Axis 11)."""
    __tablename__ = 'ukg_compliance_nodes'
    
    id = Column(Integer, ForeignKey('ukg_nodes.id'), primary_key=True)
    compliance_type = Column(String(50))
    regulation_id = Column(Integer, ForeignKey('ukg_regulation_nodes.id'))
    status = Column(String(50))  # e.g., compliant, non-compliant, in-progress
    due_date = Column(DateTime)
    parent_compliance_id = Column(Integer, ForeignKey('ukg_compliance_nodes.id'))
    
    # Relationships
    regulation = relationship("RegulationNode")
    parent_compliance = relationship("ComplianceNode", remote_side=[id], backref="subcompliance")
    
    __mapper_args__ = {
        'polymorphic_identity': 'compliance',
    }
    
    def to_dict(self):
        """Convert compliance node to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'compliance_type': self.compliance_type,
            'regulation_id': self.regulation_id,
            'status': self.status,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'parent_compliance_id': self.parent_compliance_id
        })
        return base_dict


class LocationNode(Node):
    """Node representing locations (Axis 12)."""
    __tablename__ = 'ukg_location_nodes'
    
    id = Column(Integer, ForeignKey('ukg_nodes.id'), primary_key=True)
    location_type = Column(String(50))  # e.g., country, city, region
    latitude = Column(Float)
    longitude = Column(Float)
    parent_location_id = Column(Integer, ForeignKey('ukg_location_nodes.id'))
    
    # Relationships
    parent_location = relationship("LocationNode", remote_side=[id], backref="sublocations")
    
    __mapper_args__ = {
        'polymorphic_identity': 'location',
    }
    
    def to_dict(self):
        """Convert location node to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'location_type': self.location_type,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'parent_location_id': self.parent_location_id
        })
        return base_dict


class TimeNode(Node):
    """Node representing time (Axis 13)."""
    __tablename__ = 'ukg_time_nodes'
    
    id = Column(Integer, ForeignKey('ukg_nodes.id'), primary_key=True)
    time_type = Column(String(50))  # e.g., historical, future, recurring
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    granularity = Column(String(20))  # e.g., year, month, day
    recurring = Column(Boolean, default=False)
    parent_time_id = Column(Integer, ForeignKey('ukg_time_nodes.id'))
    
    # Relationships
    parent_time = relationship("TimeNode", remote_side=[id], backref="subtimes")
    
    __mapper_args__ = {
        'polymorphic_identity': 'time',
    }
    
    def to_dict(self):
        """Convert time node to dictionary."""
        base_dict = super().to_dict()
        base_dict.update({
            'time_type': self.time_type,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'granularity': self.granularity,
            'recurring': self.recurring,
            'parent_time_id': self.parent_time_id
        })
        return base_dict


class KnowledgeAlgorithm(db.Model):
    """Model for Knowledge Algorithms that operate on the UKG."""
    __tablename__ = 'ukg_knowledge_algorithms'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    algorithm_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    version = Column(String(20), nullable=False)
    code = Column(Text, nullable=False)
    language = Column(String(50), default='python')
    input_schema = Column(JSON, nullable=False)
    output_schema = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    executions = relationship("KnowledgeAlgorithmExecution", back_populates="algorithm", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert knowledge algorithm to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'algorithm_id': self.algorithm_id,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'language': self.language,
            'input_schema': self.input_schema,
            'output_schema': self.output_schema,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }


class KnowledgeAlgorithmExecution(db.Model):
    """Model for Knowledge Algorithm Executions."""
    __tablename__ = 'ukg_knowledge_algorithm_executions'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    algorithm_id = Column(Integer, ForeignKey('ukg_knowledge_algorithms.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    status = Column(String(20), nullable=False, default='pending')  # pending, running, completed, failed
    input_params = Column(JSON, nullable=False)
    output_results = Column(JSON)
    error_message = Column(Text)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime)
    execution_time = Column(Float)  # in seconds
    
    # Relationships
    algorithm = relationship("KnowledgeAlgorithm", back_populates="executions")
    user = relationship("User")
    
    def to_dict(self):
        """Convert knowledge algorithm execution to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'algorithm_id': self.algorithm_id,
            'user_id': self.user_id,
            'status': self.status,
            'input_params': self.input_params,
            'output_results': self.output_results,
            'error_message': self.error_message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'execution_time': self.execution_time
        }


class SimulationSession(db.Model):
    """Model for Simulation Sessions."""
    __tablename__ = 'ukg_simulation_sessions'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(255))
    user_id = Column(Integer, ForeignKey('users.id'))
    parameters = Column(JSON, nullable=False)
    status = Column(String(20), nullable=False, default='pending')  # pending, running, completed, stopped, failed
    current_step = Column(Integer, default=0)
    total_steps = Column(Integer)
    results = Column(JSON)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_step_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="simulation_sessions")
    
    def to_dict(self):
        """Convert simulation session to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'session_id': self.session_id,
            'name': self.name,
            'user_id': self.user_id,
            'parameters': self.parameters,
            'status': self.status,
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'results': self.results,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'last_step_at': self.last_step_at.isoformat() if self.last_step_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }