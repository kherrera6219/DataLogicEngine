from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship, backref
from extensions import db

def _utcnow():
    """Return current UTC datetime."""
    return datetime.now(UTC)

# =============================================================================
# FROM MODELS.PY (kg_ tables)
# =============================================================================

class KnowledgeGraphNode(db.Model):
    """Basic model for knowledge graph nodes (kg_nodes)"""
    __tablename__ = 'kg_nodes'
    
    id = db.Column(db.Integer, primary_key=True)
    node_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    node_type = db.Column(db.String(32), nullable=False, index=True)
    label = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text)
    data = db.Column(db.JSON)
    axis_number = db.Column(db.Integer, index=True)
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    
    def to_dict(self):
        """Convert node to dictionary"""
        return {
            'id': self.id,
            'node_id': self.node_id,
            'node_type': self.node_type,
            'label': self.label,
            'description': self.description,
            'data': self.data,
            'axis_number': self.axis_number,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class KnowledgeGraphEdge(db.Model):
    """Basic model for knowledge graph edges (kg_edges)"""
    __tablename__ = 'kg_edges'
    
    id = db.Column(db.Integer, primary_key=True)
    edge_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    source_id = db.Column(db.Integer, db.ForeignKey('kg_nodes.id'), nullable=False, index=True)
    target_id = db.Column(db.Integer, db.ForeignKey('kg_nodes.id'), nullable=False, index=True)
    edge_type = db.Column(db.String(32), nullable=False, index=True)
    weight = db.Column(db.Float, default=1.0)
    data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    
    # Define relationships
    source = db.relationship('KnowledgeGraphNode', foreign_keys=[source_id], backref='outgoing_edges')
    target = db.relationship('KnowledgeGraphNode', foreign_keys=[target_id], backref='incoming_edges')
    
    def to_dict(self):
        """Convert edge to dictionary"""
        return {
            'id': self.id,
            'edge_id': self.edge_id,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'edge_type': self.edge_type,
            'weight': self.weight,
            'data': self.data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# =============================================================================
# FROM DB_MODELS.PY (ukg_ tables)
# =============================================================================

class Node(db.Model):
    """Base model for all nodes in the UKG system (ukg_nodes)."""
    __tablename__ = 'ukg_nodes'

    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    node_type = Column(String(100), nullable=False)
    label = Column(String(255), nullable=False)
    axis_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)
    attributes = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    active = Column(Boolean, default=True)

    # Relationships
    outgoing_edges = relationship("Edge", foreign_keys="Edge.source_node_id", back_populates="source_node")
    incoming_edges = relationship("Edge", foreign_keys="Edge.target_node_id", back_populates="target_node")

    def to_dict(self):
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
    """Base model for all edges in the UKG system (ukg_edges)."""
    __tablename__ = 'ukg_edges'

    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    edge_type = Column(String(100), nullable=False)
    weight = Column(Float, default=1.0)
    source_node_id = Column(Integer, ForeignKey('ukg_nodes.id'), nullable=False)
    target_node_id = Column(Integer, ForeignKey('ukg_nodes.id'), nullable=False)
    attributes = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    active = Column(Boolean, default=True)

    # Relationships
    source_node = relationship("Node", foreign_keys=[source_node_id], back_populates="outgoing_edges")
    target_node = relationship("Node", foreign_keys=[target_node_id], back_populates="incoming_edges")

    def to_dict(self):
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

class PillarLevel(db.Model):
    """Model for Pillar Levels (Axis 1: Knowledge)."""
    __tablename__ = 'ukg_pillar_levels'

    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    pillar_id = Column(String(10), unique=True, nullable=False)  # e.g., "PL01", "PL48"
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    sublevels = Column(JSON, nullable=True)  # Nested structure for sublevels
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Relationships
    nodes = relationship("KnowledgeNode", back_populates="pillar_level")

    def to_dict(self):
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

class Sector(db.Model):
    """Model for Sectors (Axis 2: Sectors)."""
    __tablename__ = 'ukg_sectors'

    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    sector_code = Column(String(20), unique=True, nullable=False)  # e.g., "GOV", "TECH"
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    parent_sector_id = Column(Integer, ForeignKey('ukg_sectors.id'), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Relationships
    parent_sector = relationship("Sector", remote_side=[id], back_populates="subsectors")
    subsectors = relationship("Sector", foreign_keys=[parent_sector_id], back_populates="parent_sector")
    domains = relationship("Domain", back_populates="sector")

    def to_dict(self):
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
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Relationships
    sector = relationship("Sector", back_populates="domains")
    parent_domain = relationship("Domain", remote_side=[id], back_populates="subdomains")
    subdomains = relationship("Domain", foreign_keys=[parent_domain_id], back_populates="parent_domain")

    def to_dict(self):
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
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Relationships
    parent_location = relationship("Location", remote_side=[id], back_populates="sub_locations")
    sub_locations = relationship("Location", foreign_keys=[parent_location_id], back_populates="parent_location")

    def to_dict(self):
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

class TimeContext(db.Model):
    """Model for Time Contexts (Axis 13: Time)."""
    __tablename__ = 'ukg_time_contexts'

    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    time_type = Column(String(50), nullable=False)  # e.g., "historical", "project", "career_stage"
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)  # Null for ongoing or indefinite periods
    granularity = Column(String(20), nullable=False, default="day")  # e.g., "year", "month", "day"
    recurring = Column(Boolean, default=False)
    parent_time_id = Column(Integer, ForeignKey('ukg_time_contexts.id'), nullable=True)
    attributes = Column(JSON, nullable=True)  # Store additional metadata (e.g., persona_id for career stages)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Relationships
    parent_time = relationship("TimeContext", remote_side=[id], back_populates="sub_times")
    sub_times = relationship("TimeContext", foreign_keys=[parent_time_id], back_populates="parent_time")

    def to_dict(self):
        return {
            'id': self.id,
            'uid': self.uid,
            'name': self.name,
            'time_type': self.time_type,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'granularity': self.granularity,
            'recurring': self.recurring,
            'parent_time_id': self.parent_time_id,
            'attributes': self.attributes or {},
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
    node_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Relationships
    pillar_level = relationship("PillarLevel", back_populates="nodes")

    def to_dict(self):
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
            'metadata': self.node_metadata or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class MethodNode(db.Model):
    """Model for Method Nodes (Axis 4)."""
    __tablename__ = 'ukg_method_nodes'

    id = Column(Integer, primary_key=True)
    uid = Column(String(255), unique=True, nullable=False)
    node_id = Column(String(50), unique=True, nullable=False)
    node_type = Column(String(20), nullable=False)  # mega, large, medium, small, granular
    label = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey('ukg_method_nodes.id'), nullable=True)
    attributes = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Self-referential relationship for hierarchy
    children = relationship("MethodNode", backref=backref("parent", remote_side=[id]))

    def to_dict(self):
        return {
            'id': self.id,
            'uid': self.uid,
            'node_id': self.node_id,
            'node_type': self.node_type,
            'label': self.label,
            'description': self.description,
            'parent_id': self.parent_id,
            'attributes': self.attributes or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

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
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    # Relationships
    executions = relationship("KAExecution", back_populates="algorithm")

    def to_dict(self):
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
