"""
UKG Database Models

This module defines the database models for the Universal Knowledge Graph (UKG) system.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app import db

# Import app context to ensure all models are created correctly
import app

# Base models for all UKG entities

class Node(db.Model):
    """Base model for all nodes in the UKG system."""
    __tablename__ = 'nodes'
    
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
    __tablename__ = 'edges'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    source_id = Column(String(255), nullable=False)
    target_id = Column(String(255), nullable=False)
    edge_type = Column(String(100), nullable=False)
    attributes = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    active = Column(Boolean, default=True)
    
    def to_dict(self):
        """Convert edge to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'edge_type': self.edge_type,
            'attributes': self.attributes or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'active': self.active
        }


# Axis 1: Knowledge (Pillar Levels 1-100)

class PillarLevel(db.Model):
    """Model for Pillar Levels in Axis 1 (Knowledge)."""
    __tablename__ = 'pillar_levels'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    pillar_id = Column(String(10), unique=True, nullable=False)  # e.g., "PL01", "PL87"
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    sublevels = Column(JSON, nullable=True)  # JSON structure of sublevels
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sublevels_rel = relationship("PillarSublevel", back_populates="pillar")
    
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


class PillarSublevel(db.Model):
    """Model for Sublevels within Pillar Levels in Axis 1 (Knowledge)."""
    __tablename__ = 'pillar_sublevels'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    pillar_id = Column(String(10), ForeignKey('pillar_levels.pillar_id'), nullable=False)
    sublevel_id = Column(String(20), nullable=False)  # e.g., "1", "1.1", "1.1.1"
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    parent_sublevel_id = Column(String(20), nullable=True)  # Parent sublevel, if any
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pillar = relationship("PillarLevel", back_populates="sublevels_rel")
    
    def to_dict(self):
        """Convert pillar sublevel to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'pillar_id': self.pillar_id,
            'sublevel_id': self.sublevel_id,
            'name': self.name,
            'description': self.description,
            'parent_sublevel_id': self.parent_sublevel_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# Axis 2: Sector of Industry

class Sector(db.Model):
    """Model for Sectors in Axis 2 (Sector of Industry)."""
    __tablename__ = 'sectors'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    sector_code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    parent_sector_id = Column(Integer, ForeignKey('sectors.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subsectors = relationship("Sector", backref=db.backref('parent', remote_side=[id]))
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


# Axis 3: Domain (Branch)

class Domain(db.Model):
    """Model for Domains in Axis 3 (Branch)."""
    __tablename__ = 'domains'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    domain_code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    sector_id = Column(Integer, ForeignKey('sectors.id'), nullable=False)
    parent_domain_id = Column(Integer, ForeignKey('domains.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sector = relationship("Sector", back_populates="domains")
    subdomains = relationship("Domain", backref=db.backref('parent', remote_side=[id]))
    nodes = relationship("KnowledgeNode", back_populates="domain")
    
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


# Axis 4: Knowledge Node

class KnowledgeNode(db.Model):
    """Model for Knowledge Nodes in Axis 4 (Node)."""
    __tablename__ = 'knowledge_nodes'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    node_code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    domain_id = Column(Integer, ForeignKey('domains.id'), nullable=False)
    pillar_level_id = Column(String(10), ForeignKey('pillar_levels.pillar_id'), nullable=True)
    knowledge_level = Column(Integer, nullable=True)  # 1-5 scale
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    domain = relationship("Domain", back_populates="nodes")
    honeycomb_cells = relationship("HoneycombCell", back_populates="knowledge_node")
    
    def to_dict(self):
        """Convert knowledge node to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'node_code': self.node_code,
            'name': self.name,
            'description': self.description,
            'domain_id': self.domain_id,
            'pillar_level_id': self.pillar_level_id,
            'knowledge_level': self.knowledge_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# Axis 5: Honeycomb

