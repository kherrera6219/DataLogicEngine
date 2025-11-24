"""
Universal Knowledge Graph (UKG) System - API

This module provides API functionality for the UKG system,
including endpoints for knowledge graph management, simulation,
and the 13-axis system interactions.
"""

import uuid
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from backend.middleware import api_response
from extensions import db
from models import User, SimulationSession
from db_models import *

# Set up logging
logger = logging.getLogger(__name__)

# Create Blueprint for UKG API
ukg_api = Blueprint('ukg_api', __name__, url_prefix='/api')

# -------------------------------------------------------------------------
# Axis 1: Knowledge - Pillar Levels
# -------------------------------------------------------------------------

@ukg_api.route('/pillars', methods=['GET'])
@api_response
def get_pillars():
    """Get all pillar levels."""
    pillars = PillarLevel.query.all()
    return [pillar.to_dict() for pillar in pillars]

@ukg_api.route('/pillars/<pillar_id>', methods=['GET'])
@api_response
def get_pillar(pillar_id):
    """Get a specific pillar level."""
    pillar = PillarLevel.query.filter_by(pillar_id=pillar_id).first_or_404()
    return pillar.to_dict()

@ukg_api.route('/pillars', methods=['POST'])
@api_response
def create_pillar():
    """Create a new pillar level."""
    data = request.json
    
    pillar = PillarLevel(
        uid=str(uuid.uuid4()),
        pillar_id=data['pillar_id'],
        name=data['name'],
        description=data.get('description'),
        sublevels=data.get('sublevels')
    )
    
    db.session.add(pillar)
    db.session.commit()
    
    return pillar.to_dict(), 201

# -------------------------------------------------------------------------
# Axis 2: Sectors
# -------------------------------------------------------------------------

@ukg_api.route('/sectors', methods=['GET'])
@api_response
def get_sectors():
    """Get all sectors."""
    sectors = Sector.query.all()
    return [sector.to_dict() for sector in sectors]

@ukg_api.route('/sectors/<sector_id>', methods=['GET'])
@api_response
def get_sector(sector_id):
    """Get a specific sector."""
    sector = Sector.query.filter_by(id=sector_id).first_or_404()
    return sector.to_dict()

@ukg_api.route('/sectors', methods=['POST'])
@api_response
def create_sector():
    """Create a new sector."""
    data = request.json
    
    sector = Sector(
        uid=str(uuid.uuid4()),
        sector_code=data['sector_code'],
        name=data['name'],
        description=data.get('description'),
        parent_sector_id=data.get('parent_sector_id')
    )
    
    db.session.add(sector)
    db.session.commit()
    
    return sector.to_dict(), 201

# -------------------------------------------------------------------------
# Axis 3: Domains
# -------------------------------------------------------------------------

@ukg_api.route('/domains', methods=['GET'])
@api_response
def get_domains():
    """Get all domains."""
    domains = Domain.query.all()
    return [domain.to_dict() for domain in domains]

@ukg_api.route('/domains/<domain_id>', methods=['GET'])
@api_response
def get_domain(domain_id):
    """Get a specific domain."""
    domain = Domain.query.filter_by(id=domain_id).first_or_404()
    return domain.to_dict()

@ukg_api.route('/domains', methods=['POST'])
@api_response
def create_domain():
    """Create a new domain."""
    data = request.json
    
    domain = Domain(
        uid=str(uuid.uuid4()),
        domain_code=data['domain_code'],
        name=data['name'],
        description=data.get('description'),
        sector_id=data.get('sector_id'),
        parent_domain_id=data.get('parent_domain_id')
    )
    
    db.session.add(domain)
    db.session.commit()
    
    return domain.to_dict(), 201

# -------------------------------------------------------------------------
# Knowledge Nodes
# -------------------------------------------------------------------------

@ukg_api.route('/knowledge', methods=['GET'])
@api_response
def get_knowledge_nodes():
    """Get all knowledge nodes."""
    nodes = KnowledgeNode.query.all()
    return [node.to_dict() for node in nodes]

