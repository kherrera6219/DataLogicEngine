"""
Universal Knowledge Graph (UKG) System - Database Models

This module defines the database models for the UKG system following
enterprise-grade standards for data integrity and security.
"""

import datetime
import uuid
from app import db
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON, UniqueConstraint, Table
from sqlalchemy.orm import relationship, backref
from werkzeug.security import generate_password_hash, check_password_hash

# Custom UUID generator
def generate_uuid():
    return str(uuid.uuid4())

# User model
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(36), default=generate_uuid, unique=True, nullable=False)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    password_hash = Column(String(256))
    role = Column(String(20), default='user')  # admin, user, viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    settings = Column(JSON, nullable=True)
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    media_items = relationship("MediaItem", back_populates="created_by")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.uid,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

# API Key model
class APIKey(db.Model):
    __tablename__ = 'api_keys'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(36), default=generate_uuid, unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(256), nullable=False)
    service = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    expiry_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    def to_dict(self):
        return {
            'id': self.uid,
            'name': self.name,
            'service': self.service,
            'is_active': self.is_active,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat() if self.last_used else None
        }

# System Log model
class SystemLog(db.Model):
    __tablename__ = 'system_logs'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(36), default=generate_uuid, unique=True, nullable=False)
    log_type = Column(String(20), nullable=False)  # system, simulation, user
    level = Column(String(20), nullable=False)     # info, warning, error, debug
    source = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.uid,
            'log_type': self.log_type,
            'level': self.level,
            'source': self.source,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }

# Media Item model (for generated images and videos)
class MediaItem(db.Model):
    __tablename__ = 'media_items'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(36), default=generate_uuid, unique=True, nullable=False)
    media_type = Column(String(20), nullable=False)  # image, video
    prompt = Column(Text, nullable=False)
    url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    metadata = Column(JSON, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration = Column(Float, nullable=True)  # for videos
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    created_by = relationship("User", back_populates="media_items")
    
    def to_dict(self):
        return {
            'id': self.uid,
            'media_type': self.media_type,
            'prompt': self.prompt,
            'url': self.url,
            'thumbnail_url': self.thumbnail_url,
            'metadata': self.metadata,
            'width': self.width,
            'height': self.height,
            'duration': self.duration,
            'created_at': self.created_at.isoformat()
        }

# Simulation Session model
class SimulationSession(db.Model):
    __tablename__ = 'simulation_sessions'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(36), default=generate_uuid, unique=True, nullable=False)
    query = Column(Text, nullable=False)
    parameters = Column(JSON, nullable=False)
    result = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    active_layers = Column(JSON, nullable=True)
    processing_time = Column(Float, nullable=True)  # in seconds
    refinement_passes = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default='pending')  # pending, running, completed, failed
    error_message = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.uid,
            'query': self.query,
            'parameters': self.parameters,
            'result': self.result,
            'confidence': self.confidence,
            'active_layers': self.active_layers,
            'processing_time': self.processing_time,
            'refinement_passes': self.refinement_passes,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

# System Settings model
class SystemSetting(db.Model):
    __tablename__ = 'system_settings'
    
    id = Column(Integer, primary_key=True)
    category = Column(String(50), nullable=False)  # general, security, simulation, layout, integration
    key = Column(String(100), nullable=False)
    value = Column(Text, nullable=True)
    value_type = Column(String(20), nullable=False)  # string, number, boolean, json
    description = Column(Text, nullable=True)
    modified_by_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('category', 'key', name='uix_category_key'),)
    
    def to_dict(self):
        return {
            'category': self.category,
            'key': self.key,
            'value': self.value,
            'value_type': self.value_type,
            'description': self.description,
            'updated_at': self.updated_at.isoformat()
        }

