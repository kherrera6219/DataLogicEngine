
"""
Universal Knowledge Graph (UKG) System - Contextual Experts API

This module implements API endpoints for Axis 11 (Context Experts),
enabling access to the context expert personas and their expertise models.
"""

import logging
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from core.axes.axis_system import AxisSystem

logger = logging.getLogger(__name__)

# Create Blueprint for Context Experts API
contextual_bp = Blueprint('contextual', __name__, url_prefix='/api/contextual')

# Initialize axis system
axis_system = AxisSystem()

@contextual_bp.route('/experts', methods=['GET'])
def get_all_experts():
    """Get all context experts."""
    try:
        experts = axis_system.axis11.get_all_experts()
        return jsonify({
            "success": True,
            "experts": experts
        }), 200
    except Exception as e:
        logger.error(f"[{datetime.now()}] Error retrieving context experts: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@contextual_bp.route('/experts/<expert_id>', methods=['GET'])
def get_expert(expert_id):
    """Get a specific context expert by ID."""
    try:
        expert = axis_system.axis11.get_expert_by_id(expert_id)
        if not expert:
            return jsonify({
                "success": False,
                "error": f"Context expert with ID {expert_id} not found"
            }), 404
        
        return jsonify({
            "success": True,
            "expert": expert
        }), 200
    except Exception as e:
        logger.error(f"[{datetime.now()}] Error retrieving context expert {expert_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@contextual_bp.route('/expertise-model/<expert_id>', methods=['GET'])
def get_expertise_model(expert_id):
    """Get the 7-part expertise model for a specific context expert."""
    try:
        model = axis_system.axis11.get_expertise_model(expert_id)
        return jsonify({
            "success": True,
            "expertise_model": model
        }), 200
    except Exception as e:
        logger.error(f"[{datetime.now()}] Error retrieving expertise model for {expert_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@contextual_bp.route('/by-sector/<sector_id>', methods=['GET'])
def get_experts_by_sector(sector_id):
    """Get all context experts related to a specific sector."""
    try:
        experts = axis_system.axis11.get_experts_by_sector(sector_id)
        return jsonify({
            "success": True,
            "experts": experts
        }), 200
    except Exception as e:
        logger.error(f"[{datetime.now()}] Error retrieving context experts for sector {sector_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@contextual_bp.route('/branch-structure', methods=['GET'])
def get_branch_structure():
    """Get the branch structure for context experts."""
    try:
        expert_id = request.args.get('expert_id')
        structure = axis_system.axis11.get_branch_structure(expert_id)
        return jsonify({
            "success": True,
            "branch_structure": structure
        }), 200
    except Exception as e:
        logger.error(f"[{datetime.now()}] Error retrieving branch structure: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
