
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime

from backend.auth.api_decorators import api_login_required, api_admin_required

honeycomb_api = Blueprint('honeycomb_api', __name__)


def _get_honeycomb():
    """Resolve the Honeycomb manager from app config.

    The Honeycomb System is canonical Axis 3 in the 17-axis layout; the
    legacy numbering (Axis 5, still reflected in the axis5_honeycomb.py
    filename) must not be used for manager lookup.
    """
    axis_system = current_app.config.get('AXIS_SYSTEM')
    if not axis_system:
        return None
    return axis_system.axis_managers.get(3)


@honeycomb_api.route('/api/honeycomb/generate', methods=['POST'])
@api_login_required
def generate_honeycomb():
    """Generate a honeycomb network centered on a specified node."""
    try:
        data = request.json
        if not data or 'node_uid' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameter: node_uid',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        node_uid = data['node_uid']
        max_connections = data.get('max_connections', 50)
        
        honeycomb = _get_honeycomb()
        
        if not honeycomb:
            return jsonify({
                'status': 'error',
                'message': 'Honeycomb system not initialized',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        result = honeycomb.generate_multi_axis_honeycomb(node_uid, max_connections)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error generating honeycomb: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error generating honeycomb: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

@honeycomb_api.route('/api/honeycomb/sector-crosswalk', methods=['POST'])
@api_login_required
def generate_sector_crosswalk():
    """Generate crosswalk connections between a sector and all pillar levels."""
    try:
        data = request.json
        if not data or 'sector_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameter: sector_id',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        sector_id = data['sector_id']
        
        honeycomb = _get_honeycomb()
        
        if not honeycomb:
            return jsonify({
                'status': 'error',
                'message': 'Honeycomb system not initialized',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        result = honeycomb.generate_sector_pillar_crosswalk(sector_id)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error generating sector crosswalk: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error generating sector crosswalk: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

@honeycomb_api.route('/api/honeycomb/find-paths', methods=['POST'])
@api_login_required
def find_crosswalk_paths():
    """Find all possible crosswalk paths between two nodes through the honeycomb system."""
    try:
        data = request.json
        if not data or 'source_uid' not in data or 'target_uid' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameters: source_uid and target_uid',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        source_uid = data['source_uid']
        target_uid = data['target_uid']
        max_depth = data.get('max_depth', 3)
        
        honeycomb = _get_honeycomb()
        
        if not honeycomb:
            return jsonify({
                'status': 'error',
                'message': 'Honeycomb system not initialized',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        result = honeycomb.find_crosswalk_paths(source_uid, target_uid, max_depth)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error finding crosswalk paths: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error finding crosswalk paths: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500

@honeycomb_api.route('/api/honeycomb/connect', methods=['POST'])
@api_admin_required
def create_connection():
    """Create a honeycomb connection between two nodes."""
    try:
        data = request.json
        if not data or 'source_uid' not in data or 'target_uid' not in data or 'connection_type' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameters: source_uid, target_uid, and connection_type',
                'timestamp': datetime.now().isoformat()
            }), 400
        
        source_uid = data['source_uid']
        target_uid = data['target_uid']
        connection_type = data['connection_type']
        strength = data.get('strength', 1.0)
        attributes = data.get('attributes')
        
        honeycomb = _get_honeycomb()
        
        if not honeycomb:
            return jsonify({
                'status': 'error',
                'message': 'Honeycomb system not initialized',
                'timestamp': datetime.now().isoformat()
            }), 500
        
        result = honeycomb.create_honeycomb_connection(source_uid, target_uid, connection_type, strength, attributes)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error creating honeycomb connection: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Error creating honeycomb connection: {str(e)}",
            'timestamp': datetime.now().isoformat()
        }), 500
