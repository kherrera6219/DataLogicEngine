"""
Universal Knowledge Graph (UKG) System - API Routes

This module defines the API routes for the UKG system.
"""

import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from extensions import db
from models import SimulationSession
from db_models import PillarLevel, Sector, Domain, KnowledgeNode

# Create API Blueprint
api = Blueprint('api', __name__, url_prefix='/api')

# Error response helper
def error_response(message, status_code=400):
    """Return a standardized error response."""
    return jsonify({"error": message, "success": False}), status_code

# Success response helper
def success_response(data, message="Operation successful", status_code=200):
    """Return a standardized success response."""
    response = {
        "success": True,
        "message": message,
        "data": data
    }
    return jsonify(response), status_code

# Pillar Level Routes
@api.route('/pillar-levels', methods=['GET'])
def get_pillar_levels():
    """Get all pillar levels."""
    pillar_levels = PillarLevel.query.all()
    return success_response([p.to_dict() for p in pillar_levels])

@api.route('/pillar-levels/<pillar_id>', methods=['GET'])
def get_pillar_level(pillar_id):
    """Get a specific pillar level."""
    pillar_level = PillarLevel.query.filter_by(pillar_id=pillar_id).first()
    if not pillar_level:
        return error_response(f"Pillar level with ID {pillar_id} not found", 404)
    return success_response(pillar_level.to_dict())

@api.route('/pillar-levels', methods=['POST'])
def create_pillar_level():
    """Create a new pillar level."""
    data = request.json
    
    if not data:
        return error_response("No data provided")
    
    # Validate required fields
    required_fields = ['pillar_id', 'name']
    for field in required_fields:
        if field not in data:
            return error_response(f"Missing required field: {field}")
    
    # Check if pillar level already exists
    existing = PillarLevel.query.filter_by(pillar_id=data['pillar_id']).first()
    if existing:
        return error_response(f"Pillar level with ID {data['pillar_id']} already exists", 409)
    
    # Create new pillar level
    new_pillar = PillarLevel(
        uid=str(uuid.uuid4()),
        pillar_id=data['pillar_id'],
        name=data['name'],
        description=data.get('description'),
        sublevels=data.get('sublevels')
    )
    
    db.session.add(new_pillar)
    
    try:
        db.session.commit()
        return success_response(new_pillar.to_dict(), "Pillar level created successfully", 201)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating pillar level: {str(e)}")
        return error_response(f"Error creating pillar level: {str(e)}", 500)

# Sector Routes
@api.route('/sectors', methods=['GET'])
def get_sectors():
    """Get all sectors."""
    sectors = Sector.query.all()
    return success_response([s.to_dict() for s in sectors])

@api.route('/sectors/<sector_code>', methods=['GET'])
def get_sector(sector_code):
    """Get a specific sector."""
    sector = Sector.query.filter_by(sector_code=sector_code).first()
    if not sector:
        return error_response(f"Sector with code {sector_code} not found", 404)
    return success_response(sector.to_dict())

@api.route('/sectors', methods=['POST'])
def create_sector():
    """Create a new sector."""
    data = request.json
    
    if not data:
        return error_response("No data provided")
    
    # Validate required fields
    required_fields = ['sector_code', 'name']
    for field in required_fields:
        if field not in data:
            return error_response(f"Missing required field: {field}")
    
    # Check if sector already exists
    existing = Sector.query.filter_by(sector_code=data['sector_code']).first()
    if existing:
        return error_response(f"Sector with code {data['sector_code']} already exists", 409)
    
    # Create new sector
    new_sector = Sector(
        uid=str(uuid.uuid4()),
        sector_code=data['sector_code'],
        name=data['name'],
        description=data.get('description'),
        parent_sector_id=data.get('parent_sector_id')
    )
    
    db.session.add(new_sector)
    
    try:
        db.session.commit()
        return success_response(new_sector.to_dict(), "Sector created successfully", 201)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating sector: {str(e)}")
        return error_response(f"Error creating sector: {str(e)}", 500)

# Domain Routes
@api.route('/domains', methods=['GET'])
def get_domains():
    """Get all domains."""
    domains = Domain.query.all()
    return success_response([d.to_dict() for d in domains])

