"""
Storage API Routes for DataLogicEngine.

Provides endpoints for:
- Health checking all storage services
- Testing individual connections
- Getting storage configuration status
"""

import logging
import json
import os
import shutil
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote, urlparse

from flask import Blueprint, current_app, jsonify, request
from backend.auth.api_decorators import api_session_login_required
from backend.runtime import get_application_runtime
from backend.security.desktop_ipc import require_desktop_ipc_capability

storage_api = Blueprint('storage_api', __name__, url_prefix='/api/v1/storage')
logger = logging.getLogger(__name__)

DATA_PLANE_API_KEYS = {
    "postgres": "postgresql",
    "redis": "redis",
    "neo4j": "neo4j",
    "vector": "chroma",
    "object": "minio",
}


def _supervised_storage_health() -> dict:
    runtime = get_application_runtime()
    snapshot = runtime.supervisor.snapshot()
    services = {}
    for api_name, runtime_name in DATA_PLANE_API_KEYS.items():
        status = snapshot.get(runtime_name, {})
        services[api_name] = {
            "healthy": status.get("state") == "ready",
            "state": status.get("state", "not_installed"),
            "safe_reason": status.get("safe_reason"),
            "endpoint": status.get("endpoint"),
            "expected_identity": status.get("expected_identity"),
            "observed_identity": status.get("observed_identity"),
            "updated_at": status.get("updated_at"),
            "is_cloud": False,
            "source": "internal_supervisor",
        }
    manager = current_app.extensions.get("dle_data_plane_manager")
    if manager is not None:
        details = manager.service_metadata()
        for api_name, runtime_name in DATA_PLANE_API_KEYS.items():
            service_details = details.get(runtime_name, {})
            services[api_name].update(
                {
                    "version": service_details.get("version"),
                    "expected_version": service_details.get("expected_version"),
                    "profile": service_details.get("profile"),
                    "production_authorized": service_details.get("production_authorized", False),
                }
            )
    return {
        "mode": "internal",
        "services": services,
        "production_authorized": bool(
            manager is not None and manager.plan.production_authorized
        ),
    }


def _runtime_root() -> Path:
    runtime = current_app.extensions.get("dle_runtime")
    if runtime is not None:
        return runtime.runtime_root
    settings_path = os.environ.get("DATALOGIC_STORAGE_SETTINGS_PATH")
    if settings_path:
        return Path(settings_path).resolve().parent
    return Path.cwd()


def _sqlite_path_from_database_url() -> Path | None:
    url = str(current_app.config.get("SQLALCHEMY_DATABASE_URI") or "")
    if not url.startswith("sqlite"):
        return None
    parsed = urlparse(url)
    if parsed.path:
        return Path(unquote(parsed.path)).resolve()
    if ":///" in url:
        return Path(unquote(url.split(":///", 1)[1])).resolve()
    return None


def _directory_size(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    total = 0
    for child in path.rglob("*"):
        try:
            if child.is_file():
                total += child.stat().st_size
        except OSError:
            continue
    return total


def _sqlite_metrics() -> dict:
    db_path = _sqlite_path_from_database_url()
    if not db_path or not db_path.exists():
        return {"available": False, "path": str(db_path) if db_path else None, "size_bytes": 0, "tables": 0, "rows": 0}

    metrics = {"available": True, "path": str(db_path), "size_bytes": db_path.stat().st_size, "tables": 0, "rows": 0}
    try:
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
            table_names = [
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                ).fetchall()
            ]
            metrics["tables"] = len(table_names)
            metrics["rows"] = sum(
                int(conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])  # nosec B608 – names from sqlite_master, not user input
                for table in table_names
            )
    except Exception:
        logger.exception("Failed to collect SQLite metrics")
        metrics["available"] = False
        metrics["error"] = "SQLite metrics unavailable"
    return metrics


def _local_path_metrics(name: str, relative_path: str) -> dict:
    path = (_runtime_root() / relative_path).resolve()
    return {
        "name": name,
        "path": str(path),
        "exists": path.exists(),
        "size_bytes": _directory_size(path),
    }


def _object_store_metrics() -> dict:
    base_path = (_runtime_root() / "databases" / "objects").resolve()
    buckets = {}
    if base_path.exists():
        for child in base_path.iterdir():
            if child.is_dir():
                buckets[child.name] = {
                    "object_count": sum(1 for item in child.rglob("*") if item.is_file()),
                    "total_bytes": _directory_size(child),
                }
    return {"path": str(base_path), "buckets": buckets, "size_bytes": _directory_size(base_path)}


