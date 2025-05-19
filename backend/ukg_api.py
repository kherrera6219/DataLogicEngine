import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
from flask import Blueprint, request, jsonify, current_app
import json

# Import core components
from core.simulation.app_orchestrator import AppOrchestrator

# Create blueprint
ukg_api = Blueprint('ukg_api', __name__)

# Initialize App Orchestrator
orchestrator = None

def get_orchestrator():
    """
    Get or initialize the App Orchestrator.
    
    Returns:
        AppOrchestrator: App Orchestrator instance
    """
    global orchestrator
    
    if orchestrator is None:
        try:
            orchestrator = AppOrchestrator()
            logging.info(f"[{datetime.now()}] API: App Orchestrator initialized")
        except Exception as e:
            logging.error(f"[{datetime.now()}] API: Error initializing App Orchestrator: {str(e)}")
    
    return orchestrator

# API Routes

@ukg_api.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Health status
    """
    try:
        orchestrator = get_orchestrator()
        
        if orchestrator:
            # Get system health from orchestrator
            health_info = orchestrator.get_system_health()
            health_info['api_status'] = 'healthy'
            return jsonify(health_info), 200
        else:
            return jsonify({
                'status': 'degraded',
                'message': 'App Orchestrator not available',
                'api_status': 'healthy',
                'timestamp': datetime.now().isoformat()
            }), 200
            
    except Exception as e:
        logging.error(f"[{datetime.now()}] API: Error in health check: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@ukg_api.route('/api/simulate', methods=['POST'])
def simulate():
    """
    Run a UKG simulation.
    
    Returns:
        dict: Simulation results
    """
    try:
        orchestrator = get_orchestrator()
        
        if not orchestrator:
            return jsonify({
                'status': 'error',
                'message': 'App Orchestrator not available',
                'timestamp': datetime.now().isoformat()
            }), 503
        
        # Get request data
        data = request.json
        
        if not data or 'query' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameter: query',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        # Extract parameters
        query_text = data.get('query')
        location_uids = data.get('location_uids')
        target_confidence = data.get('target_confidence')
        
        # Run simulation
        result = orchestrator.run_simulation(
            query_text=query_text,
            location_uids=location_uids,
            target_confidence=target_confidence
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        logging.error(f"[{datetime.now()}] API: Error in simulation: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@ukg_api.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """
    Get session information.
    
    Args:
        session_id: Session ID
        
    Returns:
        dict: Session information
    """
    try:
        orchestrator = get_orchestrator()
        
        if not orchestrator:
            return jsonify({
                'status': 'error',
                'message': 'App Orchestrator not available',
                'timestamp': datetime.now().isoformat()
            }), 503
        
        # Get session info
        session_info = orchestrator.get_session_info(session_id)
        
        return jsonify(session_info), 200
        
    except Exception as e:
        logging.error(f"[{datetime.now()}] API: Error getting session {session_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        }), 500

@ukg_api.route('/api/location/context', methods=['GET'])
def get_location_context():
    """
    Get location context.
    
    Returns:
        dict: Location context information
    """
    try:
        orchestrator = get_orchestrator()
        
        if not orchestrator:
            return jsonify({
                'status': 'error',
                'message': 'App Orchestrator not available',
                'timestamp': datetime.now().isoformat()
            }), 503
        
        # Get parameters
        location_uid = request.args.get('location_uid')
        query_text = request.args.get('query_text')
        
        # Get location context
        location_context = orchestrator.get_location_context(
            location_uid=location_uid,
            query_text=query_text
        )
        
        return jsonify(location_context), 200
        
    except Exception as e:
        logging.error(f"[{datetime.now()}] API: Error getting location context: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@ukg_api.route('/api/graph/search', methods=['GET'])
def search_graph():
    """
    Search the knowledge graph.
    
    Returns:
        dict: Search results
    """
    try:
        orchestrator = get_orchestrator()
        
        if not orchestrator:
            return jsonify({
                'status': 'error',
                'message': 'App Orchestrator not available',
                'timestamp': datetime.now().isoformat()
            }), 503
        
        # Get parameters
        query = request.args.get('q', '')
        node_types_str = request.args.get('node_types')
        axis_numbers_str = request.args.get('axis_numbers')
        limit = int(request.args.get('limit', 100))
        
        # Parse list parameters
        node_types = node_types_str.split(',') if node_types_str else None
        axis_numbers = [int(x) for x in axis_numbers_str.split(',')] if axis_numbers_str else None
        
        # Search graph
        search_results = orchestrator.search_knowledge_graph(
            query=query,
            node_types=node_types,
            axis_numbers=axis_numbers,
            limit=limit
        )
        
        return jsonify(search_results), 200
        
    except Exception as e:
        logging.error(f"[{datetime.now()}] API: Error searching graph: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@ukg_api.route('/api/improvements', methods=['GET'])
def get_improvements():
    """
    Get improvement proposals.
    
    Returns:
        dict: Improvement proposals
    """
    try:
        orchestrator = get_orchestrator()
        
        if not orchestrator:
            return jsonify({
                'status': 'error',
                'message': 'App Orchestrator not available',
                'timestamp': datetime.now().isoformat()
            }), 503
        
        # Get parameters
        status = request.args.get('status')
        proposal_type = request.args.get('type')
        limit = int(request.args.get('limit', 100))
        
        # Get proposals
        proposals = orchestrator.get_improvement_proposals(
            status=status,
            proposal_type=proposal_type,
            limit=limit
        )
        
        return jsonify(proposals), 200
        
    except Exception as e:
        logging.error(f"[{datetime.now()}] API: Error getting improvement proposals: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@ukg_api.route('/api/improvements/<proposal_id>/approve', methods=['POST'])
def approve_improvement(proposal_id):
    """
    Approve an improvement proposal.
    
    Args:
        proposal_id: Proposal ID
        
    Returns:
        dict: Result of approving the improvement
    """
    try:
        orchestrator = get_orchestrator()
        
        if not orchestrator:
            return jsonify({
                'status': 'error',
                'message': 'App Orchestrator not available',
                'timestamp': datetime.now().isoformat()
            }), 503
        
        # Approve proposal
        result = orchestrator.approve_improvement(proposal_id)
        
        return jsonify(result), 200
        
    except Exception as e:
        logging.error(f"[{datetime.now()}] API: Error approving improvement proposal {proposal_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'proposal_id': proposal_id,
            'timestamp': datetime.now().isoformat()
        }), 500

@ukg_api.route('/api/improvements/<proposal_id>/reject', methods=['POST'])
def reject_improvement(proposal_id):
    """
    Reject an improvement proposal.
    
    Args:
        proposal_id: Proposal ID
        
    Returns:
        dict: Result of rejecting the improvement
    """
    try:
        orchestrator = get_orchestrator()
        
        if not orchestrator:
            return jsonify({
                'status': 'error',
                'message': 'App Orchestrator not available',
                'timestamp': datetime.now().isoformat()
            }), 503
        
        # Get request data
        data = request.json or {}
        reason = data.get('reason')
        
        # Reject proposal
        result = orchestrator.reject_improvement(proposal_id, reason)
        
        return jsonify(result), 200
        
    except Exception as e:
        logging.error(f"[{datetime.now()}] API: Error rejecting improvement proposal {proposal_id}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'proposal_id': proposal_id,
            'timestamp': datetime.now().isoformat()
        }), 500