@api.route('/domains/<domain_code>', methods=['GET'])
def get_domain(domain_code):
    """Get a specific domain."""
    domain = Domain.query.filter_by(domain_code=domain_code).first()
    if not domain:
        return error_response(f"Domain with code {domain_code} not found", 404)
    return success_response(domain.to_dict())

@api.route('/domains', methods=['POST'])
def create_domain():
    """Create a new domain."""
    data = request.json
    
    if not data:
        return error_response("No data provided")
    
    # Validate required fields
    required_fields = ['domain_code', 'name']
    for field in required_fields:
        if field not in data:
            return error_response(f"Missing required field: {field}")
    
    # Check if domain already exists
    existing = Domain.query.filter_by(domain_code=data['domain_code']).first()
    if existing:
        return error_response(f"Domain with code {data['domain_code']} already exists", 409)
    
    # Create new domain
    new_domain = Domain(
        uid=str(uuid.uuid4()),
        domain_code=data['domain_code'],
        name=data['name'],
        description=data.get('description'),
        sector_id=data.get('sector_id'),
        parent_domain_id=data.get('parent_domain_id')
    )
    
    db.session.add(new_domain)
    
    try:
        db.session.commit()
        return success_response(new_domain.to_dict(), "Domain created successfully", 201)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating domain: {str(e)}")
        return error_response(f"Error creating domain: {str(e)}", 500)

# Knowledge Node Routes
@api.route('/knowledge-nodes', methods=['GET'])
def get_knowledge_nodes():
    """Get all knowledge nodes."""
    knowledge_nodes = KnowledgeNode.query.all()
    return success_response([n.to_dict() for n in knowledge_nodes])

@api.route('/knowledge-nodes/<uid>', methods=['GET'])
def get_knowledge_node(uid):
    """Get a specific knowledge node."""
    node = KnowledgeNode.query.filter_by(uid=uid).first()
    if not node:
        return error_response(f"Knowledge node with UID {uid} not found", 404)
    return success_response(node.to_dict())

@api.route('/knowledge-nodes', methods=['POST'])
def create_knowledge_node():
    """Create a new knowledge node."""
    data = request.json
    
    if not data:
        return error_response("No data provided")
    
    # Validate required fields
    required_fields = ['title', 'content', 'content_type']
    for field in required_fields:
        if field not in data:
            return error_response(f"Missing required field: {field}")
    
    # Create new knowledge node
    new_node = KnowledgeNode(
        uid=str(uuid.uuid4()),
        title=data['title'],
        content=data['content'],
        content_type=data['content_type'],
        pillar_level_id=data.get('pillar_level_id'),
        domain_id=data.get('domain_id'),
        location_id=data.get('location_id'),
        metadata=data.get('metadata')
    )
    
    db.session.add(new_node)
    
    try:
        db.session.commit()
        return success_response(new_node.to_dict(), "Knowledge node created successfully", 201)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating knowledge node: {str(e)}")
        return error_response(f"Error creating knowledge node: {str(e)}", 500)

# Simulation Routes
@api.route('/simulations', methods=['GET'])
def get_simulations():
    """Get all simulation sessions."""
    simulations = SimulationSession.query.all()
    return success_response([s.to_dict() for s in simulations])

@api.route('/simulations/<uid>', methods=['GET'])
def get_simulation(uid):
    """Get a specific simulation session."""
    simulation = SimulationSession.query.filter_by(uid=uid).first()
    if not simulation:
        return error_response(f"Simulation with UID {uid} not found", 404)
    return success_response(simulation.to_dict())

@api.route('/simulations', methods=['POST'])
def create_simulation():
    """Create a new simulation session."""
    data = request.json
    
    if not data:
        return error_response("No data provided")
    
    # Validate required fields
    required_fields = ['parameters']
    for field in required_fields:
        if field not in data:
            return error_response(f"Missing required field: {field}")
    
    # Create new simulation session
    new_simulation = SimulationSession(
        uid=str(uuid.uuid4()),
        name=data.get('name'),
        parameters=data['parameters'],
        status="active",
        current_step=0,
        results={}
    )
    
    db.session.add(new_simulation)
    
    try:
        db.session.commit()
        return success_response(new_simulation.to_dict(), "Simulation created successfully", 201)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating simulation: {str(e)}")
        return error_response(f"Error creating simulation: {str(e)}", 500)

