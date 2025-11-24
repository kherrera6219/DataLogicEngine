"""
MCP API Endpoints

Provides REST API endpoints for managing MCP servers, clients,
resources, tools, and prompts.
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import asyncio
import logging

from extensions import db
from models import MCPServer as MCPServerModel, MCPResource, MCPTool, MCPPrompt
from core.mcp import MCPManager

logger = logging.getLogger(__name__)

# Create blueprint
mcp_bp = Blueprint('mcp', __name__, url_prefix='/api/mcp')

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


# Server Management Endpoints

@mcp_bp.route('/servers', methods=['GET'])
@login_required
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

    except Exception as e:
        logger.error(f"Error listing servers: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@mcp_bp.route('/servers', methods=['POST'])
@login_required
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

    except Exception as e:
        logger.error(f"Error creating server: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@mcp_bp.route('/servers/<server_id>', methods=['GET'])
@login_required
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

    except Exception as e:
        logger.error(f"Error getting server: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@mcp_bp.route('/servers/<server_id>', methods=['DELETE'])
@login_required
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

    except Exception as e:
        logger.error(f"Error deleting server: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Resource Endpoints

@mcp_bp.route('/servers/<server_id>/resources', methods=['GET'])
@login_required
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

    except Exception as e:
        logger.error(f"Error listing resources: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@mcp_bp.route('/servers/<server_id>/resources/<int:resource_id>', methods=['GET'])
@login_required
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
        resource.last_accessed = datetime.utcnow()
        db.session.commit()

        # Get runtime server and read resource
        manager = get_mcp_manager()
        server = manager.get_server(server_id)

        if server:
            try:
                # In a full implementation, this would use asyncio to read the resource
                content = asyncio.run(server._handle_resources_read({'uri': resource.uri}))
                return jsonify({
                    'success': True,
                    'resource': resource.to_dict(),
                    'content': content
                }), 200
            except Exception as e:
                logger.error(f"Error reading resource content: {e}")

        return jsonify({
            'success': True,
            'resource': resource.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Error reading resource: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Tool Endpoints

@mcp_bp.route('/servers/<server_id>/tools', methods=['GET'])
@login_required
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

    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@mcp_bp.route('/servers/<server_id>/tools/<int:tool_id>/call', methods=['POST'])
@login_required
def call_tool(server_id, tool_id):
    """Call a tool"""
    try:
        tool = MCPTool.query.get(tool_id)

        if not tool:
            return jsonify({
                'success': False,
                'error': 'Tool not found'
            }), 404

        data = request.get_json()
        arguments = data.get('arguments', {})

        # Get runtime server and call tool
        manager = get_mcp_manager()
        server = manager.get_server(server_id)

        if not server:
            return jsonify({
                'success': False,
                'error': 'Server not running'
            }), 500

        try:
            result = asyncio.run(server._handle_tools_call({
                'name': tool.name,
                'arguments': arguments
            }))

            # Update tool stats
            tool.execution_count += 1
            tool.success_count += 1
            tool.last_executed = datetime.utcnow()
            db.session.commit()

            return jsonify({
                'success': True,
                'result': result
            }), 200

        except Exception as e:
            # Update failure stats
            tool.execution_count += 1
            tool.failure_count += 1
            tool.last_executed = datetime.utcnow()
            db.session.commit()

            logger.error(f"Error calling tool: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    except Exception as e:
        logger.error(f"Error in tool call endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Prompt Endpoints

@mcp_bp.route('/servers/<server_id>/prompts', methods=['GET'])
@login_required
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

    except Exception as e:
        logger.error(f"Error listing prompts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@mcp_bp.route('/servers/<server_id>/prompts/<int:prompt_id>/get', methods=['POST'])
@login_required
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
            result = asyncio.run(server._handle_prompts_get({
                'name': prompt.name,
                'arguments': arguments
            }))

            # Update prompt stats
            prompt.usage_count += 1
            prompt.last_used = datetime.utcnow()
            db.session.commit()

            return jsonify({
                'success': True,
                'prompt': result
            }), 200

        except Exception as e:
            logger.error(f"Error getting prompt: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    except Exception as e:
        logger.error(f"Error in get prompt endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Client Management Endpoints

@mcp_bp.route('/clients', methods=['GET'])
@login_required
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

    except Exception as e:
        logger.error(f"Error listing clients: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@mcp_bp.route('/clients', methods=['POST'])
@login_required
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

    except Exception as e:
        logger.error(f"Error creating client: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@mcp_bp.route('/clients/<client_id>/connect/<server_id>', methods=['POST'])
@login_required
def connect_client(client_id, server_id):
    """Connect a client to a server"""
    try:
        manager = get_mcp_manager()
        result = asyncio.run(manager.connect_client_to_server(client_id, server_id))

        return jsonify({
            'success': True,
            'connection': result
        }), 200

    except Exception as e:
        logger.error(f"Error connecting client: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Statistics Endpoint

@mcp_bp.route('/stats', methods=['GET'])
@login_required
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

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Setup default servers endpoint

@mcp_bp.route('/setup-default', methods=['POST'])
@login_required
def setup_default_servers():
    """Set up default MCP servers"""
    try:
        if not current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Admin access required'
            }), 403

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

    except Exception as e:
        logger.error(f"Error setting up default servers: {e}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