def _neo4j_metrics() -> dict:
    data_path = (_runtime_root() / "databases" / "neo4j" / "data").resolve()
    return {
        "available": data_path.exists(),
        "path": str(data_path),
        "size_bytes": _directory_size(data_path),
    }


def _build_desktop_metrics() -> dict:
    sqlite_metrics = _sqlite_metrics()
    chroma_metrics = _local_path_metrics("chroma", "databases/chroma")
    memory_metrics = _local_path_metrics("structured_memory", "databases/memory")
    object_metrics = _object_store_metrics()
    result = {
        "generated_at": datetime.now(UTC).isoformat(),
        "runtime_root": str(_runtime_root()),
        "sqlite": sqlite_metrics,
        "neo4j": _neo4j_metrics(),
        "chroma": chroma_metrics,
        "object_store": object_metrics,
        "structured_memory": memory_metrics,
        "total_local_bytes": sum(
            int(item.get("size_bytes") or 0)
            for item in [sqlite_metrics, chroma_metrics, object_metrics, memory_metrics]
        ),
    }
    manager = current_app.extensions.get("dle_data_plane_manager")
    if manager is not None:
        result["data_plane"] = manager.status_snapshot()
        result["storage_authority"] = "supervisor_owned_internal_services"
    return result


def _create_backup(
    target_dir: str | None = None,
    *,
    recovery_secret: str | None = None,
) -> dict:
    if current_app.config.get("DLE_DATA_PLANE_DRIVER") == "podman":
        if not recovery_secret:
            raise RuntimeError("portable_recovery_secret_required")
        from backend.storage.managed_backup import create_managed_backup

        runtime = get_application_runtime()
        target = target_dir or str(runtime.runtime_root / "backups")
        return create_managed_backup(current_app._get_current_object(), runtime, target, recovery_secret)
    root = _runtime_root()
    backup_root = Path(target_dir).expanduser().resolve() if target_dir else root / "backups"
    backup_root.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    staging_dir = backup_root / f"datalogic_backup_{timestamp}"
    staging_dir.mkdir(parents=True, exist_ok=False)

    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "runtime_root": str(root),
        "components": {},
    }

    db_path = _sqlite_path_from_database_url()
    if db_path and db_path.exists():
        sqlite_target = staging_dir / "ukg_database.db"
        with sqlite3.connect(db_path) as source, sqlite3.connect(sqlite_target) as target:
            source.backup(target)
        manifest["components"]["sqlite"] = {"path": str(db_path), "included": True}
    else:
        manifest["components"]["sqlite"] = {"path": str(db_path) if db_path else None, "included": False}

    for name, relative_path in {
        "chroma": "databases/chroma",
        "objects": "databases/objects",
        "memory": "databases/memory",
    }.items():
        source = (root / relative_path).resolve()
        if source.exists():
            shutil.copytree(source, staging_dir / name, dirs_exist_ok=True)
            manifest["components"][name] = {"path": str(source), "included": True}
        else:
            manifest["components"][name] = {"path": str(source), "included": False}

    manifest["metrics"] = _build_desktop_metrics()
    manifest_path = staging_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    archive_base = str(staging_dir)
    archive_path = shutil.make_archive(archive_base, "zip", staging_dir)
    shutil.rmtree(staging_dir)
    return {
        "artifact_path": archive_path,
        "manifest": manifest,
        "size_bytes": Path(archive_path).stat().st_size,
    }


@storage_api.route('/health', methods=['GET'])
@api_session_login_required
def get_storage_health():
    """Get health status of all storage services."""
    try:
        if current_app.extensions.get("dle_data_plane_manager") is not None:
            status = _supervised_storage_health()
        else:
            from backend.storage import get_connection_manager

            status = get_connection_manager().get_status_report()
        
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception:
        logger.exception("Failed to get storage health")
        return jsonify({
            'success': False,
            'error': 'Storage health is unavailable'
        }), 500