@api.route('/simulations/<uid>/step', methods=['POST'])
def run_simulation_step(uid):
    """Run a step for a simulation session."""
    simulation = SimulationSession.query.filter_by(uid=uid).first()
    if not simulation:
        return error_response(f"Simulation with UID {uid} not found", 404)
    
    if simulation.status != "active":
        return error_response(f"Simulation is not active (current status: {simulation.status})")
    
    # Run simulation step (placeholder)
    # In a real implementation, this would execute the simulation logic
    simulation.current_step += 1
    simulation.last_step_at = datetime.utcnow()
    
    # Update simulation results
    results = simulation.results or {}
    results[str(simulation.current_step)] = {
        "timestamp": datetime.utcnow().isoformat(),
        "step": simulation.current_step,
        "data": {"message": "Simulation step executed successfully"}
    }
    simulation.results = results
    
    try:
        db.session.commit()
        return success_response(simulation.to_dict(), "Simulation step executed successfully")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error running simulation step: {str(e)}")
        return error_response(f"Error running simulation step: {str(e)}", 500)

@api.route('/simulations/<uid>/stop', methods=['POST'])
def stop_simulation(uid):
    """Stop a simulation session."""
    simulation = SimulationSession.query.filter_by(uid=uid).first()
    if not simulation:
        return error_response(f"Simulation with UID {uid} not found", 404)
    
    if simulation.status != "active":
        return error_response(f"Simulation is not active (current status: {simulation.status})")
    
    # Stop simulation
    simulation.status = "completed"
    simulation.completed_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return success_response(simulation.to_dict(), "Simulation stopped successfully")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error stopping simulation: {str(e)}")
        return error_response(f"Error stopping simulation: {str(e)}", 500)

# Seed Data Routes
@api.route('/seed/pillar-levels', methods=['POST'])
def seed_pillar_levels():
    """Seed initial pillar level data."""
    pillar_levels = [
        {
            "pillar_id": "PL01",
            "name": "Data",
            "description": "Raw information and facts without context"
        },
        {
            "pillar_id": "PL02",
            "name": "Information",
            "description": "Data with context and meaning"
        },
        {
            "pillar_id": "PL03",
            "name": "Knowledge",
            "description": "Applied information with understanding"
        },
        {
            "pillar_id": "PL04",
            "name": "Wisdom",
            "description": "Knowledge with insights and judgment"
        },
        {
            "pillar_id": "PL05",
            "name": "Intelligence",
            "description": "Adaptive application of knowledge"
        }
    ]
    
    created = 0
    for pl_data in pillar_levels:
        existing = PillarLevel.query.filter_by(pillar_id=pl_data['pillar_id']).first()
        if not existing:
            new_pl = PillarLevel(
                uid=str(uuid.uuid4()),
                pillar_id=pl_data['pillar_id'],
                name=pl_data['name'],
                description=pl_data['description']
            )
            db.session.add(new_pl)
            created += 1
    
    try:
        db.session.commit()
        return success_response({"created": created}, f"{created} pillar levels seeded successfully")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error seeding pillar levels: {str(e)}")
        return error_response(f"Error seeding pillar levels: {str(e)}", 500)

@api.route('/seed/sectors', methods=['POST'])
def seed_sectors():
    """Seed initial sector data."""
    sectors = [
        {
            "sector_code": "GOV",
            "name": "Government",
            "description": "Public sector institutions and agencies"
        },
        {
            "sector_code": "TECH",
            "name": "Technology",
            "description": "Information technology and software"
        },
        {
            "sector_code": "FIN",
            "name": "Finance",
            "description": "Banking, investments, and financial services"
        },
        {
            "sector_code": "EDU",
            "name": "Education",
            "description": "Educational institutions and services"
        },
        {
            "sector_code": "HEAL",
            "name": "Healthcare",
            "description": "Medical services and healthcare institutions"
        }
    ]
    
    created = 0
    for sector_data in sectors:
        existing = Sector.query.filter_by(sector_code=sector_data['sector_code']).first()
        if not existing:
            new_sector = Sector(
                uid=str(uuid.uuid4()),
                sector_code=sector_data['sector_code'],
                name=sector_data['name'],
                description=sector_data['description']
            )
            db.session.add(new_sector)
            created += 1
    
    try:
        db.session.commit()
        return success_response({"created": created}, f"{created} sectors seeded successfully")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error seeding sectors: {str(e)}")
        return error_response(f"Error seeding sectors: {str(e)}", 500)