# Knowledge Node model (UKG specific)
class KnowledgeNode(db.Model):
    __tablename__ = 'ukg_knowledge_nodes'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(36), default=generate_uuid, unique=True, nullable=False)
    node_type = Column(String(50), nullable=False)  # pillar, sector, domain, method, etc.
    axis = Column(Integer, nullable=False)  # 1-13 representing UKG axes
    code = Column(String(20), nullable=False)  # e.g., PL01, SEC02
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    attributes = Column(JSON, nullable=True)
    parent_id = Column(Integer, ForeignKey('ukg_knowledge_nodes.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    children = relationship("KnowledgeNode", backref=backref("parent", remote_side=[id]))
    source_edges = relationship("KnowledgeEdge", foreign_keys="KnowledgeEdge.source_id", back_populates="source")
    target_edges = relationship("KnowledgeEdge", foreign_keys="KnowledgeEdge.target_id", back_populates="target")
    
    def to_dict(self):
        return {
            'id': self.uid,
            'node_type': self.node_type,
            'axis': self.axis,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'attributes': self.attributes,
            'parent_id': self.parent.uid if self.parent else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

# Knowledge Edge model
class KnowledgeEdge(db.Model):
    __tablename__ = 'ukg_knowledge_edges'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(36), default=generate_uuid, unique=True, nullable=False)
    edge_type = Column(String(50), nullable=False)  # directed, association, etc.
    label = Column(String(100), nullable=True)
    weight = Column(Float, default=1.0)
    source_id = Column(Integer, ForeignKey('ukg_knowledge_nodes.id'), nullable=False)
    target_id = Column(Integer, ForeignKey('ukg_knowledge_nodes.id'), nullable=False)
    attributes = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    source = relationship("KnowledgeNode", foreign_keys=[source_id], back_populates="source_edges")
    target = relationship("KnowledgeNode", foreign_keys=[target_id], back_populates="target_edges")
    
    def to_dict(self):
        return {
            'id': self.uid,
            'edge_type': self.edge_type,
            'label': self.label,
            'weight': self.weight,
            'source_id': self.source.uid,
            'target_id': self.target.uid,
            'attributes': self.attributes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

# Layer Activation model
class LayerActivation(db.Model):
    __tablename__ = 'ukg_layer_activations'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(36), default=generate_uuid, unique=True, nullable=False)
    layer_number = Column(Integer, nullable=False)  # 1-10 representing simulation layers
    simulation_session_id = Column(Integer, ForeignKey('simulation_sessions.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    confidence_score = Column(Float, nullable=True)
    start_time = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    processing_time = Column(Float, nullable=True)  # in seconds
    results = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.uid,
            'layer_number': self.layer_number,
            'simulation_session_id': self.simulation_session_id,
            'is_active': self.is_active,
            'confidence_score': self.confidence_score,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'processing_time': self.processing_time,
            'results': self.results,
            'error_message': self.error_message
        }

# Device Authentication model (for Microsoft Enterprise security standards)
class DeviceAuthentication(db.Model):
    __tablename__ = 'device_authentications'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(36), default=generate_uuid, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    device_id = Column(String(100), nullable=False)
    device_name = Column(String(100), nullable=True)
    device_type = Column(String(50), nullable=False)  # desktop, mobile, tablet
    ip_address = Column(String(50), nullable=False)
    user_agent = Column(Text, nullable=True)
    is_trusted = Column(Boolean, default=False)
    first_seen = Column(DateTime, default=datetime.datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('user_id', 'device_id', name='uix_user_device'),)
    
    def to_dict(self):
        return {
            'id': self.uid,
            'device_id': self.device_id,
            'device_name': self.device_name,
            'device_type': self.device_type,
            'ip_address': self.ip_address,
            'is_trusted': self.is_trusted,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat()
        }

# OAuth Tokens model (for Azure AD / Microsoft Entra ID integration)
class OAuthToken(db.Model):
    __tablename__ = 'oauth_tokens'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    provider = Column(String(50), nullable=False)  # azure_ad, microsoft_graph, etc.
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    scope = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('user_id', 'provider', name='uix_user_provider'),)
    
    @property
    def is_expired(self):
        return datetime.datetime.utcnow() > self.expires_at