class HoneycombCell(db.Model):
    """Model for Honeycomb Cells in Axis 5 (Honeycomb)."""
    __tablename__ = 'honeycomb_cells'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    cell_code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    knowledge_node_id = Column(Integer, ForeignKey('knowledge_nodes.id'), nullable=False)
    cell_type = Column(String(50), nullable=True)
    cell_level = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    knowledge_node = relationship("KnowledgeNode", back_populates="honeycomb_cells")
    octopus_nodes = relationship("OctopusNode", back_populates="honeycomb_cell")
    
    def to_dict(self):
        """Convert honeycomb cell to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'cell_code': self.cell_code,
            'name': self.name,
            'description': self.description,
            'knowledge_node_id': self.knowledge_node_id,
            'cell_type': self.cell_type,
            'cell_level': self.cell_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# Axis 6: Octopus Node

class OctopusNode(db.Model):
    """Model for Octopus Nodes in Axis 6 (Octopus Node)."""
    __tablename__ = 'octopus_nodes'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    node_code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    honeycomb_cell_id = Column(Integer, ForeignKey('honeycomb_cells.id'), nullable=False)
    node_type = Column(String(50), nullable=True)
    connection_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    honeycomb_cell = relationship("HoneycombCell", back_populates="octopus_nodes")
    
    def to_dict(self):
        """Convert octopus node to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'node_code': self.node_code,
            'name': self.name,
            'description': self.description,
            'honeycomb_cell_id': self.honeycomb_cell_id,
            'node_type': self.node_type,
            'connection_count': self.connection_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# Axis 7: Compliance

class ComplianceStandard(db.Model):
    """Model for Compliance Standards in Axis 7 (Compliance)."""
    __tablename__ = 'compliance_standards'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    standard_code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    standard_type = Column(String(50), nullable=False)
    issuing_authority = Column(String(255), nullable=False)
    version = Column(String(50), nullable=True)
    effective_date = Column(DateTime, nullable=True)
    expiration_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    controls = relationship("ComplianceControl", back_populates="standard")
    
    def to_dict(self):
        """Convert compliance standard to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'standard_code': self.standard_code,
            'name': self.name,
            'description': self.description,
            'standard_type': self.standard_type,
            'issuing_authority': self.issuing_authority,
            'version': self.version,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ComplianceControl(db.Model):
    """Model for Compliance Controls in Axis 7 (Compliance)."""
    __tablename__ = 'compliance_controls'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    control_id = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    standard_id = Column(Integer, ForeignKey('compliance_standards.id'), nullable=False)
    control_category = Column(String(50), nullable=False)
    implementation_level = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    standard = relationship("ComplianceStandard", back_populates="controls")
    
    def to_dict(self):
        """Convert compliance control to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'control_id': self.control_id,
            'name': self.name,
            'description': self.description,
            'standard_id': self.standard_id,
            'control_category': self.control_category,
            'implementation_level': self.implementation_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# Axis 8: Knowledge Expert Persona

class KnowledgeExpert(db.Model):
    """Model for Knowledge Experts in Axis 8 (Knowledge Expert Persona)."""
    __tablename__ = 'knowledge_experts'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    expert_code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    pillar_level_id = Column(String(10), ForeignKey('pillar_levels.pillar_id'), nullable=False)
    expertise_level = Column(Integer, nullable=True)  # 1-5 scale
    qualifications = Column(Text, nullable=True)
    experience_years = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert knowledge expert to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'expert_code': self.expert_code,
            'name': self.name,
            'description': self.description,
            'pillar_level_id': self.pillar_level_id,
            'expertise_level': self.expertise_level,
            'qualifications': self.qualifications,
            'experience_years': self.experience_years,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# Axis 9: Sector Industry Expert Persona

class SectorExpert(db.Model):
    """Model for Sector Experts in Axis 9 (Sector Industry Expert Persona)."""
    __tablename__ = 'sector_experts'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    expert_code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    sector_id = Column(Integer, ForeignKey('sectors.id'), nullable=False)
    expertise_level = Column(Integer, nullable=True)  # 1-5 scale
    industry_experience = Column(Text, nullable=True)
    experience_years = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert sector expert to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'expert_code': self.expert_code,
            'name': self.name,
            'description': self.description,
            'sector_id': self.sector_id,
            'expertise_level': self.expertise_level,
            'industry_experience': self.industry_experience,
            'experience_years': self.experience_years,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# Axis 10: Octopus Node Expert Persona