@ukg_api.route('/knowledge/<node_id>', methods=['GET'])
@api_response
def get_knowledge_node(node_id):
    """Get a specific knowledge node."""
    node = KnowledgeNode.query.filter_by(id=node_id).first_or_404()
    return node.to_dict()

@ukg_api.route('/knowledge', methods=['POST'])
@api_response
def create_knowledge_node():
    """Create a new knowledge node."""
    data = request.json
    
    node = KnowledgeNode(
        uid=str(uuid.uuid4()),
        title=data['title'],
        content=data['content'],
        content_type=data['content_type'],
        pillar_level_id=data.get('pillar_level_id'),
        domain_id=data.get('domain_id'),
        location_id=data.get('location_id'),
        metadata=data.get('metadata')
    )
    
    db.session.add(node)
    db.session.commit()
    
    return node.to_dict(), 201

# -------------------------------------------------------------------------
# Knowledge Graph - Base Nodes and Edges
# -------------------------------------------------------------------------

@ukg_api.route('/nodes', methods=['GET'])
@api_response
def get_nodes():
    """Get all nodes."""
    nodes = Node.query.all()
    return [node.to_dict() for node in nodes]

@ukg_api.route('/nodes/<node_id>', methods=['GET'])
@api_response
def get_node(node_id):
    """Get a specific node."""
    node = Node.query.filter_by(id=node_id).first_or_404()
    return node.to_dict()

@ukg_api.route('/nodes', methods=['POST'])
@api_response
def create_node():
    """Create a new node."""
    data = request.json
    
    node = Node(
        uid=str(uuid.uuid4()),
        node_type=data['node_type'],
        label=data['label'],
        axis_number=data['axis_number'],
        description=data.get('description'),
        attributes=data.get('attributes')
    )
    
    db.session.add(node)
    db.session.commit()
    
    return node.to_dict(), 201

@ukg_api.route('/edges', methods=['GET'])
@api_response
def get_edges():
    """Get all edges."""
    edges = Edge.query.all()
    return [edge.to_dict() for edge in edges]

@ukg_api.route('/edges/<edge_id>', methods=['GET'])
@api_response
def get_edge(edge_id):
    """Get a specific edge."""
    edge = Edge.query.filter_by(id=edge_id).first_or_404()
    return edge.to_dict()

@ukg_api.route('/edges', methods=['POST'])
@api_response
def create_edge():
    """Create a new edge."""
    data = request.json
    
    edge = Edge(
        uid=str(uuid.uuid4()),
        edge_type=data['edge_type'],
        weight=data.get('weight', 1.0),
        source_node_id=data['source_node_id'],
        target_node_id=data['target_node_id'],
        attributes=data.get('attributes')
    )
    
    db.session.add(edge)
    db.session.commit()
    
    return edge.to_dict(), 201

# -------------------------------------------------------------------------
# Simulation
# -------------------------------------------------------------------------

@ukg_api.route('/simulations', methods=['GET'])
@api_response
def get_simulations():
    """Get all simulation sessions."""
    sessions = SimulationSession.query.all()
    return [session.to_dict() for session in sessions]

@ukg_api.route('/simulations/<session_id>', methods=['GET'])
@api_response
def get_simulation(session_id):
    """Get a specific simulation session."""
    session = SimulationSession.query.filter_by(session_id=session_id).first_or_404()
    return session.to_dict()

@ukg_api.route('/simulations', methods=['POST'])
@api_response
def create_simulation():
    """Create a new simulation session."""
    data = request.json
    
    session = SimulationSession(
        uid=str(uuid.uuid4()),
        session_id=f"sim-{uuid.uuid4().hex[:8]}",
        name=data.get('name'),
        parameters=data['parameters'],
        status="active",
        current_step=0,
        results=None,
        started_at=datetime.utcnow()
    )
    
    db.session.add(session)
    db.session.commit()
    
    return session.to_dict(), 201