@storage_api.route('/health/<service>', methods=['GET'])
@api_session_login_required
def check_service_health(service: str):
    """Check health of a specific storage service."""
    try:
        valid_services = list(DATA_PLANE_API_KEYS)
        if service not in valid_services:
            return jsonify({
                'success': False,
                'error': f'Invalid service. Must be one of: {valid_services}'
            }), 400
        
        manager = current_app.extensions.get("dle_data_plane_manager")
        if manager is None:
            from backend.storage import get_connection_manager

            healthy = bool(get_connection_manager().check_health(service))
            data = {
                "service": service,
                "healthy": healthy,
                "state": "ready" if healthy else "failed",
                "safe_reason": None if healthy else "legacy_development_probe_failed",
                "endpoint": None,
                "expected_identity": None,
                "observed_identity": None,
            }
        else:
            runtime_name = DATA_PLANE_API_KEYS[service]
            runtime = get_application_runtime()
            status = runtime.supervisor.probe(runtime_name)
            healthy = status.state.value == "ready"
            data = {
                "service": service,
                "healthy": healthy,
                "state": status.state.value,
                "safe_reason": status.safe_reason,
                "endpoint": status.endpoint,
                "expected_identity": status.expected_identity,
                "observed_identity": status.observed_identity,
            }

        return jsonify({
            'success': True,
            'data': data,
        }), 200 if healthy else 503
    except Exception:
        logger.exception("Failed to check storage service health")
        return jsonify({
            'success': False,
            'error': 'Storage service health is unavailable'
        }), 500


@storage_api.route('/desktop-metrics', methods=['GET'])
@api_session_login_required
def get_desktop_metrics():
    """Return detailed local desktop storage metrics."""
    try:
        return jsonify({
            'success': True,
            'data': _build_desktop_metrics(),
        })
    except Exception:
        logger.exception("Failed to build desktop metrics")
        return jsonify({
            'success': False,
            'error': 'Failed to build desktop metrics'
        }), 500


@storage_api.route('/backup', methods=['POST'])
@api_session_login_required
def run_desktop_backup():
    """Create a one-click local backup archive in the selected folder."""
    capability_error = require_desktop_ipc_capability("backup")
    if capability_error:
        return capability_error
    try:
        data = request.get_json(silent=True) or {}
        target_dir = data.get("target_dir") if isinstance(data.get("target_dir"), str) else None
        recovery_secret = (
            data.get("recovery_secret")
            if isinstance(data.get("recovery_secret"), str)
            else None
        )
        with get_application_runtime().exclusive_operation("backup"):
            backup = _create_backup(target_dir, recovery_secret=recovery_secret)
        return jsonify({
            'success': True,
            'data': backup,
        }), 201
    except Exception:
        logger.exception("Desktop backup failed")
        return jsonify({
            'success': False,
            'error': 'Desktop backup failed'
        }), 500


@storage_api.route('/desktop-flags', methods=['GET'])
@api_session_login_required
def get_desktop_flags():
    """Return desktop local-first runtime feature flags."""
    try:
        from backend.storage.runtime_settings import (
            get_local_slm_audit_mode,
            get_offline_queue_enabled,
        )
        return jsonify({
            'success': True,
            'data': {
                'local_slm_audit_mode': get_local_slm_audit_mode(),
                'offline_queue_enabled': get_offline_queue_enabled(),
            },
        })
    except Exception:
        logger.exception("Failed to load desktop flags")
        return jsonify({'success': False, 'error': 'Desktop flags are unavailable'}), 500


@storage_api.route('/desktop-flags', methods=['POST'])
@api_session_login_required
def set_desktop_flags():
    """Persist desktop local-first runtime feature flags."""
    try:
        from backend.storage.runtime_settings import (
            set_local_slm_audit_mode,
            set_offline_queue_enabled,
        )
        data = request.get_json(silent=True) or {}
        response: dict[str, bool] = {}
        if 'local_slm_audit_mode' in data:
            response['local_slm_audit_mode'] = set_local_slm_audit_mode(bool(data.get('local_slm_audit_mode')))
        if 'offline_queue_enabled' in data:
            response['offline_queue_enabled'] = set_offline_queue_enabled(bool(data.get('offline_queue_enabled')))
        if not response:
            return jsonify({'success': False, 'error': 'No desktop flags provided'}), 400
        return jsonify({'success': True, 'data': response})
    except Exception:
        logger.exception("Failed to save desktop flags")
        return jsonify({'success': False, 'error': 'Desktop flag update failed'}), 500