@api.route('/seed/domains', methods=['POST'])
def seed_domains():
    """Seed initial domain data."""
    domains = [
        {
            "domain_code": "FEDGOV",
            "name": "Federal Government",
            "description": "Federal government agencies and institutions",
            "sector_code": "GOV"
        },
        {
            "domain_code": "STGOV",
            "name": "State Government",
            "description": "State government agencies and institutions",
            "sector_code": "GOV"
        },
        {
            "domain_code": "CSEC",
            "name": "Cybersecurity",
            "description": "Information security and cybersecurity",
            "sector_code": "TECH"
        },
        {
            "domain_code": "AI",
            "name": "Artificial Intelligence",
            "description": "Artificial intelligence and machine learning",
            "sector_code": "TECH"
        },
        {
            "domain_code": "BANK",
            "name": "Banking",
            "description": "Banking services and institutions",
            "sector_code": "FIN"
        }
    ]
    
    created = 0
    for domain_data in domains:
        existing = Domain.query.filter_by(domain_code=domain_data['domain_code']).first()
        if not existing:
            # Get sector ID
            sector = Sector.query.filter_by(sector_code=domain_data['sector_code']).first()
            sector_id = sector.id if sector else None
            
            new_domain = Domain(
                uid=str(uuid.uuid4()),
                domain_code=domain_data['domain_code'],
                name=domain_data['name'],
                description=domain_data['description'],
                sector_id=sector_id
            )
            db.session.add(new_domain)
            created += 1
    
    try:
        db.session.commit()
        return success_response({"created": created}, f"{created} domains seeded successfully")
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error seeding domains: {str(e)}")
        return error_response(f"Error seeding domains: {str(e)}", 500)

# Error Logging Route
@api.route('/log-error', methods=['POST'])
def log_frontend_error():
    """
    Log frontend errors for monitoring and debugging.
    Accepts error data from the frontend error tracking service.
    """
    try:
        error_data = request.json

        if not error_data:
            return error_response("No error data provided")

        # Extract error information
        error_info = {
            'timestamp': error_data.get('timestamp', datetime.utcnow().isoformat()),
            'type': error_data.get('type', 'unknown'),
            'message': error_data.get('message', 'No message'),
            'stack': error_data.get('stack'),
            'url': error_data.get('url'),
            'user_agent': error_data.get('userAgent'),
            'severity': error_data.get('severity', 'error'),
            'source': error_data.get('source', 'frontend'),
            'boundary_name': error_data.get('boundaryName'),
            'boundary_type': error_data.get('boundaryType'),
            'page': error_data.get('page'),
            'context': error_data.get('context', {})
        }

        # Log to application logger with appropriate level
        severity = error_info['severity']
        log_message = f"Frontend Error - {error_info['type']}: {error_info['message']} | URL: {error_info['url']}"

        if severity == 'critical':
            current_app.logger.critical(log_message, extra=error_info)
        elif severity == 'error':
            current_app.logger.error(log_message, extra=error_info)
        elif severity == 'warning':
            current_app.logger.warning(log_message, extra=error_info)
        else:
            current_app.logger.info(log_message, extra=error_info)

        # In production, you would also send to external monitoring service
        # Example: send_to_sentry(error_info), send_to_datadog(error_info)

        return success_response(
            {"logged": True, "timestamp": error_info['timestamp']},
            "Error logged successfully"
        )

    except Exception as e:
        current_app.logger.error(f"Error logging frontend error: {str(e)}")
        # Don't return error response to avoid error loops
        return jsonify({"success": True, "logged": False}), 200

# Register the blueprint
def register_api(app):
    """Register the API blueprint with the Flask application."""
    app.register_blueprint(api)