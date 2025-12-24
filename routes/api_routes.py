"""
API Routes Blueprint

Handles all API endpoints defined in routes.py (not backend blueprint APIs).
"""

import datetime
from datetime import UTC
import logging
import uuid

from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from sqlalchemy import text, select

from extensions import db
from models import SimulationSession
from db_models import Node, Edge, PillarLevel, Sector, Domain

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/health')
def api_health():
    """API health check endpoint."""
    try:
        db.session.execute(select(text('1')))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"
    
    return jsonify({
        "status": "ok" if db_status == "healthy" else "degraded",
        "version": "1.0.0",
        "timestamp": datetime.datetime.now(UTC).isoformat(),
        "components": {
            "api": "healthy",
            "database": db_status
        }
    })


@api_bp.route('/graph')
@login_required
def api_graph():
    """API endpoint to get graph data for visualization."""
    try:
        axis = request.args.get('axis', type=int)
        node_type = request.args.get('nodeType')
        limit = request.args.get('limit', 100, type=int)
        
        node_query = Node.query
        
        if axis:
            node_query = node_query.filter_by(axis_number=axis)
        
        if node_type:
            node_query = node_query.filter_by(node_type=node_type)
        
        nodes = node_query.limit(limit).all()
        
        node_data = []
        node_ids = []
        
        for node in nodes:
            node_ids.append(node.id)
            node_data.append({
                "id": node.id,
                "label": node.label,
                "axis_number": node.axis_number,
                "node_type": node.node_type,
                "description": node.description,
                "size": 8,
                "value": 1
            })
        
        edges = Edge.query.filter(
            Edge.source_node_id.in_(node_ids),
            Edge.target_node_id.in_(node_ids)
        ).all()
        
        edge_data = []
        
        for edge in edges:
            edge_data.append({
                "source": edge.source_node_id,
                "target": edge.target_node_id,
                "label": edge.edge_type,
                "value": edge.weight,
                "directed": True
            })
        
        pillars = PillarLevel.query.order_by(PillarLevel.pillar_id).all()
        sectors = Sector.query.order_by(Sector.sector_code).all()
        domains = Domain.query.order_by(Domain.domain_code).all()
        
        pillar_data = [{"id": p.id, "pillar_id": p.pillar_id, "name": p.name, "description": p.description} for p in pillars]
        sector_data = [{"id": s.id, "sector_code": s.sector_code, "name": s.name, "naics_mapping": s.naics_mapping} for s in sectors]
        domain_data = [{"id": d.id, "domain_code": d.domain_code, "name": d.name, "description": d.description} for d in domains]
        
        graph_data = {
            "nodes": node_data,
            "links": edge_data,
            "pillars": pillar_data,
            "sectors": sector_data,
            "domains": domain_data
        }
        
        return jsonify(graph_data)
    
    except Exception as e:
        logger.error(f"Error getting graph data: {str(e)}")
        return jsonify({"error": str(e)}), 500


@api_bp.route('/query', methods=['POST'])
@login_required
def api_query():
    """API endpoint to process a knowledge query."""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({"error": "Missing query parameter"}), 400
        
        query = data['query']
        confidence_threshold = data.get('confidenceThreshold', 0.85)
        max_layer = data.get('maxLayer', 5)
        
        simulation = SimulationSession()
        simulation.session_id = str(uuid.uuid4())
        simulation.user_id = current_user.id
        simulation.parameters = {
            "query": query,
            "confidenceThreshold": confidence_threshold,
            "maxLayer": max_layer
        }
        simulation.status = "completed"
        simulation.current_step = 8
        simulation.total_steps = 8
        simulation.started_at = datetime.datetime.now(UTC)
        simulation.completed_at = datetime.datetime.now(UTC)
        
        if "knowledge" in query.lower():
            response = f"The Universal Knowledge Graph organizes information across 13 axes, including knowledge domains, sectors, methods, and more. This allows for multi-perspective analysis of complex topics."
            confidence = 0.92
            active_layer = 2
        elif "simulation" in query.lower():
            response = f"Simulations in the UKG system use a 10-layer architecture with recursive processing to generate insights based on integrated knowledge across multiple domains."
            confidence = 0.89
            active_layer = 3
        elif "persona" in query.lower() or "expert" in query.lower():
            response = f"The Quad Persona Engine creates synthetic experts through 7 component structures (job role, education, certifications, skills, training, career path, related jobs). This allows the system to provide multi-perspective expertise on complex topics."
            confidence = 0.94
            active_layer = 4
        else:
            response = f"I understand your query about '{query}'. The Universal Knowledge Graph integrates multiple perspectives on this topic across knowledge domains, sectors, regulatory frameworks, and compliance requirements."
            confidence = 0.85
            active_layer = 1
        
        simulation.results = {
            "response": response,
            "confidenceScore": confidence,
            "activeLayer": active_layer
        }
        
        db.session.add(simulation)
        db.session.commit()
        
        return jsonify({
            "query": query,
            "response": response,
            "confidenceScore": confidence,
            "activeLayer": active_layer,
            "simulationId": simulation.session_id
        })
    
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return jsonify({"error": str(e)}), 500


@api_bp.route('/simulation/run', methods=['POST'])
@login_required
def api_run_simulation():
    """API endpoint to run a simulation."""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({"error": "Missing query parameter"}), 400
        
        query = data['query']
        confidence_threshold = data.get('confidenceThreshold', 0.85)
        max_layer = data.get('maxLayer', 5)
        refinement_steps = data.get('refinementSteps', 8)
        
        simulation = SimulationSession()
        simulation.session_id = str(uuid.uuid4())
        simulation.name = data.get('name', f"Simulation {datetime.datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}")
        simulation.user_id = current_user.id
        simulation.parameters = {
            "query": query,
            "confidenceThreshold": confidence_threshold,
            "maxLayer": max_layer,
            "refinementSteps": refinement_steps
        }
        simulation.status = "running"
        simulation.current_step = 0
        simulation.total_steps = refinement_steps
        simulation.started_at = datetime.datetime.now(UTC)
        
        db.session.add(simulation)
        db.session.commit()
        
        return jsonify({
            "simulationId": simulation.session_id,
            "status": "running",
            "message": "Simulation started successfully"
        })
    
    except Exception as e:
        logger.error(f"Error starting simulation: {str(e)}")
        return jsonify({"error": str(e)}), 500
