from flask import Blueprint, request, jsonify
import logging
from datetime import datetime
import traceback

from backend.ukg_db import UkgDatabaseManager

# Create a Blueprint for the UKG API
ukg_api = Blueprint('ukg_api', __name__, url_prefix='/api/ukg')

# Initialize database manager
db_manager = UkgDatabaseManager()

# API Routes

@ukg_api.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        "status": "ok",
        "message": "UKG API is operational",
        "timestamp": datetime.utcnow().isoformat()
    })

# Node Management Endpoints
@ukg_api.route('/nodes', methods=['POST'])
def create_node():
    """Create a new node in the UKG."""
    try:
        data = request.json
        
        # Required fields
        node_type = data.get('node_type', 'GenericNode')
        label = data.get('label', '')
        
        # Optional fields
        uid = data.get('uid')
        description = data.get('description')
        original_id = data.get('original_id')
        axis_number = data.get('axis_number')
        level = data.get('level')
        attributes = data.get('attributes')
        
        # Create the node
        result = db_manager.add_node(
            uid=uid,
            node_type=node_type,
            label=label,
            description=description,
            original_id=original_id,
            axis_number=axis_number,
            level=level,
            attributes=attributes
        )
        
        return jsonify({
            "success": True,
            "message": "Node created successfully",
            "node": result
        }), 201
        
    except Exception as e:
        logging.error(f"[{datetime.now()}] Error creating node: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Error creating node: {str(e)}"
        }), 500

@ukg_api.route('/nodes/<uid>', methods=['GET'])
def get_node(uid):
    """Get a node by its UID."""
    try:
        node = db_manager.get_node(uid)
        
        if not node:
            return jsonify({
                "success": False,
                "message": f"Node with UID {uid} not found"
            }), 404
            
        return jsonify({
            "success": True,
            "node": node
        })
        
    except Exception as e:
        logging.error(f"[{datetime.now()}] Error retrieving node {uid}: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Error retrieving node: {str(e)}"
        }), 500

@ukg_api.route('/nodes/<uid>', methods=['PUT'])
def update_node(uid):
    """Update a node's attributes."""
    try:
        data = request.json
        result = db_manager.update_node(uid, **data)
        
        if not result:
            return jsonify({
                "success": False,
                "message": f"Node with UID {uid} not found"
            }), 404
            
        return jsonify({
            "success": True,
            "message": "Node updated successfully",
            "node": result
        })
        
    except Exception as e:
        logging.error(f"[{datetime.now()}] Error updating node {uid}: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Error updating node: {str(e)}"
        }), 500

@ukg_api.route('/nodes/<uid>', methods=['DELETE'])
def delete_node(uid):
    """Delete a node and its connected edges."""
    try:
        result = db_manager.delete_node(uid)
        
        if not result:
            return jsonify({
                "success": False,
                "message": f"Node with UID {uid} not found"
            }), 404
            
        return jsonify({
            "success": True,
            "message": "Node and connected edges deleted successfully"
        })
        
    except Exception as e:
        logging.error(f"[{datetime.now()}] Error deleting node {uid}: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Error deleting node: {str(e)}"
        }), 500

@ukg_api.route('/nodes', methods=['GET'])
def get_nodes():
    """Get nodes filtered by type or axis number."""
    try:
        node_type = request.args.get('type')
        axis_number = request.args.get('axis')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        if axis_number:
            # Get nodes by axis number
            axis_number = int(axis_number)
            nodes = db_manager.get_nodes_by_axis(axis_number, limit, offset)
            return jsonify({
                "success": True,
                "nodes": nodes,
                "count": len(nodes),
                "filters": {"axis_number": axis_number}
            })
            
        elif node_type:
            # Get nodes by type
            nodes = db_manager.get_nodes_by_type(node_type, limit, offset)
            return jsonify({
                "success": True,
                "nodes": nodes,
                "count": len(nodes),
                "filters": {"node_type": node_type}
            })
            
        else:
            return jsonify({
                "success": False,
                "message": "Please specify either 'type' or 'axis' as a filter"
            }), 400
            
    except Exception as e:
        logging.error(f"[{datetime.now()}] Error retrieving nodes: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Error retrieving nodes: {str(e)}"
        }), 500

