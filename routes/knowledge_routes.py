"""
Knowledge Routes Blueprint

Handles CRUD operations for Core Knowledge Entities:
- Pillar Levels (Axis 1)
- Sectors (Axis 2)
- Domains (Axis 3)
- Knowledge Nodes (Axis 5)
"""

import uuid
import logging
from flask import Blueprint, request, jsonify, current_app
from extensions import db
from models import PillarLevel, Sector, Domain, KnowledgeNode
from backend.auth.api_decorators import api_login_required, api_admin_required

knowledge_bp = Blueprint('knowledge_api', __name__, url_prefix='/api/v1')
logger = logging.getLogger(__name__)

# Error response helper
def error_response(message, status_code=400):
    return jsonify({"error": message, "success": False}), status_code

# Success response helper
def success_response(data, message="Operation successful", status_code=200):
    response = {
        "success": True,
        "message": message,
        "data": data
    }
    return jsonify(response), status_code

# --- PILLAR LEVELS ---

@knowledge_bp.route('/pillar-levels', methods=['GET'])
@api_login_required
def get_pillar_levels():
    """Get all pillar levels."""
    pillar_levels = PillarLevel.query.all()
    return success_response([p.to_dict() for p in pillar_levels])

@knowledge_bp.route('/pillar-levels/<pillar_id>', methods=['GET'])
@api_login_required
def get_pillar_level(pillar_id):
    """Get a specific pillar level."""
    pillar_level = PillarLevel.query.filter_by(pillar_id=pillar_id).first()
    if not pillar_level:
        return error_response(f"Pillar level with ID {pillar_id} not found", 404)
    return success_response(pillar_level.to_dict())

@knowledge_bp.route('/pillar-levels', methods=['POST'])
@api_admin_required
def create_pillar_level():
    """Create a new pillar level."""
    data = request.json
    if not data: return error_response("No data provided")
    
    required_fields = ['pillar_id', 'name']
    for field in required_fields:
        if field not in data: return error_response(f"Missing required field: {field}")
    
    existing = PillarLevel.query.filter_by(pillar_id=data['pillar_id']).first()
    if existing: return error_response(f"Pillar level with ID {data['pillar_id']} already exists", 409)
    
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
        return error_response(str(e), 500)

# --- SECTORS ---

@knowledge_bp.route('/sectors', methods=['GET'])
@api_login_required
def get_sectors():
    sectors = Sector.query.all()
    return success_response([s.to_dict() for s in sectors])

@knowledge_bp.route('/sectors/<sector_code>', methods=['GET'])
@api_login_required
def get_sector(sector_code):
    sector = Sector.query.filter_by(sector_code=sector_code).first()
    if not sector: return error_response(f"Sector with code {sector_code} not found", 404)
    return success_response(sector.to_dict())

@knowledge_bp.route('/sectors', methods=['POST'])
@api_admin_required
def create_sector():
    data = request.json
    if not data: return error_response("No data provided")
    
    required_fields = ['sector_code', 'name']
    for field in required_fields:
        if field not in data: return error_response(f"Missing required field: {field}")
    
    existing = Sector.query.filter_by(sector_code=data['sector_code']).first()
    if existing: return error_response(f"Sector with code {data['sector_code']} already exists", 409)
    
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
        return error_response(str(e), 500)

# --- DOMAINS ---

@knowledge_bp.route('/domains', methods=['GET'])
@api_login_required
def get_domains():
    domains = Domain.query.all()
    return success_response([d.to_dict() for d in domains])

@knowledge_bp.route('/domains/<domain_code>', methods=['GET'])
@api_login_required
def get_domain(domain_code):
    domain = Domain.query.filter_by(domain_code=domain_code).first()
    if not domain: return error_response(f"Domain with code {domain_code} not found", 404)
    return success_response(domain.to_dict())

@knowledge_bp.route('/domains', methods=['POST'])
@api_admin_required
def create_domain():
    data = request.json
    if not data: return error_response("No data provided")
    
    required_fields = ['domain_code', 'name']
    for field in required_fields:
        if field not in data: return error_response(f"Missing required field: {field}")
    
    existing = Domain.query.filter_by(domain_code=data['domain_code']).first()
    if existing: return error_response(f"Domain with code {data['domain_code']} already exists", 409)
    
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
        return error_response(str(e), 500)

# --- KNOWLEDGE NODES ---

@knowledge_bp.route('/knowledge-nodes', methods=['GET'])
@api_login_required
def get_knowledge_nodes():
    nodes = KnowledgeNode.query.all()
    return success_response([n.to_dict() for n in nodes])

@knowledge_bp.route('/knowledge-nodes/<uid>', methods=['GET'])
@api_login_required
def get_knowledge_node(uid):
    node = KnowledgeNode.query.filter_by(uid=uid).first()
    if not node: return error_response(f"Node {uid} not found", 404)
    return success_response(node.to_dict())

@knowledge_bp.route('/knowledge-nodes', methods=['POST'])
@api_admin_required
def create_knowledge_node():
    data = request.json
    if not data: return error_response("No data provided")
    
    required_fields = ['title', 'content', 'content_type']
    for field in required_fields:
        if field not in data: return error_response(f"Missing required field: {field}")
    
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
        return success_response(new_node.to_dict(), "Node created successfully", 201)
    except Exception as e:
        db.session.rollback()
        return error_response(str(e), 500)
