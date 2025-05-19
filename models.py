"""
Universal Knowledge Graph (UKG) System - Models

This module defines database models for the UKG chat interface.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
# We'll import the db instance from where it's used

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