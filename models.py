"""
Universal Knowledge Graph (UKG) System - Models

This module defines database models for the UKG system.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

class Conversation(db.Model):
    """Model for chat conversations in the UKG system."""
    __tablename__ = 'ukg_conversations'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert conversation to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'title': self.title,
            'metadata': self.meta_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Message(db.Model):
    """Model for chat messages in the UKG system."""
    __tablename__ = 'ukg_messages'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    conversation_id = Column(Integer, ForeignKey('ukg_conversations.id'), nullable=False)
    content = Column(Text, nullable=False)
    role = Column(String(50), nullable=False)  # e.g., "user", "system"
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def to_dict(self):
        """Convert message to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'conversation_id': self.conversation_id,
            'content': self.content,
            'role': self.role,
            'metadata': self.meta_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Node(db.Model):
    """Model for nodes in the UKG knowledge graph."""
    __tablename__ = 'ukg_nodes'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    node_type = Column(String(100), nullable=False)
    label = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    original_id = Column(String(255), nullable=True)
    axis_number = Column(Integer, nullable=True)
    level = Column(Integer, nullable=True)
    attributes = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    source_edges = relationship("Edge", foreign_keys="Edge.source_id", back_populates="source", cascade="all, delete-orphan")
    target_edges = relationship("Edge", foreign_keys="Edge.target_id", back_populates="target", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert node to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'node_type': self.node_type,
            'label': self.label,
            'description': self.description,
            'original_id': self.original_id,
            'axis_number': self.axis_number,
            'level': self.level,
            'attributes': self.attributes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Edge(db.Model):
    """Model for edges in the UKG knowledge graph."""
    __tablename__ = 'ukg_edges'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    edge_type = Column(String(100), nullable=False)
    source_id = Column(Integer, ForeignKey('ukg_nodes.id'), nullable=False)
    target_id = Column(Integer, ForeignKey('ukg_nodes.id'), nullable=False)
    label = Column(String(255), nullable=True)
    weight = Column(Float, default=1.0)
    attributes = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    source = relationship("Node", foreign_keys=[source_id], back_populates="source_edges")
    target = relationship("Node", foreign_keys=[target_id], back_populates="target_edges")
    
    def to_dict(self):
        """Convert edge to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'edge_type': self.edge_type,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'label': self.label,
            'weight': self.weight,
            'attributes': self.attributes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class KnowledgeAlgorithm(db.Model):
    """Model for knowledge algorithms in the UKG system."""
    __tablename__ = 'ukg_knowledge_algorithms'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(10), nullable=False)  # e.g., "KA-01"
    version = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    parameters = Column(JSON, nullable=True)
    meta_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    executions = relationship("KAExecution", back_populates="algorithm", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert algorithm to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'name': self.name,
            'code': self.code,
            'version': self.version,
            'description': self.description,
            'parameters': self.parameters,
            'metadata': self.meta_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class KAExecution(db.Model):
    """Model for knowledge algorithm executions in the UKG system."""
    __tablename__ = 'ukg_ka_executions'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    algorithm_id = Column(Integer, ForeignKey('ukg_knowledge_algorithms.id'), nullable=False)
    session_id = Column(Integer, ForeignKey('ukg_sessions.id'), nullable=True)
    status = Column(String(50), nullable=False)  # e.g., "success", "failed"
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration_ms = Column(Float, nullable=True)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    meta_data = Column(JSON, nullable=True)
    
    # Relationships
    algorithm = relationship("KnowledgeAlgorithm", back_populates="executions")
    session = relationship("Session", back_populates="executions")
    
    def to_dict(self):
        """Convert execution to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'algorithm_id': self.algorithm_id,
            'session_id': self.session_id,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_ms': self.duration_ms,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'error_message': self.error_message,
            'metadata': self.meta_data
        }

class Session(db.Model):
    """Model for UKG simulation sessions."""
    __tablename__ = 'ukg_sessions'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    session_type = Column(String(100), nullable=False)  # e.g., "quad_persona", "refinement"
    status = Column(String(50), nullable=False)  # e.g., "active", "completed"
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    query = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    refinement_cycles = Column(Integer, nullable=True, default=0)
    meta_data = Column(JSON, nullable=True)
    
    # Relationships
    executions = relationship("KAExecution", back_populates="session")
    memory_entries = relationship("MemoryEntry", back_populates="session")
    
    def to_dict(self):
        """Convert session to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'session_type': self.session_type,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'query': self.query,
            'confidence_score': self.confidence_score,
            'refinement_cycles': self.refinement_cycles,
            'metadata': self.meta_data
        }

class MemoryEntry(db.Model):
    """Model for UKG memory entries."""
    __tablename__ = 'ukg_memory_entries'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    session_id = Column(Integer, ForeignKey('ukg_sessions.id'), nullable=True)
    memory_type = Column(String(100), nullable=False)  # e.g., "knowledge", "context"
    key = Column(String(255), nullable=True)
    content = Column(JSON, nullable=False)
    confidence = Column(Float, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    expiration = Column(DateTime, nullable=True)
    meta_data = Column(JSON, nullable=True)
    
    # Relationships
    session = relationship("Session", back_populates="memory_entries")
    
    def to_dict(self):
        """Convert memory entry to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'session_id': self.session_id,
            'memory_type': self.memory_type,
            'key': self.key,
            'content': self.content,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'expiration': self.expiration.isoformat() if self.expiration else None,
            'metadata': self.meta_data
        }