@ukg_api.route('/simulations/<session_id>/step', methods=['POST'])
@api_response
def run_simulation_step(session_id):
    """Run a step for a simulation session."""
    session = SimulationSession.query.filter_by(session_id=session_id).first_or_404()
    
    if session.status != "active":
        return {"error": f"Simulation is in {session.status} state"}, 400
    
    # Run simulation logic here
    # This is a placeholder for the actual simulation step logic
    
    session.current_step += 1
    session.last_step_at = datetime.utcnow()
    
    # Update results with new data
    if not session.results:
        session.results = {"steps": []}
    
    # Add current step results
    step_result = {
        "step": session.current_step,
        "timestamp": datetime.utcnow().isoformat(),
        "data": {"message": f"Step {session.current_step} completed"}
    }
    
    session.results["steps"].append(step_result)
    db.session.commit()
    
    return session.to_dict()

@ukg_api.route('/simulations/<session_id>/stop', methods=['POST'])
@api_response
def stop_simulation(session_id):
    """Stop a simulation session."""
    session = SimulationSession.query.filter_by(session_id=session_id).first_or_404()
    
    if session.status != "active":
        return {"error": f"Simulation is already in {session.status} state"}, 400
    
    session.status = "completed"
    session.completed_at = datetime.utcnow()
    db.session.commit()
    
    return session.to_dict()

# -------------------------------------------------------------------------
# Seed Data Functions (for development)
# -------------------------------------------------------------------------

@ukg_api.route('/seed/pillars', methods=['POST'])
@api_response
def seed_pillar_levels():
    """Seed initial pillar level data."""
    # Delete existing data
    PillarLevel.query.delete()
    
    # Create seed data
    pillars = [
        PillarLevel(
            uid=str(uuid.uuid4()),
            pillar_id="PL01",
            name="Data",
            description="Raw data, unprocessed information",
            sublevels={"ranges": ["1-5"]}
        ),
        PillarLevel(
            uid=str(uuid.uuid4()),
            pillar_id="PL10",
            name="Information",
            description="Organized data with structure",
            sublevels={"ranges": ["6-15"]}
        ),
        PillarLevel(
            uid=str(uuid.uuid4()),
            pillar_id="PL20",
            name="Knowledge",
            description="Information with context and meaning",
            sublevels={"ranges": ["16-25"]}
        ),
        PillarLevel(
            uid=str(uuid.uuid4()),
            pillar_id="PL30",
            name="Understanding",
            description="Knowledge with patterns and insights",
            sublevels={"ranges": ["26-35"]}
        ),
        PillarLevel(
            uid=str(uuid.uuid4()),
            pillar_id="PL40",
            name="Wisdom",
            description="Understanding with experience and judgment",
            sublevels={"ranges": ["36-45"]}
        ),
        PillarLevel(
            uid=str(uuid.uuid4()),
            pillar_id="PL50",
            name="Integration",
            description="Wisdom across multiple domains",
            sublevels={"ranges": ["46-55"]}
        ),
        PillarLevel(
            uid=str(uuid.uuid4()),
            pillar_id="PL60",
            name="Synthesis",
            description="Integration with creative combinations",
            sublevels={"ranges": ["56-65"]}
        ),
        PillarLevel(
            uid=str(uuid.uuid4()),
            pillar_id="PL70",
            name="Insight",
            description="Synthesis with novel applications",
            sublevels={"ranges": ["66-75"]}
        ),
        PillarLevel(
            uid=str(uuid.uuid4()),
            pillar_id="PL80",
            name="Innovation",
            description="Insights driving new paradigms",
            sublevels={"ranges": ["76-85"]}
        ),
        PillarLevel(
            uid=str(uuid.uuid4()),
            pillar_id="PL90",
            name="Transformation",
            description="Innovations changing knowledge systems",
            sublevels={"ranges": ["86-95"]}
        ),
        PillarLevel(
            uid=str(uuid.uuid4()),
            pillar_id="PL100",
            name="Transcendence",
            description="Transformations across all axes",
            sublevels={"ranges": ["96-100"]}
        )
    ]
    
    for pillar in pillars:
        db.session.add(pillar)
    
    db.session.commit()
    
    return {"message": f"Seeded {len(pillars)} pillar levels"}

