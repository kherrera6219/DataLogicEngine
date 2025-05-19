"""
Universal Knowledge Graph (UKG) System - Core Models

This module defines the core data models for the UKG system
to work with the PostgreSQL database.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app import db

# Base Models for UKG Core Components

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
    knowledge_nodes = relationship("KnowledgeNode", back_populates="pillar_level")
    
    def to_dict(self):
        """Convert pillar level to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'pillar_id': self.pillar_id,
            'name': self.name,
            'description': self.description,
            'sublevels': self.sublevels,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

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
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

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
            'parent_domain_id': self.parent_domain_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

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
    knowledge_nodes = relationship("KnowledgeNode", back_populates="location")
    
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
            'attributes': self.attributes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

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
    meta_info = Column(JSON, nullable=True)  # Renamed from 'metadata' to avoid reserved name conflict
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pillar_level = relationship("PillarLevel", back_populates="knowledge_nodes")
    location = relationship("Location", back_populates="knowledge_nodes")
    
    def to_dict(self):
        """Convert knowledge node to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'title': self.title,
            'content': self.content,
            'content_type': self.content_type,
            'pillar_level_id': self.pillar_level_id,
            'domain_id': self.domain_id,
            'location_id': self.location_id,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
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