@ukg_api.route('/nodes/original-id/<original_id>', methods=['GET'])
def get_node_by_original_id(original_id):
    """Get a node by its original ID."""
    try:
        node_type = request.args.get('type')
        node = db_manager.get_node_by_original_id(original_id, node_type)
        
        if not node:
            return jsonify({
                "success": False,
                "message": f"Node with original ID {original_id} not found"
            }), 404
            
        return jsonify({
            "success": True,
            "node": node
        })
        
    except Exception as e:
        logging.error(f"[{datetime.now()}] Error retrieving node by original ID {original_id}: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Error retrieving node: {str(e)}"
        }), 500

# Edge Management Endpoints
@ukg_api.route('/edges', methods=['POST'])
def create_edge():
    """Create a new edge between nodes."""
    try:
        data = request.json
        
        # Required fields
        source_uid = data.get('source_uid')
        target_uid = data.get('target_uid')
        
        if not source_uid or not target_uid:
            return jsonify({
                "success": False,
                "message": "Both source_uid and target_uid are required"
            }), 400
        
        # Optional fields
        uid = data.get('uid')
        edge_type = data.get('edge_type', 'GenericRelation')
        label = data.get('label')
        weight = float(data.get('weight', 1.0))
        attributes = data.get('attributes')
        
        # Create the edge
        result = db_manager.add_edge(
            source_uid=source_uid,
            target_uid=target_uid,
            edge_type=edge_type,
            label=label,
            weight=weight,
            attributes=attributes,
            uid=uid
        )
        
        if not result:
            return jsonify({
                "success": False,
                "message": "Edge creation failed. Source or target node not found."
            }), 404
        
        return jsonify({
            "success": True,
            "message": "Edge created successfully",
            "edge": result
        }), 201
        
    except Exception as e:
        logging.error(f"[{datetime.now()}] Error creating edge: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Error creating edge: {str(e)}"
        }), 500

@ukg_api.route('/edges/<uid>', methods=['GET'])
def get_edge(uid):
    """Get an edge by its UID."""
    try:
        edge = db_manager.get_edge(uid)
        
        if not edge:
            return jsonify({
                "success": False,
                "message": f"Edge with UID {uid} not found"
            }), 404
            
        return jsonify({
            "success": True,
            "edge": edge
        })
        
    except Exception as e:
        logging.error(f"[{datetime.now()}] Error retrieving edge {uid}: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Error retrieving edge: {str(e)}"
        }), 500

@ukg_api.route('/edges/<uid>', methods=['PUT'])
def update_edge(uid):
    """Update an edge's attributes."""
    try:
        data = request.json
        result = db_manager.update_edge(uid, **data)
        
        if not result:
            return jsonify({
                "success": False,
                "message": f"Edge with UID {uid} not found"
            }), 404
            
        return jsonify({
            "success": True,
            "message": "Edge updated successfully",
            "edge": result
        })
        
    except Exception as e:
        logging.error(f"[{datetime.now()}] Error updating edge {uid}: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Error updating edge: {str(e)}"
        }), 500

@ukg_api.route('/edges/<uid>', methods=['DELETE'])
def delete_edge(uid):
    """Delete an edge."""
    try:
        result = db_manager.delete_edge(uid)
        
        if not result:
            return jsonify({
                "success": False,
                "message": f"Edge with UID {uid} not found"
            }), 404
            
        return jsonify({
            "success": True,
            "message": "Edge deleted successfully"
        })
        
    except Exception as e:
        logging.error(f"[{datetime.now()}] Error deleting edge {uid}: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Error deleting edge: {str(e)}"
        }), 500

