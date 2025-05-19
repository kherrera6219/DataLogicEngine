import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON, text
from sqlalchemy.orm import relationship, Query

# Setup base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with our base
db = SQLAlchemy(model_class=Base)

# Node model - represents nodes in the Universal Knowledge Graph
class Node(db.Model):
    __tablename__ = 'nodes'
    
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
    outgoing_edges = relationship("Edge", foreign_keys="Edge.source_id", back_populates="source")
    incoming_edges = relationship("Edge", foreign_keys="Edge.target_id", back_populates="target")
    
    def __repr__(self):
        return f"<Node {self.uid}: {self.label}>"

# Edge model - represents connections between nodes in the graph
class Edge(db.Model):
    __tablename__ = 'edges'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    edge_type = Column(String(100), nullable=False)
    source_id = Column(Integer, ForeignKey('nodes.id'), nullable=False)
    target_id = Column(Integer, ForeignKey('nodes.id'), nullable=False)
    label = Column(String(255), nullable=True)
    weight = Column(Float, default=1.0)
    attributes = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    source = relationship("Node", foreign_keys=[source_id], back_populates="outgoing_edges")
    target = relationship("Node", foreign_keys=[target_id], back_populates="incoming_edges")
    
    def __repr__(self):
        return f"<Edge {self.uid}: {self.source_id} -> {self.target_id}>"

# KnowledgeAlgorithm model - stores information about available KAs
class KnowledgeAlgorithm(db.Model):
    __tablename__ = 'knowledge_algorithms'
    
    id = Column(Integer, primary_key=True)
    ka_id = Column(String(100), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    input_schema = Column(JSON, nullable=True)
    output_schema = Column(JSON, nullable=True)
    version = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    executions = relationship("KAExecution", back_populates="algorithm")
    
    def __repr__(self):
        return f"<KnowledgeAlgorithm {self.ka_id}: {self.name}>"

# KAExecution model - tracks executions of Knowledge Algorithms
class KAExecution(db.Model):
    __tablename__ = 'ka_executions'
    
    id = Column(Integer, primary_key=True)
    algorithm_id = Column(Integer, ForeignKey('knowledge_algorithms.id'), nullable=False)
    session_id = Column(String(255), nullable=False)
    pass_num = Column(Integer, default=0)
    layer_num = Column(Integer, default=0)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    confidence = Column(Float, default=0.0)
    execution_time = Column(Float, nullable=True)  # in milliseconds
    status = Column(String(50), default='pending')
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    algorithm = relationship("KnowledgeAlgorithm", back_populates="executions")
    
    def __repr__(self):
        return f"<KAExecution {self.id}: {self.algorithm.ka_id if self.algorithm else 'Unknown'} ({self.status})>"

# Session model - represents a user interaction session
class Session(db.Model):
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), unique=True, nullable=False)
    query_text = Column(Text, nullable=True)
    target_confidence = Column(Float, default=0.85)
    final_confidence = Column(Float, nullable=True)
    status = Column(String(50), default='active')
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    memory_entries = relationship("MemoryEntry", back_populates="session")
    
    def __repr__(self):
        return f"<Session {self.session_id}: {self.status}>"

# MemoryEntry model - represents entries in the structured memory store
class MemoryEntry(db.Model):
    __tablename__ = 'memory_entries'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    session_id = Column(String(255), ForeignKey('sessions.session_id'), nullable=False, index=True)
    entry_type = Column(String(100), nullable=False)
    pass_num = Column(Integer, default=0)
    layer_num = Column(Integer, default=0)
    content = Column(JSON, nullable=True)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="memory_entries")
    
    def __repr__(self):
        return f"<MemoryEntry {self.uid}: {self.entry_type}>"