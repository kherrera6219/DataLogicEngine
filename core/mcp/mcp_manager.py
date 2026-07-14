"""
MCP Manager

Manages MCP servers and clients, providing a central registry
and orchestration layer for the DataLogicEngine MCP integration.
"""

from typing import Dict, List, Optional, Any
import logging

from .mcp_server import MCPServer
from .mcp_client import MCPClient
from .mcp_protocol import MCPError, MCPErrorCode
from .runtime_loop import MCPRuntimeLoop


logger = logging.getLogger(__name__)


class MCPManager:
    """
    Central manager for MCP servers and clients in DataLogicEngine

    Provides server registry, client connections, and orchestration
    """

    def __init__(self, app_orchestrator=None):
        self.app_orchestrator = app_orchestrator

        # Server and client registries
        self.servers: Dict[str, MCPServer] = {}
        self.clients: Dict[str, MCPClient] = {}
        self.client_connections: Dict[str, str] = {}  # client_id -> server_id

        # External dynamic servers configuration and clients
        self.external_configs: Dict[str, Dict[str, Any]] = {}
        self.external_clients: Dict[str, MCPClient] = {}
        self.runtime_loop = MCPRuntimeLoop()

        # Statistics
        self.stats = {
            "servers_created": 0,
            "clients_created": 0,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0
        }

        logger.info("MCP Manager initialized")

    def create_server(
        self,
        name: str,
        version: str = "1.0.0",
        description: Optional[str] = None
    ) -> MCPServer:
        """Create and register a new MCP server"""
        server = MCPServer(name=name, version=version, description=description)
        self.servers[server.server_id] = server
        self.stats["servers_created"] += 1

        logger.info(f"Created MCP server: {name} (ID: {server.server_id})")
        return server

    def get_server(self, server_id: str) -> Optional[MCPServer]:
        """Get a server by ID"""
        return self.servers.get(server_id)

    def get_server_by_name(self, name: str) -> Optional[MCPServer]:
        """Get a server by name"""
        for server in self.servers.values():
            if server.name == name:
                return server
        return None

    def list_servers(self) -> List[Dict[str, Any]]:
        """List all registered servers"""
        return [server.get_server_info() for server in self.servers.values()]

    def create_client(
        self,
        name: str = "DataLogicEngine",
        version: str = "1.0.0"
    ) -> MCPClient:
        """Create and register a new MCP client"""
        client = MCPClient(name=name, version=version)
        self.clients[client.client_id] = client
        self.stats["clients_created"] += 1

        logger.info(f"Created MCP client: {name} (ID: {client.client_id})")
        return client

    def get_client(self, client_id: str) -> Optional[MCPClient]:
        """Get a client by ID"""
        return self.clients.get(client_id)

    def list_clients(self) -> List[Dict[str, Any]]:
        """List all registered clients"""
        return [client.get_client_info() for client in self.clients.values()]

    async def connect_client_to_server(
        self,
        client_id: str,
        server_id: str
    ) -> Dict[str, Any]:
        """Connect a client to a server"""
        client = self.get_client(client_id)
        server = self.get_server(server_id)

        if not client:
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, f"Client not found: {client_id}")
        if not server:
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, f"Server not found: {server_id}")

        server.register_client_callback(client.handle_request)
        result = await client.initialize(server)
        self.client_connections[client_id] = server_id

        logger.info(f"Connected client {client_id} to server {server_id}")
        return result

    def disconnect_client(self, client_id: str):
        """Disconnect a client from its server"""
        client = self.get_client(client_id)
        if client:
            client.disconnect()
            if client_id in self.client_connections:
                del self.client_connections[client_id]
            logger.info(f"Disconnected client: {client_id}")

    def remove_server(self, server_id: str):
        """Remove a server from the registry"""
        if server_id in self.servers:
            # Disconnect all clients connected to this server
            clients_to_disconnect = [
                cid for cid, sid in self.client_connections.items()
                if sid == server_id
            ]
            for client_id in clients_to_disconnect:
                self.disconnect_client(client_id)

            del self.servers[server_id]
            logger.info(f"Removed server: {server_id}")

    def remove_client(self, client_id: str):
        """Remove a client from the registry"""
        if client_id in self.clients:
            self.disconnect_client(client_id)
            del self.clients[client_id]
            logger.info(f"Removed client: {client_id}")

    def load_external_config(self) -> Dict[str, Any]:
        """Return explicit runtime definitions; repository JSON is not an authority."""
        return dict(self.external_configs)

    async def start_external_servers(self):
        """Legacy bulk start is disabled; each server needs an exact consent grant."""
        raise MCPError(
            MCPErrorCode.INVALID_REQUEST,
            "Bulk MCP auto-start is disabled",
            {"reason": "MCP_EXPLICIT_CONSENT_REQUIRED"},
        )

    async def stop_external_servers(self):
        """Clean up and disconnect all spawned external MCP servers"""
        for name, client in list(self.external_clients.items()):
            try:
                await client.disconnect_async()
                self.remove_client(client.client_id)
            except Exception as e:
                logger.error(f"Error stopping external client '{name}': {e}")
        self.external_clients.clear()
        logger.info("Cleared all active external MCP server processes")

    async def _start_external_server(
        self,
        server_key: str,
        definition: Dict[str, Any],
        resolved_env: Dict[str, str],
    ) -> Dict[str, Any]:
        existing = self.external_clients.pop(server_key, None)
        if existing is not None:
            await existing.disconnect_async()
            self.remove_client(existing.client_id)

        client = self.create_client(name=f"ExternalClient-{definition['name']}")
        try:
            initialized = await client.connect_via_stdio(
                [definition["command"], *definition.get("args", [])],
                {**definition.get("env", {}), **resolved_env},
                cwd=definition["cwd"],
                limits=definition.get("limits"),
            )
            self.external_clients[server_key] = client
            self.external_configs[server_key] = dict(definition)
            self.client_connections[client.client_id] = f"external-{server_key}"

            discovery: Dict[str, Any] = {"tools": [], "resources": [], "prompts": [], "errors": []}
            capabilities = client.server_capabilities or {}
            for capability, operation in (
                ("tools", client.list_tools),
                ("resources", client.list_resources),
                ("prompts", client.list_prompts),
            ):
                if capability not in capabilities:
                    continue
                try:
                    discovery[capability] = await operation()
                except Exception as exc:
                    discovery["errors"].append(
                        {"capability": capability, "error_code": type(exc).__name__}
                    )
            return {
                "initialized": initialized,
                "client": client.get_client_info(),
                "discovery": discovery,
            }
        except Exception:
            await client.disconnect_async()
            self.remove_client(client.client_id)
            raise

    def start_external_server_sync(
        self,
        server_key: str,
        definition: Dict[str, Any],
        resolved_env: Dict[str, str],
    ) -> Dict[str, Any]:
        timeout = (float(definition.get("limits", {}).get("request_timeout_seconds", 30)) * 4) + 5
        return self.runtime_loop.submit(
            self._start_external_server(server_key, definition, resolved_env),
            timeout=timeout,
        )

    async def _stop_external_server(self, server_key: str) -> bool:
        client = self.external_clients.pop(server_key, None)
        self.external_configs.pop(server_key, None)
        if client is None:
            return False
        await client.disconnect_async()
        self.remove_client(client.client_id)
        return True

    def stop_external_server_sync(self, server_key: str) -> bool:
        return bool(self.runtime_loop.submit(self._stop_external_server(server_key), timeout=10))

    def restart_external_server_sync(
        self,
        server_key: str,
        definition: Dict[str, Any],
        resolved_env: Dict[str, str],
    ) -> Dict[str, Any]:
        if server_key in self.external_clients:
            self.stop_external_server_sync(server_key)
        return self.start_external_server_sync(server_key, definition, resolved_env)

    def call_external_tool_sync(
        self,
        server_key: str,
        name: str,
        arguments: Dict[str, Any],
        *,
        timeout: float,
        operation_id: str | None = None,
    ) -> Dict[str, Any]:
        client = self.external_clients.get(server_key)
        if client is None:
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, "Server is not running")
        return self.runtime_loop.submit(
            client.call_tool(name=name, arguments=arguments),
            timeout=timeout,
            operation_id=operation_id,
        )

    def read_external_resource_sync(
        self,
        server_key: str,
        uri: str,
        *,
        timeout: float,
        operation_id: str | None = None,
    ) -> Dict[str, Any]:
        client = self.external_clients.get(server_key)
        if client is None:
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, "Server is not running")
        return self.runtime_loop.submit(
            client.read_resource(uri=uri),
            timeout=timeout,
            operation_id=operation_id,
        )

    def get_external_prompt_sync(
        self,
        server_key: str,
        name: str,
        arguments: Dict[str, Any],
        *,
        timeout: float,
        operation_id: str | None = None,
    ) -> Dict[str, Any]:
        client = self.external_clients.get(server_key)
        if client is None:
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, "Server is not running")
        return self.runtime_loop.submit(
            client.get_prompt(name=name, arguments=arguments),
            timeout=timeout,
            operation_id=operation_id,
        )

    def cancel_external_operation(self, operation_id: str) -> bool:
        """Cancel one durable external operation by its server-owned ledger ID."""
        return self.runtime_loop.cancel(operation_id)

    def shutdown(self) -> None:
        if self.external_clients:
            try:
                self.runtime_loop.submit(self.stop_external_servers(), timeout=15)
            except Exception:
                logger.exception("MCP runtime shutdown failed")
        self.runtime_loop.stop()

    def get_stats(self) -> Dict[str, Any]:
        """Get manager statistics"""
        return {
            **self.stats,
            "active_servers": len(self.servers),
            "active_clients": len(self.clients),
            "active_connections": len(self.client_connections)
        }

    # Integration with DataLogicEngine components

    def setup_default_servers(self):
        """Reject the retired fake/default server registration path."""
        raise MCPError(
            MCPErrorCode.METHOD_NOT_FOUND,
            "Placeholder default MCP servers were removed",
            {"reason": "MCP_DEFAULT_PLACEHOLDERS_REMOVED"},
        )
