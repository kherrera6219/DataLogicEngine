from flask import Blueprint, request, jsonify, current_app
import logging
from datetime import datetime
import uuid
from .models import db, UkgNode, UkgEdge, KnowledgeAlgorithm, UkgSession
from .ukg_db import UkgDatabaseManager

# Create a Blueprint for UKG API routes
ukg_bp = Blueprint('ukg', __name__)

@ukg_bp.route('/nodes', methods=['GET'])
def get_nodes():
    """Get UKG nodes, optionally filtered by type or axis"""
    node_type = request.args.get('type')
    axis_number = request.args.get('axis')
    
    query = UkgNode.query
    
    if node_type:
        query = query.filter_by(node_type=node_type)
    
    if axis_number:
        try:
            axis_number = int(axis_number)
            query = query.filter_by(axis_number=axis_number)
        except ValueError:
            return jsonify({'error': 'Invalid axis number'}), 400
    
    nodes = query.all()
    return jsonify({
        'count': len(nodes),
        'nodes': [node.to_dict() for node in nodes]
    })

@ukg_bp.route('/nodes/<uid>', methods=['GET'])
def get_node(uid):
    """Get a specific UKG node by its UID"""
    node = UkgNode.query.filter_by(uid=uid).first()
    if not node:
        return jsonify({'error': 'Node not found'}), 404
    
    return jsonify(node.to_dict())

@ukg_bp.route('/nodes', methods=['POST'])
def create_node():
    """Create a new UKG node"""
    data = request.json
    
    if not data or not data.get('node_type') or not data.get('label'):
        return jsonify({'error': 'Node type and label are required'}), 400
    
    # Generate UID if not provided
    uid = data.get('uid', f"node-{uuid.uuid4()}")
    
    node = UkgDatabaseManager.add_node(
        uid=uid,
        node_type=data.get('node_type'),
        label=data.get('label'),
        description=data.get('description'),
        original_id=data.get('original_id'),
        axis_number=data.get('axis_number'),
        level=data.get('level'),
        attributes=data.get('attributes')
    )
    
    if not node:
        return jsonify({'error': 'Failed to create node'}), 500
    
    return jsonify(node.to_dict()), 201

@ukg_bp.route('/edges', methods=['GET'])
def get_edges():
    """Get UKG edges, optionally filtered by type"""
    edge_type = request.args.get('type')
    
    query = UkgEdge.query
    
    if edge_type:
        query = query.filter_by(edge_type=edge_type)
    
    edges = query.all()
    return jsonify({
        'count': len(edges),
        'edges': [edge.to_dict() for edge in edges]
    })

@ukg_bp.route('/edges/<uid>', methods=['GET'])
def get_edge(uid):
    """Get a specific UKG edge by its UID"""
    edge = UkgEdge.query.filter_by(uid=uid).first()
    if not edge:
        return jsonify({'error': 'Edge not found'}), 404
    
    return jsonify(edge.to_dict())

@ukg_bp.route('/edges', methods=['POST'])
def create_edge():
    """Create a new UKG edge between two nodes"""
    data = request.json
    
    if not data or not data.get('edge_type') or not data.get('source_uid') or not data.get('target_uid'):
        return jsonify({'error': 'Edge type, source UID, and target UID are required'}), 400
    
    # Generate UID if not provided
    uid = data.get('uid', f"edge-{uuid.uuid4()}")
    
    edge = UkgDatabaseManager.add_edge(
        uid=uid,
        edge_type=data.get('edge_type'),
        source_uid=data.get('source_uid'),
        target_uid=data.get('target_uid'),
        label=data.get('label'),
        weight=data.get('weight', 1.0),
        attributes=data.get('attributes')
    )
    
    if not edge:
        return jsonify({'error': 'Failed to create edge'}), 500
    
    return jsonify(edge.to_dict()), 201

@ukg_bp.route('/sessions', methods=['GET'])
def get_sessions():
    """Get UKG sessions, optionally filtered by status"""
    status = request.args.get('status')
    
    query = UkgSession.query
    
    if status:
        query = query.filter_by(status=status)
    
    sessions = query.all()
    return jsonify({
        'count': len(sessions),
        'sessions': [session.to_dict() for session in sessions]
    })