@ukg_api.route('/nodes/<node_uid>/connections', methods=['GET'])
def get_node_connections(node_uid):
    """Get connections to/from a node."""
    try:
        edge_type = request.args.get('edge_type')
        direction = request.args.get('direction', 'both')
        limit = int(request.args.get('limit', 100))
        
        if direction not in ['outgoing', 'incoming', 'both']:
            return jsonify({
                "success": False,
                "message": "Direction must be one of: outgoing, incoming, both"
            }), 400
        
        connections = db_manager.get_connected_nodes(
            node_uid=node_uid,
            edge_type=edge_type,
            direction=direction,
            limit=limit
        )
        
        return jsonify({
            "success": True,
            "node_uid": node_uid,
            "connections": connections,
            "count": len(connections),
            "filters": {
                "edge_type": edge_type,
                "direction": direction
            }
        })
        
    except Exception as e:
        logging.error(f"[{datetime.now()}] Error retrieving connections for node {node_uid}: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Error retrieving connections: {str(e)}"
        }), 500

# Session Management Endpoints
@ukg_api.route('/sessions', methods=['POST'])
def create_session():
    """Create a new UKG session."""
    try:
        data = request.json or {}
        
        session_id = data.get('session_id')
        user_query = data.get('user_query')
        target_confidence = float(data.get('target_confidence', 0.85))
        
        result = db_manager.create_session(
            session_id=session_id,
            user_query=user_query,
            target_confidence=target_confidence
        )
        
        return jsonify({
            "success": True,
            "message": "Session created successfully",
            "session": result
        }), 201
        
    except Exception as e:
        logging.error(f"[{datetime.now()}] Error creating session: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Error creating session: {str(e)}"
        }), 500

@ukg_api.route('/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session data."""
    try:
        session = db_manager.get_session(session_id)
        
        if not session:
            return jsonify({
                "success": False,
                "message": f"Session with ID {session_id} not found"
            }), 404
            
        return jsonify({
            "success": True,
            "session": session
        })
        
    except Exception as e:
        logging.error(f"[{datetime.now()}] Error retrieving session {session_id}: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Error retrieving session: {str(e)}"
        }), 500

@ukg_api.route('/sessions/<session_id>/complete', methods=['POST'])
def complete_session(session_id):
    """Mark a session as completed."""
    try:
        data = request.json or {}
        
        final_confidence = float(data.get('final_confidence', 0.0))
        status = data.get('status', 'completed')
        
        result = db_manager.complete_session(
            session_id=session_id,
            final_confidence=final_confidence,
            status=status
        )
        
        if not result:
            return jsonify({
                "success": False,
                "message": f"Session with ID {session_id} not found"
            }), 404
            
        return jsonify({
            "success": True,
            "message": "Session completed successfully",
            "session": result
        })
        
    except Exception as e:
        logging.error(f"[{datetime.now()}] Error completing session {session_id}: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Error completing session: {str(e)}"
        }), 500

# Memory Management Endpoints
@ukg_api.route('/memory', methods=['POST'])
def add_memory_entry():
    """Add a new entry to the structured memory."""
    try:
        data = request.json
        
        # Required fields
        session_id = data.get('session_id')
        entry_type = data.get('entry_type')
        
        if not session_id or not entry_type:
            return jsonify({
                "success": False,
                "message": "Both session_id and entry_type are required"
            }), 400
        
        # Optional fields
        uid = data.get('uid')
        content = data.get('content')
        pass_num = int(data.get('pass_num', 0))
        layer_num = int(data.get('layer_num', 0))
        confidence = float(data.get('confidence', 1.0))
        
        result = db_manager.add_memory_entry(
            session_id=session_id,
            entry_type=entry_type,
            content=content,
            pass_num=pass_num,
            layer_num=layer_num,
            confidence=confidence,
            uid=uid
        )
        
        if not result:
            return jsonify({
                "success": False,
                "message": f"Session with ID {session_id} not found"
            }), 404
            
        return jsonify({
            "success": True,
            "message": "Memory entry added successfully",
            "memory_entry": result
        }), 201
        
    except Exception as e:
        logging.error(f"[{datetime.now()}] Error adding memory entry: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Error adding memory entry: {str(e)}"
        }), 500

