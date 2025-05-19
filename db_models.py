"""
Universal Knowledge Graph (UKG) Database Models

This module defines improved database models that fix validation issues 
and provide a proper structure for the 13-axis knowledge graph system.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app import db

# Base Models for UKG Core Components

class Node(db.Model):
    """Base model for all nodes in the UKG system."""
    __tablename__ = 'ukg_nodes'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    node_type = Column(String(100), nullable=False)
    label = Column(String(255), nullable=False)
    axis_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    attributes = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    active = Column(Boolean, default=True)
    
    # Relationships
    outgoing_edges = relationship("Edge", foreign_keys="Edge.source_node_id", back_populates="source_node")
    incoming_edges = relationship("Edge", foreign_keys="Edge.target_node_id", back_populates="target_node")
    
    def to_dict(self):
        """Convert node to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'node_type': self.node_type,
            'label': self.label,
            'axis_number': self.axis_number,
            'description': self.description,
            'attributes': self.attributes or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'active': self.active
        }

class Edge(db.Model):
    """Base model for all edges in the UKG system."""
    __tablename__ = 'ukg_edges'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    edge_type = Column(String(100), nullable=False)
    weight = Column(Float, default=1.0)
    source_node_id = Column(Integer, ForeignKey('ukg_nodes.id'), nullable=False)
    target_node_id = Column(Integer, ForeignKey('ukg_nodes.id'), nullable=False)
    attributes = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
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
            'weight': self.weight,
            'source_node_id': self.source_node_id,
            'target_node_id': self.target_node_id,
            'attributes': self.attributes or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'active': self.active
        }

# Axis 1: Knowledge - Pillar Levels

class PillarLevel(db.Model):
    """Model for Pillar Levels (Axis 1: Knowledge)."""
    __tablename__ = 'ukg_pillar_levels'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    pillar_id = Column(String(10), unique=True, nullable=False)  # e.g., "PL01", "PL48"
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    sublevels = Column(JSON, nullable=True)  # Nested structure for sublevels
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    nodes = relationship("KnowledgeNode", back_populates="pillar_level")
    
    def to_dict(self):
        """Convert pillar level to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'pillar_id': self.pillar_id,
            'name': self.name,
            'description': self.description,
            'sublevels': self.sublevels or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Axis 2: Sectors

class Sector(db.Model):
    """Model for Sectors (Axis 2: Sectors)."""
    __tablename__ = 'ukg_sectors'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    sector_code = Column(String(20), unique=True, nullable=False)  # e.g., "GOV", "TECH"
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    parent_sector_id = Column(Integer, ForeignKey('ukg_sectors.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    parent_sector = relationship("Sector", remote_side=[id])
    subsectors = relationship("Sector", foreign_keys=[parent_sector_id])
    domains = relationship("Domain", back_populates="sector")
    
    def to_dict(self):
        """Convert sector to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'sector_code': self.sector_code,
            'name': self.name,
            'description': self.description,
            'parent_sector_id': self.parent_sector_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'subsector_count': len(self.subsectors) if self.subsectors else 0
        }

# Axis 3: Domains

class Domain(db.Model):
    """Model for Domains (Axis 3: Domains)."""
    __tablename__ = 'ukg_domains'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    domain_code = Column(String(20), unique=True, nullable=False)  # e.g., "FEDGOV", "CSEC"
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    sector_id = Column(Integer, ForeignKey('ukg_sectors.id'), nullable=True)
    parent_domain_id = Column(Integer, ForeignKey('ukg_domains.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sector = relationship("Sector", back_populates="domains")
    parent_domain = relationship("Domain", remote_side=[id])
    subdomains = relationship("Domain", foreign_keys=[parent_domain_id])
    
    def to_dict(self):
        """Convert domain to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'domain_code': self.domain_code,
            'name': self.name,
            'description': self.description,
            'sector_id': self.sector_id,
            'sector_name': self.sector.name if self.sector else None,
            'parent_domain_id': self.parent_domain_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'subdomain_count': len(self.subdomains) if self.subdomains else 0
        }

# Axis 12: Location Context

class Location(db.Model):
    """Model for Locations (Axis 12: Location)."""
    __tablename__ = 'ukg_locations'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    location_type = Column(String(50), nullable=False)  # e.g., "country", "city", "virtual"
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    parent_location_id = Column(Integer, ForeignKey('ukg_locations.id'), nullable=True)
    attributes = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    parent_location = relationship("Location", remote_side=[id])
    sub_locations = relationship("Location", foreign_keys=[parent_location_id])
    
    def to_dict(self):
        """Convert location to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'name': self.name,
            'location_type': self.location_type,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'parent_location_id': self.parent_location_id,
            'attributes': self.attributes or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Knowledge Nodes - Specialized node type for knowledge content

class KnowledgeNode(db.Model):
    """Model for Knowledge Nodes containing actual knowledge content."""
    __tablename__ = 'ukg_knowledge_nodes'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String(50), nullable=False)  # e.g., "text", "markdown", "code"
    pillar_level_id = Column(Integer, ForeignKey('ukg_pillar_levels.id'), nullable=True)
    domain_id = Column(Integer, ForeignKey('ukg_domains.id'), nullable=True)
    location_id = Column(Integer, ForeignKey('ukg_locations.id'), nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pillar_level = relationship("PillarLevel", back_populates="nodes")
    
    def to_dict(self):
        """Convert knowledge node to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'title': self.title,
            'content_type': self.content_type,
            'content_preview': self.content[:100] + '...' if len(self.content) > 100 else self.content,
            'pillar_level_id': self.pillar_level_id,
            'pillar_id': self.pillar_level.pillar_id if self.pillar_level else None,
            'domain_id': self.domain_id,
            'location_id': self.location_id,
            'metadata': self.metadata or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Knowledge Algorithms

class KnowledgeAlgorithm(db.Model):
    """Model for Knowledge Algorithms that can be executed on the knowledge graph."""
    __tablename__ = 'ukg_knowledge_algorithms'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    algorithm_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    code = Column(Text, nullable=False)
    language = Column(String(50), nullable=False)  # e.g., "python", "javascript"
    version = Column(String(20), nullable=False)
    input_schema = Column(JSON, nullable=False)
    output_schema = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    executions = relationship("KAExecution", back_populates="algorithm")
    
    def to_dict(self):
        """Convert knowledge algorithm to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'algorithm_id': self.algorithm_id,
            'name': self.name,
            'description': self.description,
            'language': self.language,
            'version': self.version,
            'input_schema': self.input_schema,
            'output_schema': self.output_schema,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class KAExecution(db.Model):
    """Model for Knowledge Algorithm Executions."""
    __tablename__ = 'ukg_ka_executions'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    algorithm_id = Column(Integer, ForeignKey('ukg_knowledge_algorithms.id'), nullable=False)
    input_params = Column(JSON, nullable=False)
    output_results = Column(JSON, nullable=True)
    status = Column(String(20), nullable=False)  # e.g., "pending", "running", "completed", "failed"
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    algorithm = relationship("KnowledgeAlgorithm", back_populates="executions")
    
    def to_dict(self):
        """Convert algorithm execution to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'algorithm_id': self.algorithm_id,
            'algorithm_name': self.algorithm.name if self.algorithm else None,
            'input_params': self.input_params,
            'output_results': self.output_results,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'execution_time': (self.completed_at - self.started_at).total_seconds() if self.completed_at else None
        }

# Simulation Sessions

class SimulationSession(db.Model):
    """Model for Simulation Sessions."""
    __tablename__ = 'ukg_simulation_sessions'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    session_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=True)
    parameters = Column(JSON, nullable=False)
    status = Column(String(20), nullable=False)  # e.g., "active", "completed", "stopped", "failed"
    current_step = Column(Integer, default=0)
    results = Column(JSON, nullable=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_step_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    def to_dict(self):
        """Convert simulation session to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'session_id': self.session_id,
            'name': self.name,
            'status': self.status,
            'current_step': self.current_step,
            'parameters': self.parameters,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'last_step_at': self.last_step_at.isoformat() if self.last_step_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'elapsed_time': (datetime.utcnow() - self.started_at).total_seconds() if self.started_at else None
        }