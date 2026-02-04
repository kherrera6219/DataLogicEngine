"""
Simulation Routes for DataLogicEngine

Provides API endpoints for managing and running simulations.
"""

import uuid
import logging
from datetime import datetime, UTC
from flask import Blueprint, request, jsonify, current_app
from backend.middleware import api_response
from models import SimulationSession, User
from extensions import db

# Set up logging
logger = logging.getLogger(__name__)

# Create Blueprint
simulation_bp = Blueprint('simulation_api', __name__)

@simulation_bp.route('/', methods=['GET'])
@api_response
def get_simulations():
    """Get all simulation sessions."""
    try:
        simulations = SimulationSession.query.all()
        return [sim.to_dict() for sim in simulations]
    except Exception as e:
        logger.error(f"Error getting simulations: {str(e)}")
        # api_response decorator handles return format, but we raise to trigger it?
        # Or return error dict. api_response usually expects raw data or tuple.
        raise e

@simulation_bp.route('/', methods=['POST'])
@api_response
def create_simulation():
    """Create a new simulation session."""
    data = request.json
    if not data:
        return {"error": "No data provided"}, 400
    
    # Validate required fields
    if 'parameters' not in data:
        return {"error": "Missing required field: parameters"}, 400
    
    try:
        # Create new simulation
        new_simulation = SimulationSession(
            uid=str(uuid.uuid4()),
            name=data.get('name', f"Simulation-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"),
            parameters=data['parameters'],
            status="pending",
            current_step=0,
            results={}
        )
        
        db.session.add(new_simulation)
        db.session.commit()
        
        # Run the simulation asynchronously if requested
        if data.get('auto_start', False):
            # This would typically be done with a task queue like Celery
            new_simulation.status = "active"
            db.session.commit()
        
        return new_simulation.to_dict(), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating simulation: {str(e)}")
        raise e

@simulation_bp.route('/<simulation_id>', methods=['GET'])
@api_response
def get_simulation(simulation_id):
    """Get details of a specific simulation."""
    simulation = SimulationSession.query.filter_by(uid=simulation_id).first()
    
    if not simulation:
        return {"error": f"Simulation with ID {simulation_id} not found"}, 404
    
    return simulation.to_dict()
