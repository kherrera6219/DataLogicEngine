"""
Universal Knowledge Graph (UKG) System - Models

This module defines all database models for the system.
It acts as a single import point for all models.
"""

# Import models from db_models.py to avoid duplication
from db_models import Node, Edge, PillarLevel, Sector, Domain
from db_models import Location, KnowledgeNode, KnowledgeAlgorithm, KAExecution, SimulationSession

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app import db

class Conversation(db.Model):
    """Model for chat conversations in the UKG system."""
    __tablename__ = 'ukg_conversations'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    metadata = Column(JSON, nullable=True)
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
            'metadata': self.metadata,
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
    metadata = Column(JSON, nullable=True)
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
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class SimulationSession(db.Model):
    """Model for Simulation Sessions."""
    __tablename__ = 'ukg_simulation_sessions'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
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
            'name': self.name,
            'parameters': self.parameters,
            'status': self.status,
            'current_step': self.current_step,
            'results': self.results,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'last_step_at': self.last_step_at.isoformat() if self.last_step_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }