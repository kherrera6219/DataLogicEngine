# ruff: noqa: E402
"""
MCP API Endpoints

Provides REST API endpoints for managing MCP servers, clients,
resources, tools, and prompts.
"""

from flask import Blueprint, Response, current_app, jsonify, g, request, stream_with_context
from datetime import datetime, UTC
import asyncio
import logging
import threading
import time

from extensions import db
from models import MCPServer as MCPServerModel, MCPResource, MCPTool, MCPPrompt
from core.mcp import MCPManager
from backend.mcp_server.connector_metrics import infer_connector_id, record_connector_execution
from backend.mcp_server.router import MCPRouter
from backend.mcp_server.scope_enforcement import (
    ScopeEnforcementError,
    enforce_scopes,
    normalize_scopes,
    parse_execution_context,
)

logger = logging.getLogger(__name__)

# Thread-local event loop for async operations (avoids blocking Flask routes)
_async_loop = None
_async_loop_lock = threading.Lock()


def get_async_loop():
    """Get or create a shared event loop for async operations."""
    global _async_loop
    with _async_loop_lock:
        if _async_loop is None or _async_loop.is_closed():
            _async_loop = asyncio.new_event_loop()
        return _async_loop


def run_async(coro):
    """Run an async coroutine safely without blocking Flask routes."""
    loop = get_async_loop()
    try:
        return loop.run_until_complete(coro)
    except RuntimeError:
        # Fallback if loop is already running (shouldn't happen with thread-local)
        new_loop = asyncio.new_event_loop()
        try:
            return new_loop.run_until_complete(coro)
        finally:
            new_loop.close()


from backend.auth.api_decorators import (
    api_admin_required,
    api_login_required,
    api_session_login_required,
    get_authenticated_principal,
)

# Create blueprint
mcp_bp = Blueprint('mcp', __name__)

# Global MCP manager instance
mcp_manager = None


def init_mcp_manager(app_orchestrator=None):
    """Initialize the MCP manager"""
    global mcp_manager
    mcp_manager = MCPManager(app_orchestrator=app_orchestrator)
    logger.info("MCP Manager initialized")
    return mcp_manager


def get_mcp_manager():
    """Get the global MCP manager instance"""
    global mcp_manager
    if mcp_manager is None:
        mcp_manager = MCPManager()
    return mcp_manager


def _mcp_error(message, status=500):
    return jsonify({'success': False, 'error': message}), status


def _tool_uses_write_scope(tool_name: str) -> bool:
    lowered = (tool_name or "").strip().lower()
    write_markers = ("create", "update", "delete", "write", "import", "sync", "patch")
    return any(marker in lowered for marker in write_markers)


def _required_tool_scopes(tool: MCPTool) -> list[str]:
    metadata = tool.tool_metadata if isinstance(tool.tool_metadata, dict) else {}
    explicit_scopes = normalize_scopes(metadata.get("required_scopes"))
    if explicit_scopes:
        return sorted(explicit_scopes)

    connector = infer_connector_id(tool.name)
    if connector is None:
        return []
    action = "write" if _tool_uses_write_scope(tool.name) else "read"
    return ["mcp:execute", f"connector:{connector}:{action}"]


def _build_tool_execution_context() -> dict:
    user = get_authenticated_principal()
    tenant_id = getattr(user, "tenant_id", None) or request.headers.get("X-Tenant-ID")
    # Single-mode / OS-level auth: the one OS user is the owner.
    role = "owner"
    roles = {role}

    # Single-mode / OS-level auth (auth deprecation Phase B, 2026-06-13): the one OS
    # user is the owner with full access — grant all MCP connector scopes
    # unconditionally rather than deriving them from the removed RBAC layer.
    scopes: set[str] = {"mcp:execute", "connector:*:read", "connector:*:write", "*"}
    is_admin = True

    api_key = getattr(g, "external_api_key", None)
    if api_key is not None:
        permissions = api_key.permissions if isinstance(api_key.permissions, dict) else {}
        scopes.update(normalize_scopes(permissions.get("connector_scopes")))

    if is_admin:
        scopes.add("*")

    return {
        "user_id": str(getattr(user, "id", "")),
        "tenant_id": str(tenant_id) if tenant_id else None,
        "roles": sorted(roles),
        "scopes": sorted(scopes),
        "is_admin": is_admin,
    }


@mcp_bp.route('/rpc', methods=['POST'])
@api_session_login_required
def mcp_rpc():
    """Handle active MCP JSON-RPC requests, including sampling and subscriptions."""
    try:
        payload = request.get_json() or {}
        response = run_async(MCPRouter().handle_message(payload))
        return jsonify(response), 200
    except Exception as exc:
        logger.error("MCP RPC failed: %s", exc)
        return jsonify({"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": "MCP RPC failed"}}), 500


@mcp_bp.route('/subscriptions/stream/<client_id>', methods=['GET'])
@api_session_login_required
def mcp_subscription_stream(client_id):
    """SSE stream for MCP resource subscription notifications."""
    from backend.mcp_server.subscriptions import subscription_manager

    return Response(
        stream_with_context(subscription_manager.stream(client_id)),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        },
    )


# Server Management Endpoints

@mcp_bp.route('/servers', methods=['GET'])
@api_session_login_required
def list_servers():
    """List all MCP servers"""
    try:
        # Get from database
        db_servers = MCPServerModel.query.all()
        servers_data = [server.to_dict() for server in db_servers]

        # Get runtime servers
        manager = get_mcp_manager()
        runtime_servers = manager.list_servers()

        return jsonify({
            'success': True,
            'servers': servers_data,
            'runtime_servers': runtime_servers,
            'count': len(servers_data)
        }), 200

    except Exception:
        logger.exception("Error listing servers")
        return _mcp_error('MCP servers are unavailable', 500)


@mcp_bp.route('/servers', methods=['POST'])
@api_admin_required
def create_server():
    """Create a new MCP server"""
    try:
        data = request.get_json()

        name = data.get('name')
        version = data.get('version', '1.0.0')
        description = data.get('description', '')

        if not name:
            return jsonify({
                'success': False,
                'error': 'Server name is required'
            }), 400

        # Create runtime server
        manager = get_mcp_manager()
        server = manager.create_server(
            name=name,
            version=version,
            description=description
        )

        # Save to database
        db_server = MCPServerModel(
            server_id=server.server_id,
            name=name,
            version=version,
            description=description,
            status='active',
            supports_resources=True,
            supports_tools=True,
            supports_prompts=True,
            supports_logging=True,
            config=data.get('config', {}),
            metadata=data.get('metadata', {})
        )
        db.session.add(db_server)
        db.session.commit()

        logger.info(f"Created MCP server: {name}")

        return jsonify({
            'success': True,
            'server': db_server.to_dict()
        }), 201

    except Exception:
        logger.exception("Error creating server")
        db.session.rollback()
        return _mcp_error('MCP server could not be created', 500)


@mcp_bp.route('/servers/<server_id>', methods=['GET'])
@api_session_login_required
def get_server(server_id):
    """Get a specific MCP server"""
    try:
        db_server = MCPServerModel.query.filter_by(server_id=server_id).first()

        if not db_server:
            return jsonify({
                'success': False,
                'error': 'Server not found'
            }), 404

        # Get runtime server info
        manager = get_mcp_manager()
        runtime_server = manager.get_server(server_id)

        response_data = db_server.to_dict()
        if runtime_server:
            response_data['runtime_info'] = runtime_server.get_server_info()

        return jsonify({
            'success': True,
            'server': response_data
        }), 200

    except Exception:
        logger.exception("Error getting server")
        return _mcp_error('MCP server details are unavailable', 500)


@mcp_bp.route('/servers/<server_id>', methods=['DELETE'])
@api_admin_required
def delete_server(server_id):
    """Delete an MCP server"""
    try:
        db_server = MCPServerModel.query.filter_by(server_id=server_id).first()

        if not db_server:
            return jsonify({
                'success': False,
                'error': 'Server not found'
            }), 404

        # Remove from runtime
        manager = get_mcp_manager()
        manager.remove_server(server_id)

        # Delete from database
        db.session.delete(db_server)
        db.session.commit()

        logger.info(f"Deleted MCP server: {server_id}")

        return jsonify({
            'success': True,
            'message': 'Server deleted successfully'
        }), 200

    except Exception:
        logger.exception("Error deleting server")
        db.session.rollback()
        return _mcp_error('MCP server could not be deleted', 500)


# Resource Endpoints

@mcp_bp.route('/servers/<server_id>/resources', methods=['GET'])
@api_session_login_required
def list_resources(server_id):
    """List resources for a server"""
    try:
        db_server = MCPServerModel.query.filter_by(server_id=server_id).first()

        if not db_server:
            return jsonify({
                'success': False,
                'error': 'Server not found'
            }), 404

        resources = MCPResource.query.filter_by(server_id=db_server.id).all()
        resources_data = [resource.to_dict() for resource in resources]

        return jsonify({
            'success': True,
            'resources': resources_data,
            'count': len(resources_data)
        }), 200

    except Exception:
        logger.exception("Error listing resources")
        return _mcp_error('MCP resources are unavailable', 500)


@mcp_bp.route('/servers/<server_id>/resources/<int:resource_id>', methods=['GET'])
@api_session_login_required
def read_resource(server_id, resource_id):
    """Read a specific resource"""
    try:
        resource = MCPResource.query.get(resource_id)

        if not resource:
            return jsonify({
                'success': False,
                'error': 'Resource not found'
            }), 404

        # Update access stats
        resource.access_count += 1
        resource.last_accessed = datetime.now(UTC)
        db.session.commit()

        # Get runtime server and read resource
        manager = get_mcp_manager()
        server = manager.get_server(server_id)

        if server:
            try:
                # Use shared event loop for async operations
                content = run_async(server._handle_resources_read({'uri': resource.uri}))
                return jsonify({
                    'success': True,
                    'resource': resource.to_dict(),
                    'content': content
                }), 200
            except Exception:
                logger.exception("Error reading resource content")

        return jsonify({
            'success': True,
            'resource': resource.to_dict()
        }), 200

    except Exception:
        logger.exception("Error reading resource")
        return _mcp_error('MCP resource is unavailable', 500)


# Tool Endpoints

@mcp_bp.route('/servers/<server_id>/tools', methods=['GET'])
@api_session_login_required
def list_tools(server_id):
    """List tools for a server"""
    try:
        db_server = MCPServerModel.query.filter_by(server_id=server_id).first()

        if not db_server:
            return jsonify({
                'success': False,
                'error': 'Server not found'
            }), 404

        tools = MCPTool.query.filter_by(server_id=db_server.id).all()
        tools_data = [tool.to_dict() for tool in tools]

        return jsonify({
            'success': True,
            'tools': tools_data,
            'count': len(tools_data)
        }), 200

    except Exception:
        logger.exception("Error listing tools")
        return _mcp_error('MCP tools are unavailable', 500)


@mcp_bp.route('/servers/<server_id>/tools/<int:tool_id>/call', methods=['POST'])
@api_login_required
def call_tool(server_id, tool_id):
    """Call a tool"""
    try:
        tool = MCPTool.query.get(tool_id)

        if not tool:
            return jsonify({
                'success': False,
                'error': 'Tool not found'
            }), 404

        data = request.get_json(silent=True) or {}
        arguments = data.get('arguments', {})
        connector_id = infer_connector_id(tool.name)

        execution_context_raw = _build_tool_execution_context()
        execution_context = parse_execution_context(execution_context_raw)
        required_scopes = _required_tool_scopes(tool)
        try:
            enforce_scopes(
                tool_name=tool.name,
                required_scopes=required_scopes,
                context=execution_context,
                permissive_on_missing_context=False,
            )
        except ScopeEnforcementError as scope_error:
            logger.warning("MCP scope enforcement denied tool call for %s: %s", tool.name, scope_error)
            return jsonify({
                'success': False,
                'error': str(scope_error),
                'code': 'MCP_SCOPE_DENIED',
                'required_scopes': sorted(required_scopes),
            }), 403

        # Get runtime server and call tool
        manager = get_mcp_manager()
        server = manager.get_server(server_id)

        if not server:
            return jsonify({
                'success': False,
                'error': 'Server not running'
            }), 500

        started = time.perf_counter()
        try:
            result = run_async(server._handle_tools_call({
                'name': tool.name,
                'arguments': arguments,
                'context': execution_context_raw,
            }))
            duration_ms = (time.perf_counter() - started) * 1000.0

            # Update tool stats
            tool.execution_count += 1
            tool.success_count += 1
            tool.last_executed = datetime.now(UTC)
            db.session.commit()
            record_connector_execution(
                tool_name=tool.name,
                connector_id=connector_id,
                duration_ms=duration_ms,
                success=True,
            )

            return jsonify({
                'success': True,
                'result': result,
                'metrics': {
                    'connector_id': connector_id,
                    'latency_ms': round(duration_ms, 2),
                },
            }), 200

        except Exception:
            duration_ms = (time.perf_counter() - started) * 1000.0
            # Update failure stats
            tool.execution_count += 1
            tool.failure_count += 1
            tool.last_executed = datetime.now(UTC)
            db.session.commit()
            record_connector_execution(
                tool_name=tool.name,
                connector_id=connector_id,
                duration_ms=duration_ms,
                success=False,
            )

            logger.exception("Error calling tool")
            return _mcp_error('MCP tool execution failed', 500)

    except Exception:
        logger.exception("Error in tool call endpoint")
        return _mcp_error('MCP tool execution failed', 500)


# Prompt Endpoints

@mcp_bp.route('/servers/<server_id>/prompts', methods=['GET'])
@api_session_login_required
def list_prompts(server_id):
    """List prompts for a server"""
    try:
        db_server = MCPServerModel.query.filter_by(server_id=server_id).first()

        if not db_server:
            return jsonify({
                'success': False,
                'error': 'Server not found'
            }), 404

        prompts = MCPPrompt.query.filter_by(server_id=db_server.id).all()
        prompts_data = [prompt.to_dict() for prompt in prompts]

        return jsonify({
            'success': True,
            'prompts': prompts_data,
            'count': len(prompts_data)
        }), 200

    except Exception:
        logger.exception("Error listing prompts")
        return _mcp_error('MCP prompts are unavailable', 500)


@mcp_bp.route('/servers/<server_id>/prompts/<int:prompt_id>/get', methods=['POST'])
@api_session_login_required
def get_prompt(server_id, prompt_id):
    """Get a prompt template"""
    try:
        prompt = MCPPrompt.query.get(prompt_id)

        if not prompt:
            return jsonify({
                'success': False,
                'error': 'Prompt not found'
            }), 404

        data = request.get_json()
        arguments = data.get('arguments', {})

        # Get runtime server and get prompt
        manager = get_mcp_manager()
        server = manager.get_server(server_id)

        if not server:
            return jsonify({
                'success': False,
                'error': 'Server not running'
            }), 500

        try:
            result = run_async(server._handle_prompts_get({
                'name': prompt.name,
                'arguments': arguments
            }))

            # Update prompt stats
            prompt.usage_count += 1
            prompt.last_used = datetime.now(UTC)
            db.session.commit()

            return jsonify({
                'success': True,
                'prompt': result
            }), 200

        except Exception:
            logger.exception("Error getting prompt")
            return _mcp_error('MCP prompt is unavailable', 500)

    except Exception:
        logger.exception("Error in get prompt endpoint")
        return _mcp_error('MCP prompt is unavailable', 500)


# Client Management Endpoints

@mcp_bp.route('/clients', methods=['GET'])
@api_session_login_required
def list_clients():
    """List all MCP clients"""
    try:
        manager = get_mcp_manager()
        clients = manager.list_clients()

        return jsonify({
            'success': True,
            'clients': clients,
            'count': len(clients)
        }), 200

    except Exception:
        logger.exception("Error listing clients")
        return _mcp_error('MCP clients are unavailable', 500)


@mcp_bp.route('/clients', methods=['POST'])
@api_admin_required
def create_client():
    """Create a new MCP client"""
    try:
        data = request.get_json()

        name = data.get('name', 'DataLogicEngine')
        version = data.get('version', '1.0.0')

        manager = get_mcp_manager()
        client = manager.create_client(name=name, version=version)

        return jsonify({
            'success': True,
            'client': client.get_client_info()
        }), 201

    except Exception:
        logger.exception("Error creating client")
        return _mcp_error('MCP client could not be created', 500)


@mcp_bp.route('/clients/<client_id>/connect/<server_id>', methods=['POST'])
@api_admin_required
def connect_client(client_id, server_id):
    """Connect a client to a server"""
    try:
        manager = get_mcp_manager()
        result = run_async(manager.connect_client_to_server(client_id, server_id))

        return jsonify({
            'success': True,
            'connection': result
        }), 200

    except Exception:
        logger.exception("Error connecting client")
        return _mcp_error('MCP client connection failed', 500)


# Statistics Endpoint

@mcp_bp.route('/stats', methods=['GET'])
@api_session_login_required
def get_stats():
    """Get MCP system statistics"""
    try:
        manager = get_mcp_manager()
        stats = manager.get_stats()

        # Database stats
        db_stats = {
            'total_servers': MCPServerModel.query.count(),
            'active_servers': MCPServerModel.query.filter_by(status='active').count(),
            'total_resources': MCPResource.query.count(),
            'total_tools': MCPTool.query.count(),
            'total_prompts': MCPPrompt.query.count()
        }

        return jsonify({
            'success': True,
            'stats': {
                **stats,
                **db_stats
            }
        }), 200

    except Exception:
        logger.exception("Error getting stats")
        return _mcp_error('MCP statistics are unavailable', 500)


# Setup default servers endpoint