@storage_api.route('/test-connection', methods=['POST'])
@api_session_login_required
def test_connection():
    """Reject obsolete arbitrary storage targets; test supervised services instead."""
    if current_app.extensions.get("dle_data_plane_manager") is not None:
        return jsonify({
            'success': False,
            'error': 'Arbitrary storage targets are disabled; use /health/<service>',
        }), 410
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
    except Exception:
        logger.exception("Connection test failed")
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
    except Exception:
        logger.exception("PostgreSQL connection test failed")
        return {
            'service': 'postgres',
            'connected': False,
            'message': 'PostgreSQL connection test failed'
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
    except Exception:
        logger.exception("Redis connection test failed")
        return {
            'service': 'redis',
            'connected': False,
            'message': 'Redis connection test failed'
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
    except Exception:
        logger.exception("Neo4j connection test failed")
        return {
            'service': 'neo4j',
            'connected': False,
            'message': 'Neo4j connection test failed'
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
        except Exception:
            logger.exception("ChromaDB path check failed")
            return {
                'service': 'vector',
                'connected': False,
                'message': 'ChromaDB path access failed'
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
        except Exception:
            logger.exception("Pinecone connection test failed")
            return {
                'service': 'vector',
                'connected': False,
                'message': 'Pinecone connection test failed'
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
        except Exception:
            logger.exception("Local object storage path check failed")
            return {
                'service': 'object',
                'connected': False,
                'message': 'Local object storage path access failed'
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
        except Exception:
            logger.exception("S3 connection test failed")
            return {
                'service': 'object',
                'connected': False,
                'message': 'S3 connection test failed'
            }
    else:
        return {
            'service': 'object',
            'connected': False,
            'message': f'Unknown object storage provider: {provider}'
        }


@storage_api.route('/databases/start', methods=['POST'])
@api_session_login_required
def start_databases():
    """Start local database services (desktop mode only)."""
    try:
        supervisor = get_application_runtime().supervisor
        results = {
            service: supervisor.start(service).to_dict()
            for service in DATA_PLANE_API_KEYS.values()
        }
        success = all(result["success"] for result in results.values())
        return jsonify({
            'success': success,
            'results': results,
            'message': 'Database startup completed' if success else 'One or more database services did not start',
        }), 200 if success else 503
    except Exception:
        logger.exception("Failed to start database services")
        return jsonify({
            'success': False,
            'error': 'Database startup failed'
        }), 500


@storage_api.route('/databases/autostart', methods=['GET'])
@api_session_login_required
def get_database_autostart():
    """Get persisted desktop auto-start preference for local databases."""
    try:
        from backend.storage.runtime_settings import get_auto_start_databases

        return jsonify({
            'success': True,
            'enabled': bool(get_auto_start_databases()),
        })
    except Exception:
        logger.exception("Failed to load database auto-start preference")
        return jsonify({
            'success': False,
            'error': 'Database auto-start preference is unavailable'
        }), 500


@storage_api.route('/databases/autostart', methods=['POST'])
@api_session_login_required
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
    except Exception:
        logger.exception("Failed to save database auto-start preference")
        return jsonify({
            'success': False,
            'error': 'Database auto-start preference update failed'
        }), 500


@storage_api.route('/cloud-config', methods=['GET'])
@api_session_login_required
def get_cloud_config():
    """Report the retired externally hosted storage configuration surface."""
    return jsonify({
        'success': False,
        'error': 'Cloud database configuration is not part of the supported product',
    }), 410


@storage_api.route('/cloud-config', methods=['POST'])
@api_session_login_required
def save_cloud_config():
    """Reject the retired externally hosted storage configuration surface."""
    return jsonify({
        'success': False,
        'error': 'Cloud database configuration is not part of the supported product',
    }), 410


@storage_api.route('/databases/stop', methods=['POST'])
@api_session_login_required
def stop_databases():
    """Stop local database services."""
    try:
        supervisor = get_application_runtime().supervisor
        results = {
            service: supervisor.stop(service).to_dict()
            for service in reversed(tuple(DATA_PLANE_API_KEYS.values()))
        }
        success = all(result["success"] for result in results.values())
        return jsonify({
            'success': success,
            'results': results,
            'message': 'Database shutdown completed' if success else 'One or more database services did not stop',
        }), 200 if success else 500
    except Exception:
        logger.exception("Failed to stop database services")
        return jsonify({
            'success': False,
            'error': 'Database shutdown failed'
        }), 500