@ukg_api.route('/seed/sectors', methods=['POST'])
@api_response
def seed_sectors():
    """Seed initial sector data."""
    # Delete existing data
    Sector.query.delete()
    
    # Create seed data
    sectors = [
        Sector(
            uid=str(uuid.uuid4()),
            sector_code="GOV",
            name="Government",
            description="Government and public administration sector"
        ),
        Sector(
            uid=str(uuid.uuid4()),
            sector_code="TECH",
            name="Technology",
            description="Information technology sector"
        ),
        Sector(
            uid=str(uuid.uuid4()),
            sector_code="HEALTH",
            name="Healthcare",
            description="Healthcare and medical sector"
        ),
        Sector(
            uid=str(uuid.uuid4()),
            sector_code="FIN",
            name="Finance",
            description="Financial services sector"
        ),
        Sector(
            uid=str(uuid.uuid4()),
            sector_code="EDU",
            name="Education",
            description="Education and research sector"
        ),
        Sector(
            uid=str(uuid.uuid4()),
            sector_code="MANUF",
            name="Manufacturing",
            description="Manufacturing and production sector"
        ),
        Sector(
            uid=str(uuid.uuid4()),
            sector_code="ENERGY",
            name="Energy",
            description="Energy and utilities sector"
        )
    ]
    
    for sector in sectors:
        db.session.add(sector)
    
    db.session.commit()
    
    return {"message": f"Seeded {len(sectors)} sectors"}

@ukg_api.route('/seed/domains', methods=['POST'])
@api_response
def seed_domains():
    """Seed initial domain data."""
    # Ensure sectors are already seeded
    sectors = Sector.query.all()
    if not sectors:
        return {"error": "Please seed sectors first"}, 400
    
    # Delete existing data
    Domain.query.delete()
    
    # Get sector mappings
    sector_map = {s.sector_code: s.id for s in sectors}
    
    # Create seed data
    domains = [
        # Government domains
        Domain(
            uid=str(uuid.uuid4()),
            domain_code="FEDGOV",
            name="Federal Government",
            description="Federal government agencies and operations",
            sector_id=sector_map.get("GOV")
        ),
        Domain(
            uid=str(uuid.uuid4()),
            domain_code="STGOV",
            name="State Government",
            description="State government agencies and operations",
            sector_id=sector_map.get("GOV")
        ),
        
        # Technology domains
        Domain(
            uid=str(uuid.uuid4()),
            domain_code="CLOUD",
            name="Cloud Computing",
            description="Cloud infrastructure and services",
            sector_id=sector_map.get("TECH")
        ),
        Domain(
            uid=str(uuid.uuid4()),
            domain_code="CSEC",
            name="Cybersecurity",
            description="Information security and cyber defense",
            sector_id=sector_map.get("TECH")
        ),
        Domain(
            uid=str(uuid.uuid4()),
            domain_code="AI",
            name="Artificial Intelligence",
            description="Machine learning and AI technologies",
            sector_id=sector_map.get("TECH")
        ),
        
        # Healthcare domains
        Domain(
            uid=str(uuid.uuid4()),
            domain_code="HPROV",
            name="Healthcare Providers",
            description="Hospitals, clinics, and medical practices",
            sector_id=sector_map.get("HEALTH")
        ),
        Domain(
            uid=str(uuid.uuid4()),
            domain_code="PHARMA",
            name="Pharmaceuticals",
            description="Pharmaceutical research and manufacturing",
            sector_id=sector_map.get("HEALTH")
        )
    ]
    
    for domain in domains:
        db.session.add(domain)
    
    db.session.commit()
    
    return {"message": f"Seeded {len(domains)} domains"}

def register_api(app):
    """Register the API blueprint with the Flask application."""
    app.register_blueprint(ukg_api)
    return app