@ukg_api.route('/memory/<session_id>', methods=['GET'])
def get_memory_entries(session_id):
    """Get memory entries for a session."""
    try:
        entry_type = request.args.get('type')
        pass_num = request.args.get('pass')
        limit = int(request.args.get('limit', 100))
        
        if pass_num is not None:
            pass_num = int(pass_num)
        
        entries = db_manager.get_memory_entries(
            session_id=session_id,
            entry_type=entry_type,
            pass_num=pass_num,
            limit=limit
        )
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "memory_entries": entries,
            "count": len(entries),
            "filters": {
                "entry_type": entry_type,
                "pass_num": pass_num
            }
        })
        
    except Exception as e:
        logging.error(f"[{datetime.now()}] Error retrieving memory entries for session {session_id}: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Error retrieving memory entries: {str(e)}"
        }), 500

# Knowledge Algorithm Endpoints
@ukg_api.route('/kas', methods=['POST'])
def register_ka():
    """Register a Knowledge Algorithm."""
    try:
        data = request.json
        
        # Required fields
        ka_id = data.get('ka_id')
        name = data.get('name')
        
        if not ka_id or not name:
            return jsonify({
                "success": False,
                "message": "Both ka_id and name are required"
            }), 400
        
        # Optional fields
        description = data.get('description')
        input_schema = data.get('input_schema')
        output_schema = data.get('output_schema')
        version = data.get('version')
        
        result = db_manager.register_knowledge_algorithm(
            ka_id=ka_id,
            name=name,
            description=description,
            input_schema=input_schema,
            output_schema=output_schema,
            version=version
        )
        
        return jsonify({
            "success": True,
            "message": "Knowledge Algorithm registered successfully",
            "knowledge_algorithm": result
        }), 201
        
    except Exception as e:
        logging.error(f"[{datetime.now()}] Error registering Knowledge Algorithm: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Error registering Knowledge Algorithm: {str(e)}"
        }), 500

@ukg_api.route('/kas/executions', methods=['POST'])
def record_ka_execution():
    """Record an execution of a Knowledge Algorithm."""
    try:
        data = request.json
        
        # Required fields
        ka_id = data.get('ka_id')
        session_id = data.get('session_id')
        pass_num = int(data.get('pass_num', 0))
        layer_num = int(data.get('layer_num', 0))
        
        if not ka_id or not session_id:
            return jsonify({
                "success": False,
                "message": "Both ka_id and session_id are required"
            }), 400
        
        # Optional fields
        input_data = data.get('input_data')
        output_data = data.get('output_data')
        confidence = float(data.get('confidence', 0.0))
        execution_time = data.get('execution_time')
        status = data.get('status', 'completed')
        error_message = data.get('error_message')
        
        result = db_manager.record_ka_execution(
            ka_id=ka_id,
            session_id=session_id,
            pass_num=pass_num,
            layer_num=layer_num,
            input_data=input_data,
            output_data=output_data,
            confidence=confidence,
            execution_time=execution_time,
            status=status,
            error_message=error_message
        )
        
        if not result:
            return jsonify({
                "success": False,
                "message": f"Knowledge Algorithm with ID {ka_id} not found"
            }), 404
            
        return jsonify({
            "success": True,
            "message": "Knowledge Algorithm execution recorded successfully",
            "ka_execution": result
        }), 201
        
    except Exception as e:
        logging.error(f"[{datetime.now()}] Error recording KA execution: {str(e)}")
        logging.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": f"Error recording KA execution: {str(e)}"
        }), 500