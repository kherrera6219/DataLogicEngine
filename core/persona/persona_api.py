"""
Universal Knowledge Graph (UKG) System - Quad Persona API

This module implements API endpoints for the Quad Persona System,
enabling interaction with the persona-based knowledge processing.
"""

import os
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from flask import Blueprint, request, jsonify, current_app
from app import db
from models import KnowledgeNode
from core.persona.persona_system import PersonaSystem
from core.persona.persona_models import Persona, Perspective, IntegratedView

logger = logging.getLogger(__name__)

# Create Blueprint for Persona API
persona_bp = Blueprint('persona', __name__, url_prefix='/api/persona')

# Initialize the Persona System
persona_system = PersonaSystem()

@persona_bp.route('/all', methods=['GET'])
def get_all_personas():
    """Get information about all personas in the system."""
    try:
        personas = persona_system.get_all_personas()
        return jsonify({
            "success": True,
            "personas": personas
        }), 200
    except Exception as e:
        logger.error(f"Error retrieving personas: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@persona_bp.route('/<persona_id>', methods=['GET'])
def get_persona(persona_id):
    """Get details for a specific persona."""
    try:
        persona = persona_system.get_persona(persona_id)
        if not persona:
            return jsonify({
                "success": False,
                "error": f"Persona '{persona_id}' not found"
            }), 404
        
        return jsonify({
            "success": True,
            "persona": persona
        }), 200
    except Exception as e:
        logger.error(f"Error retrieving persona {persona_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@persona_bp.route('/process/<node_id>', methods=['POST'])
def process_knowledge_node(node_id):
    """Process a knowledge node through all personas."""
    try:
        # Get the knowledge node
        node = db.session.query(KnowledgeNode).get(node_id)
        if not node:
            return jsonify({
                "success": False,
                "error": f"Knowledge node with ID {node_id} not found"
            }), 404
        
        # Convert to dictionary for processing
        node_dict = node.to_dict()
        
        # Process the node through the persona system
        result = persona_system.process_knowledge(node_dict)
        
        # Save the perspectives to the database
        save_perspectives(node_id, result)
        
        return jsonify({
            "success": True,
            "result": result
        }), 200
    except Exception as e:
        logger.error(f"Error processing knowledge node {node_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@persona_bp.route('/filter/<persona_id>', methods=['POST'])
def apply_persona_filter(persona_id):
    """Apply a persona-specific filter to query results."""
    try:
        # Get the query results from request
        data = request.json
        if not data:
            return jsonify({
                "success": False,
                "error": "No query results provided"
            }), 400
        
        # Apply the persona filter
        filtered_results = persona_system.apply_persona_filter(persona_id, data)
        
        return jsonify({
            "success": True,
            "filtered_results": filtered_results
        }), 200
    except Exception as e:
        logger.error(f"Error applying persona filter {persona_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@persona_bp.route('/reconcile/<node_id>', methods=['POST'])
def reconcile_perspectives(node_id):
    """Compare and reconcile different persona perspectives on a knowledge node."""
    try:
        # Get the list of personas to reconcile
        data = request.json
        if not data or "persona_ids" not in data:
            return jsonify({
                "success": False,
                "error": "No persona IDs provided"
            }), 400
        
        persona_ids = data["persona_ids"]
        
        # Reconcile the perspectives
        reconciliation = persona_system.reconcile_perspectives(node_id, persona_ids)
        
        return jsonify({
            "success": True,
            "reconciliation": reconciliation
        }), 200
    except Exception as e:
        logger.error(f"Error reconciling perspectives for node {node_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def save_perspectives(node_id: int, result: Dict[str, Any]) -> None:
    """
    Save perspectives and integrated view to the database.
    
    Parameters:
    - node_id: ID of the knowledge node
    - result: Result from persona processing
    """
    try:
        perspectives_ids = []
        
        # Save individual perspectives
        for persona_id, perspective_data in result.get("perspectives", {}).items():
            # Check if a persona record exists, create if not
            persona = db.session.query(Persona).filter_by(persona_id=persona_id).first()
            if not persona:
                persona_info = persona_system.get_persona(persona_id)
                persona = Persona(
                    uid=str(uuid.uuid4()),
                    persona_id=persona_id,
                    name=persona_info["name"],
                    description=persona_info["description"],
                    traits=persona_info.get("traits"),
                    strengths=persona_info.get("strengths"),
                    focus=persona_info.get("focus")
                )
                db.session.add(persona)
                db.session.flush()  # Get the ID without committing
            
            # Create the perspective record
            perspective = Perspective(
                uid=str(uuid.uuid4()),
                persona_id=persona.id,
                knowledge_node_id=node_id,
                key_insights=perspective_data.get("key_insights"),
                strengths_identified=perspective_data.get("strengths_identified"),
                blind_spots=perspective_data.get("blind_spots"),
                recommendations=perspective_data.get("recommendations")
            )
            db.session.add(perspective)
            db.session.flush()  # Get the ID without committing
            
            perspectives_ids.append(perspective.id)
        
        # Save the integrated view
        integrated_data = result.get("integrated_view", {})
        integrated_view = IntegratedView(
            uid=str(uuid.uuid4()),
            knowledge_node_id=node_id,
            synthesis_method=integrated_data.get("synthesis_method", "Multi-perspective integration"),
            key_insights=integrated_data.get("key_insights"),
            comprehensive_strengths=integrated_data.get("comprehensive_strengths"),
            potential_limitations=integrated_data.get("potential_limitations"),
            balanced_recommendations=integrated_data.get("balanced_recommendations"),
            perspectives=perspectives_ids
        )
        db.session.add(integrated_view)
        
        # Commit all changes
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving perspectives: {str(e)}")
        raise

def register_persona_api(app):
    """Register the persona API blueprint with the Flask app."""
    app.register_blueprint(persona_bp)
    logger.info("Registered Persona API Blueprint")