@ukg_bp.route('/sessions', methods=['POST'])
def create_session():
    """Create a new UKG session"""
    data = request.json or {}
    
    # Generate session ID if not provided
    session_id = data.get('session_id', f"session-{uuid.uuid4()}")
    
    session = UkgDatabaseManager.create_session(
        session_id=session_id,
        user_id=data.get('user_id'),
        query=data.get('query'),
        target_confidence=data.get('target_confidence', 0.85)
    )
    
    if not session:
        return jsonify({'error': 'Failed to create session'}), 500
    
    return jsonify(session.to_dict()), 201

@ukg_bp.route('/sessions/<session_id>/complete', methods=['POST'])
def complete_session(session_id):
    """Mark a UKG session as completed"""
    data = request.json or {}
    
    result = UkgDatabaseManager.complete_session(
        session_id=session_id,
        final_confidence=data.get('final_confidence')
    )
    
    if not result:
        return jsonify({'error': 'Failed to complete session'}), 404
    
    return jsonify({'success': True, 'session_id': session_id})

@ukg_bp.route('/knowledge-algorithms', methods=['GET'])
def get_knowledge_algorithms():
    """Get all registered Knowledge Algorithms"""
    algorithms = KnowledgeAlgorithm.query.all()
    return jsonify({
        'count': len(algorithms),
        'algorithms': [ka.to_dict() for ka in algorithms]
    })

@ukg_bp.route('/knowledge-algorithms', methods=['POST'])
def register_knowledge_algorithm():
    """Register a new Knowledge Algorithm"""
    data = request.json
    
    if not data or not data.get('ka_id') or not data.get('name'):
        return jsonify({'error': 'KA ID and name are required'}), 400
    
    ka = UkgDatabaseManager.register_knowledge_algorithm(
        ka_id=data.get('ka_id'),
        name=data.get('name'),
        description=data.get('description'),
        input_schema=data.get('input_schema'),
        output_schema=data.get('output_schema'),
        version=data.get('version', '1.0')
    )
    
    if not ka:
        return jsonify({'error': 'Failed to register Knowledge Algorithm'}), 500
    
    return jsonify(ka.to_dict()), 201

@ukg_bp.route('/executions', methods=['POST'])
def record_execution():
    """Record the execution of a Knowledge Algorithm"""
    data = request.json
    
    if not data or not data.get('ka_id') or not data.get('session_id') or not data.get('input_data'):
        return jsonify({'error': 'KA ID, session ID, and input data are required'}), 400
    
    execution = UkgDatabaseManager.record_ka_execution(
        ka_id=data.get('ka_id'),
        session_id=data.get('session_id'),
        input_data=data.get('input_data'),
        output_data=data.get('output_data'),
        confidence=data.get('confidence', 0.0),
        execution_time=data.get('execution_time'),
        status=data.get('status', 'completed'),
        error_message=data.get('error_message'),
        pass_num=data.get('pass_num', 0),
        layer_num=data.get('layer_num', 0)
    )
    
    if not execution:
        return jsonify({'error': 'Failed to record execution'}), 500
    
    return jsonify(execution.to_dict()), 201

@ukg_bp.route('/stats', methods=['GET'])
def get_ukg_stats():
    """Get statistics about the UKG database"""
    node_count = UkgNode.query.count()
    edge_count = UkgEdge.query.count()
    session_count = UkgSession.query.count()
    ka_count = KnowledgeAlgorithm.query.count()
    
    # Get node counts by type
    node_types = db.session.query(
        UkgNode.node_type, 
        db.func.count(UkgNode.id)
    ).group_by(UkgNode.node_type).all()
    
    # Get node counts by axis
    axis_counts = db.session.query(
        UkgNode.axis_number, 
        db.func.count(UkgNode.id)
    ).filter(UkgNode.axis_number.isnot(None)
    ).group_by(UkgNode.axis_number).all()
    
    return jsonify({
        'total_nodes': node_count,
        'total_edges': edge_count,
        'total_sessions': session_count,
        'total_knowledge_algorithms': ka_count,
        'node_types': {t[0]: t[1] for t in node_types},
        'axis_counts': {a[0]: a[1] for a in axis_counts},
        'timestamp': datetime.utcnow().isoformat()
    })