class OctopusExpert(db.Model):
    """Model for Octopus Node Experts in Axis 10 (Octopus Node Expert Persona)."""
    __tablename__ = 'octopus_experts'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    expert_code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    octopus_node_id = Column(Integer, ForeignKey('octopus_nodes.id'), nullable=False)
    expertise_level = Column(Integer, nullable=True)  # 1-5 scale
    specialization = Column(Text, nullable=True)
    experience_years = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert octopus expert to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'expert_code': self.expert_code,
            'name': self.name,
            'description': self.description,
            'octopus_node_id': self.octopus_node_id,
            'expertise_level': self.expertise_level,
            'specialization': self.specialization,
            'experience_years': self.experience_years,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# Axis 11: Spiderweb Node Expert Persona

class SpiderwebExpert(db.Model):
    """Model for Spiderweb Node Experts in Axis 11 (Spiderweb Node Expert Persona)."""
    __tablename__ = 'spiderweb_experts'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    expert_code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    network_complexity = Column(Integer, nullable=True)  # 1-5 scale
    network_size = Column(Integer, nullable=True)
    specialization = Column(Text, nullable=True)
    experience_years = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert spiderweb expert to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'expert_code': self.expert_code,
            'name': self.name,
            'description': self.description,
            'network_complexity': self.network_complexity,
            'network_size': self.network_size,
            'specialization': self.specialization,
            'experience_years': self.experience_years,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# Axis 12: Location

class Location(db.Model):
    """Model for Locations in Axis 12 (Location)."""
    __tablename__ = 'locations'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    location_code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    location_type = Column(String(50), nullable=False)  # physical, virtual, hybrid
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    address = Column(Text, nullable=True)
    country = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert location to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'location_code': self.location_code,
            'name': self.name,
            'description': self.description,
            'location_type': self.location_type,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'address': self.address,
            'country': self.country,
            'region': self.region,
            'city': self.city,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# Axis 13: Time

class TimeEntity(db.Model):
    """Model for Time Entities in Axis 13 (Time)."""
    __tablename__ = 'time_entities'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    time_code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    time_type = Column(String(50), nullable=False)  # point, period, recurring
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Integer, nullable=True)  # in seconds
    recurrence_pattern = Column(String(255), nullable=True)
    time_zone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert time entity to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'time_code': self.time_code,
            'name': self.name,
            'description': self.description,
            'time_type': self.time_type,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'recurrence_pattern': self.recurrence_pattern,
            'time_zone': self.time_zone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Additional models for connecting the various axes

class KnowledgeAlgorithm(db.Model):
    """Model for Knowledge Algorithms in the UKG system."""
    __tablename__ = 'knowledge_algorithms'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    algorithm_code = Column(String(20), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    algorithm_type = Column(String(50), nullable=False)
    version = Column(String(50), nullable=False)
    implementation = Column(Text, nullable=True)
    parameters = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert knowledge algorithm to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'algorithm_code': self.algorithm_code,
            'name': self.name,
            'description': self.description,
            'algorithm_type': self.algorithm_type,
            'version': self.version,
            'implementation': self.implementation,
            'parameters': self.parameters or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Session(db.Model):
    """Model for UKG Sessions."""
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    session_type = Column(String(50), nullable=False)
    user_id = Column(String(255), nullable=True)
    status = Column(String(50), default='active')
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    attributes = Column(JSON, nullable=True)
    final_confidence = Column(Float, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    def to_dict(self):
        """Convert session to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'session_type': self.session_type,
            'user_id': self.user_id,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'attributes': self.attributes or {},
            'final_confidence': self.final_confidence,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class MemoryEntry(db.Model):
    """Model for Structured Memory Entries."""
    __tablename__ = 'memory_entries'
    
    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    memory_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(255), nullable=True)
    importance = Column(Float, default=0.5)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    accessed_at = Column(DateTime, nullable=True)
    access_count = Column(Integer, default=0)
    
    def to_dict(self):
        """Convert memory entry to dictionary."""
        return {
            'id': self.id,
            'uid': self.uid,
            'memory_type': self.memory_type,
            'content': self.content,
            'source': self.source,
            'importance': self.importance,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'accessed_at': self.accessed_at.isoformat() if self.accessed_at else None,
            'access_count': self.access_count
        }