@mcp_bp.route('/setup-default', methods=['POST'])
@api_admin_required
def setup_default_servers():
    """Set up default MCP servers"""
    try:
        manager = get_mcp_manager()
        server = manager.setup_default_servers()

        # Save to database if not exists
        db_server = MCPServerModel.query.filter_by(server_id=server.server_id).first()
        if not db_server:
            db_server = MCPServerModel(
                server_id=server.server_id,
                name=server.name,
                version=server.version,
                description=server.description,
                status='active'
            )
            db.session.add(db_server)
            db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Default servers set up successfully',
            'server': db_server.to_dict()
        }), 200

    except Exception:
        logger.exception("Error setting up default servers")
        db.session.rollback()
        return _mcp_error('Default MCP servers could not be set up', 500)


@mcp_bp.route('/console', methods=['POST'])
@api_admin_required
def mcp_console():
    """Execute a raw MCP console command (admin only)."""
    try:
        data = request.get_json() or {}
        command = str(data.get('command', '')).strip()
        if not command:
            return jsonify({'success': False, 'error': 'command is required'}), 400

        manager = get_mcp_manager()
        # Interpret simple commands: list-servers, stats, help
        if command in ('list-servers', 'servers'):
            servers = MCPServerModel.query.all()
            result = [s.to_dict() for s in servers]
        elif command in ('stats', 'status'):
            stats = manager.get_stats()
            result = stats
        elif command == 'help':
            result = {
                'commands': ['list-servers', 'servers', 'stats', 'status', 'help'],
                'description': 'MCP Console — type a command to inspect the MCP system.'
            }
        else:
            result = {'error': 'Unknown command. Type "help" for available commands.'}

        return jsonify({'success': True, 'result': result})
    except Exception:
        logger.exception("MCP console error")
        return jsonify({'success': False, 'error': 'MCP console is unavailable'}), 500


@mcp_bp.route('/config', methods=['GET'])
@api_admin_required
def get_external_config():
    """Retrieve external MCP servers configuration"""
    try:
        manager = get_mcp_manager()
        config = manager.load_external_config()
        return jsonify({
            'success': True,
            'config': config,
            'active_servers': list(manager.external_clients.keys())
        }), 200
    except Exception:
        logger.exception("Error getting external config")
        return jsonify({'success': False, 'error': 'MCP external configuration is unavailable'}), 500


@mcp_bp.route('/config', methods=['POST'])
@api_admin_required
def update_external_config():
    """Update external MCP servers configuration and dynamically hot-reload"""
    try:
        data = request.get_json() or {}
        new_config = data.get("config", {})
        
        import json
        from pathlib import Path
        config_path = Path(current_app.root_path).parent / 'config' / 'mcp_servers.json'
        
        # Save config
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump({"mcpServers": new_config}, f, indent=2)
            
        # Hot-reload all external servers
        manager = get_mcp_manager()
        run_async(manager.start_external_servers())
        
        return jsonify({
            'success': True,
            'message': 'Configuration updated and dynamic servers reloaded',
            'active_servers': list(manager.external_clients.keys())
        }), 200
    except Exception:
        logger.exception("Error updating external config")
        return _mcp_error('MCP external configuration could not be updated', 500)


@mcp_bp.route('/servers/<name>/start', methods=['POST'])
@api_admin_required
def start_dynamic_server(name):
    """Start a specific configured dynamic MCP server"""
    try:
        manager = get_mcp_manager()
        manager.load_external_config()
        
        if name not in manager.external_configs:
            return _mcp_error('Server configuration not found', 404)
            
        if name in manager.external_clients:
            return jsonify({'success': True, 'message': f"Server '{name}' is already running"}), 200
            
        config = manager.external_configs[name]
        command = [config["command"]] + config.get("args", [])
        env = config.get("env", {})
        
        client = manager.create_client(name=f"ExternalClient-{name}")
        run_async(client.connect_via_stdio(command, env))
        manager.external_clients[name] = client
        manager.client_connections[client.client_id] = f"external-{name}"
        
        return jsonify({
            'success': True,
            'message': f"Dynamic server '{name}' started successfully",
            'server': client.get_client_info()
        }), 200
    except Exception:
        logger.exception("Error starting dynamic server")
        return _mcp_error('MCP dynamic server could not be started', 500)


@mcp_bp.route('/servers/<name>/stop', methods=['POST'])
@api_admin_required
def stop_dynamic_server(name):
    """Stop a specific active dynamic MCP server"""
    try:
        manager = get_mcp_manager()
        
        if name not in manager.external_clients:
            return _mcp_error('Dynamic server is not running', 404)
            
        client = manager.external_clients.pop(name)
        client.disconnect()
        manager.remove_client(client.client_id)
        
        return jsonify({
            'success': True,
            'message': f"Dynamic server '{name}' stopped successfully"
        }), 200
    except Exception:
        logger.exception("Error stopping dynamic server")
        return _mcp_error('MCP dynamic server could not be stopped', 500)
