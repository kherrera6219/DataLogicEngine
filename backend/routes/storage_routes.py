"""
Storage API Routes for DataLogicEngine.

Provides endpoints for:
- Health checking all storage services
- Testing individual connections
- Getting storage configuration status
"""

import logging
import os

from flask import Blueprint, jsonify, request
from flask_login import login_required

storage_api = Blueprint('storage_api', __name__, url_prefix='/api/v1/storage')
logger = logging.getLogger(__name__)


@storage_api.route('/health', methods=['GET'])
@login_required
def get_storage_health():
    """Get health status of all storage services."""
    try:
        from backend.storage import get_connection_manager
        
        manager = get_connection_manager()
        status = manager.get_status_report()
        
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@storage_api.route('/health/<service>', methods=['GET'])
@login_required
def check_service_health(service: str):
    """Check health of a specific storage service."""
    try:
        from backend.storage import get_connection_manager
        
        manager = get_connection_manager()
        
        valid_services = ['postgres', 'redis', 'neo4j', 'vector', 'object']
        if service not in valid_services:
            return jsonify({
                'success': False,
                'error': f'Invalid service. Must be one of: {valid_services}'
            }), 400
        
        healthy = manager.check_health(service)
        
        return jsonify({
            'success': True,
            'data': {
                'service': service,
                'healthy': healthy
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@storage_api.route('/test-connection', methods=['POST'])
@login_required
def test_connection():
    """Test a storage connection with provided credentials."""
    try:
        from backend.schemas.request_schemas import StorageTestRequest
        from pydantic import ValidationError
        
        try:
            req = StorageTestRequest(**(request.get_json() or {}))
        except ValidationError as e:
            return jsonify({
                'success': False,
                'error': e.errors()
            }), 400
        
        service = req.service
        data = req.model_dump(exclude_none=True)
        
        result = {
            'service': service,
            'connected': False,
            'message': ''
        }
        
        if service == 'postgres':
            result = _test_postgres(data)
        elif service == 'redis':
            result = _test_redis(data)
        elif service == 'neo4j':
            result = _test_neo4j(data)
        elif service == 'vector':
            result = _test_vector(data)
        elif service == 'object':
            result = _test_object(data)
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return jsonify({
            'success': False,
            'error': "Internal server error during connection test"
        }), 500


def _test_postgres(data: dict) -> dict:
    """Test PostgreSQL connection."""
    import socket
    
    host = data.get('host', '127.0.0.1')
    port = int(data.get('port', 5432))
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            return {
                'service': 'postgres',
                'connected': True,
                'message': f'Successfully connected to PostgreSQL at {host}:{port}'
            }
        else:
            return {
                'service': 'postgres',
                'connected': False,
                'message': f'Cannot connect to PostgreSQL at {host}:{port}'
            }
    except Exception as e:
        return {
            'service': 'postgres',
            'connected': False,
            'message': str(e)
        }


def _test_redis(data: dict) -> dict:
    """Test Redis connection."""
    import socket
    
    host = data.get('host', '127.0.0.1')
    port = int(data.get('port', 6379))
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            return {
                'service': 'redis',
                'connected': True,
                'message': f'Successfully connected to Redis at {host}:{port}'
            }
        else:
            return {
                'service': 'redis',
                'connected': False,
                'message': f'Cannot connect to Redis at {host}:{port}'
            }
    except Exception as e:
        return {
            'service': 'redis',
            'connected': False,
            'message': str(e)
        }


def _test_neo4j(data: dict) -> dict:
    """Test Neo4j connection."""
    import socket
    
    host = data.get('host', '127.0.0.1')
    port = int(data.get('port', 7687))
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            return {
                'service': 'neo4j',
                'connected': True,
                'message': f'Successfully connected to Neo4j at {host}:{port}'
            }
        else:
            return {
                'service': 'neo4j',
                'connected': False,
                'message': f'Cannot connect to Neo4j at {host}:{port}'
            }
    except Exception as e:
        return {
            'service': 'neo4j',
            'connected': False,
            'message': str(e)
        }


def _test_vector(data: dict) -> dict:
    """Test vector database connection."""
    provider = data.get('provider', 'chromadb')
    
    if provider == 'chromadb':
        local_path = data.get('local_path', 'databases/chroma')
        try:
            from backend.utils.safe_path import get_safe_path
            safe_local_path = get_safe_path(os.getcwd(), local_path)
            os.makedirs(safe_local_path, exist_ok=True)
            return {
                'service': 'vector',
                'connected': True,
                'message': f'ChromaDB path accessible: {safe_local_path}'
            }
        except Exception as e:
            return {
                'service': 'vector',
                'connected': False,
                'message': f"Path access refused: {str(e)}"
            }
    elif provider == 'pinecone':
        api_key = data.get('api_key')
        if not api_key:
            return {
                'service': 'vector',
                'connected': False,
                'message': 'Pinecone API key required'
            }
        try:
            from pinecone import Pinecone
            pc = Pinecone(api_key=api_key)
            indexes = pc.list_indexes()
            return {
                'service': 'vector',
                'connected': True,
                'message': f'Connected to Pinecone. Found {len(indexes)} indexes.'
            }
        except Exception as e:
            return {
                'service': 'vector',
                'connected': False,
                'message': str(e)
            }
    else:
        return {
            'service': 'vector',
            'connected': False,
            'message': f'Unknown vector provider: {provider}'
        }


def _test_object(data: dict) -> dict:
    """Test object storage connection."""
    provider = data.get('provider', 'local')
    
    if provider == 'local':
        local_path = data.get('local_path', './databases/objects')
        try:
            import os
            os.makedirs(local_path, exist_ok=True)
            return {
                'service': 'object',
                'connected': True,
                'message': f'Local object storage path accessible: {local_path}'
            }
        except Exception as e:
            return {
                'service': 'object',
                'connected': False,
                'message': str(e)
            }
    elif provider == 's3':
        endpoint = data.get('endpoint_url')
        access_key = data.get('access_key')
        secret_key = data.get('secret_key')
        
        if not access_key or not secret_key:
            return {
                'service': 'object',
                'connected': False,
                'message': 'S3 access_key and secret_key required'
            }
        
        try:
            import boto3
            client = boto3.client(
                's3',
                endpoint_url=endpoint,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key
            )
            client.list_buckets()
            return {
                'service': 'object',
                'connected': True,
                'message': f'Connected to S3-compatible storage at {endpoint or "AWS"}'
            }
        except Exception as e:
            return {
                'service': 'object',
                'connected': False,
                'message': str(e)
            }
    else:
        return {
            'service': 'object',
            'connected': False,
            'message': f'Unknown object storage provider: {provider}'
        }


@storage_api.route('/databases/start', methods=['POST'])
@login_required
def start_databases():
    """Start local database services (desktop mode only)."""
    try:
        from backend.storage import get_db_manager
        
        manager = get_db_manager()
        manager.start_all()
        
        return jsonify({
            'success': True,
            'message': 'Database startup initiated'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@storage_api.route('/databases/autostart', methods=['GET'])
@login_required
def get_database_autostart():
    """Get persisted desktop auto-start preference for local databases."""
    try:
        from backend.storage.runtime_settings import get_auto_start_databases

        return jsonify({
            'success': True,
            'enabled': bool(get_auto_start_databases()),
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@storage_api.route('/databases/autostart', methods=['POST'])
@login_required
def set_database_autostart():
    """Persist desktop auto-start preference for local databases."""
    try:
        from backend.storage.runtime_settings import set_auto_start_databases

        data = request.get_json() or {}
        if 'enabled' not in data:
            return jsonify({
                'success': False,
                'error': 'enabled flag is required'
            }), 400

        enabled = bool(data.get('enabled'))
        saved = set_auto_start_databases(enabled)

        return jsonify({
            'success': True,
            'enabled': saved,
            'message': 'Auto-start preference saved',
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@storage_api.route('/cloud-config', methods=['GET'])
@login_required
def get_cloud_config():
    """Return saved cloud connection strings (secrets masked)."""
    try:
        from backend.storage.runtime_settings import load_storage_settings
        settings = load_storage_settings()
        cloud = settings.get('cloud_config', {})
        # Return only whether each key is set — never expose raw secrets via GET.
        masked = {k: ('***' if v else '') for k, v in cloud.items()}
        return jsonify({'success': True, 'cloud_config': masked})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_api.route('/cloud-config', methods=['POST'])
@login_required
def save_cloud_config():
    """Persist cloud connection strings to runtime settings."""
    try:
        from backend.storage.runtime_settings import load_storage_settings, save_storage_settings
        data = request.get_json() or {}

        allowed_keys = {
            'postgres_url', 'redis_url', 'neo4j_uri',
            'pinecone_api_key', 's3_endpoint', 's3_bucket',
            's3_access_key', 's3_secret_key',
        }
        cloud_patch = {k: str(v) for k, v in data.items() if k in allowed_keys}

        settings = load_storage_settings()
        existing = settings.get('cloud_config', {})
        existing.update(cloud_patch)
        settings['cloud_config'] = existing
        save_storage_settings(settings)

        return jsonify({'success': True, 'message': 'Cloud configuration saved'})
    except Exception as e:
        logger.error(f"Failed to save cloud config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_api.route('/databases/stop', methods=['POST'])
@login_required
def stop_databases():
    """Stop local database services."""
    try:
        from backend.storage import get_db_manager

        manager = get_db_manager()
        manager.stop_all()

        return jsonify({
            'success': True,
            'message': 'Database shutdown initiated'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
