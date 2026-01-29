"""
Simulation Routes Blueprint

Handles CRUD and execution of Simulation Sessions.
"""

import uuid
import datetime
from datetime import UTC
import logging
from flask import Blueprint, request, jsonify, current_app
from extensions import db
from models import SimulationSession
from backend.auth.api_decorators import api_login_required, api_admin_required
from flask_login import current_user

simulation_bp = Blueprint('simulation_api', __name__, url_prefix='/api/v1')
logger = logging.getLogger(__name__)

# Initialize production engine
from backend.simulation.simulation_engine import create_simulation_engine
engine = create_simulation_engine()

def error_response(message, status_code=400):
    return jsonify({"error": message, "success": False}), status_code

def success_response(data, message="Operation successful", status_code=200):
    response = {"success": True, "message": message, "data": data}
    return jsonify(response), status_code

@simulation_bp.route('/simulations', methods=['GET'])
@api_login_required
def get_simulations():
    """Get all simulation sessions for current user."""
    simulations = SimulationSession.query.filter_by(user_id=current_user.id).order_by(SimulationSession.created_at.desc()).all()
    return success_response([s.to_dict() for s in simulations])

@simulation_bp.route('/simulations/<uid>', methods=['GET'])
@api_login_required
def get_simulation(uid):
    simulation = SimulationSession.query.filter_by(uid=uid).first()
    if not simulation: return error_response(f"Simulation {uid} not found", 404)
    # Optional: Check ownership
    # if simulation.user_id != current_user.id: return error_response("Unauthorized", 403)
    return success_response(simulation.to_dict())

@simulation_bp.route('/simulations', methods=['POST'])
@api_login_required
def create_simulation():
    data = request.json
    if not data: return error_response("No data provided")
    
    if 'parameters' not in data: return error_response("Missing parameters")
    
    new_simulation = SimulationSession(
        uid=str(uuid.uuid4()),
        name=data.get('name'),
        user_id=current_user.id,
        parameters=data['parameters'],
        status="active",
        current_step=0,
        results={}
    )
    
    db.session.add(new_simulation)
    try:
        db.session.commit()
        return success_response(new_simulation.to_dict(), "Simulation created", 201)
    except Exception as e:
        db.session.rollback()
        return error_response(str(e), 500)

@simulation_bp.route('/simulations/<uid>/step', methods=['POST'])
@api_login_required
def run_simulation_step(uid):
    simulation = SimulationSession.query.filter_by(uid=uid).first()
    if not simulation: return error_response(f"Simulation {uid} not found", 404)
    if simulation.status != "active": return error_response(f"Simulation not active: {simulation.status}")
    
    # Real Production Execution
    try:
        query = simulation.parameters.get('query', 'Standard Analysis')
        context = simulation.parameters.get('context', {})
        
        # Run one step of the production engine
        result = engine.process_query(query, context)
        
        simulation.current_step += 1
        simulation.last_step_at = datetime.datetime.now(UTC)
        
        results = simulation.results or {}
        results[str(simulation.current_step)] = result
        simulation.results = results
        
        if result.get('status') == 'completed':
            simulation.status = "completed"
            simulation.completed_at = datetime.datetime.now(UTC)
            
        db.session.commit()
        return success_response(simulation.to_dict(), "Step executed with production engine")
    except Exception as e:
        logger.error(f"Engine execution failed: {e}")
        return error_response(f"Engine failure: {str(e)}", 500)

@simulation_bp.route('/simulations/<uid>/stop', methods=['POST'])
@api_login_required
def stop_simulation(uid):
    simulation = SimulationSession.query.filter_by(uid=uid).first()
    if not simulation: return error_response(f"Simulation {uid} not found", 404)
    
    simulation.status = "completed"
    simulation.completed_at = datetime.datetime.now(UTC)
    
    db.session.commit()
    return success_response(simulation.to_dict(), "Simulation stopped")
