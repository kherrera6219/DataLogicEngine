"""
MCP Manager

Manages MCP servers and clients, providing a central registry
and orchestration layer for the DataLogicEngine MCP integration.
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import logging

from .mcp_server import MCPServer
from .mcp_client import MCPClient
from .mcp_protocol import MCPError, MCPErrorCode


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
        """Set up default MCP servers for DataLogicEngine"""

        # Main UKG Server
        ukg_server = self.create_server(
            name="DataLogicEngine-UKG",
            version="1.0.0",
            description="Universal Knowledge Graph MCP Server"
        )

        # Register UKG resources
        self._register_ukg_resources(ukg_server)

        # Register UKG tools
        self._register_ukg_tools(ukg_server)

        # Register UKG prompts
        self._register_ukg_prompts(ukg_server)

        logger.info("Default MCP servers set up successfully")
        return ukg_server

    def _register_ukg_resources(self, server: MCPServer):
        """Register UKG-related resources"""

        # Knowledge Graph Resource
        async def get_graph_stats(params):
            if self.app_orchestrator and hasattr(self.app_orchestrator, 'graph_manager'):
                stats = self.app_orchestrator.graph_manager.get_stats()
                return str(stats)
            return "Knowledge graph not available"

        server.register_resource(
            uri="ukg://graph/stats",
            name="Knowledge Graph Statistics",
            handler=get_graph_stats,
            description="Current statistics of the Universal Knowledge Graph",
            mime_type="application/json"
        )

        # Pillars Resource
        async def get_pillars(params):
            if self.app_orchestrator and hasattr(self.app_orchestrator, 'graph_manager'):
                # In a full implementation, fetch from database
                return "Pillars: Identity, Technology, Healthcare, Finance, Education, Government"
            return "Pillars not available"

        server.register_resource(
            uri="ukg://pillars",
            name="Knowledge Pillars",
            handler=get_pillars,
            description="List of knowledge pillars in the UKG",
            mime_type="text/plain"
        )

        # Knowledge Algorithms Resource
        async def get_algorithms(params):
            if self.app_orchestrator and hasattr(self.app_orchestrator, 'ka_loader'):
                algorithms = self.app_orchestrator.ka_loader.list_algorithms()
                return f"Available algorithms: {', '.join(algorithms)}"
            return "Knowledge algorithms not available"

        server.register_resource(
            uri="ukg://algorithms",
            name="Knowledge Algorithms",
            handler=get_algorithms,
            description="List of available knowledge algorithms",
            mime_type="text/plain"
        )

    def _register_ukg_tools(self, server: MCPServer):
        """Register UKG-related tools"""

        # Query Tool
        async def query_graph(arguments):
            query = arguments.get("query", "")
            if not query:
                raise MCPError(MCPErrorCode.INVALID_PARAMS, "Missing 'query' parameter")

            if self.app_orchestrator:
                result = await self._run_simulation(query)
                return result
            return "Query execution not available"

        server.register_tool(
            name="query_knowledge_graph",
            description="Query the Universal Knowledge Graph using natural language",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language query"
                    },
                    "context": {
                        "type": "object",
                        "description": "Optional context for the query"
                    }
                },
                "required": ["query"]
            },
            handler=query_graph
        )

        # Execute Knowledge Algorithm Tool
        async def execute_algorithm(arguments):
            algorithm_name = arguments.get("algorithm")
            params = arguments.get("params", {})

            if not algorithm_name:
                raise MCPError(MCPErrorCode.INVALID_PARAMS, "Missing 'algorithm' parameter")

            if self.app_orchestrator and hasattr(self.app_orchestrator, 'ka_loader'):
                # Execute the knowledge algorithm
                result = f"Executed {algorithm_name} with params: {params}"
                return result
            return "Algorithm execution not available"

        server.register_tool(
            name="execute_knowledge_algorithm",
            description="Execute a specific knowledge algorithm",
            input_schema={
                "type": "object",
                "properties": {
                    "algorithm": {
                        "type": "string",
                        "description": "Name of the knowledge algorithm to execute"
                    },
                    "params": {
                        "type": "object",
                        "description": "Parameters for the algorithm"
                    }
                },
                "required": ["algorithm"]
            },
            handler=execute_algorithm
        )

    def _register_ukg_prompts(self, server: MCPServer):
        """Register UKG-related prompt templates"""

        # Regulatory Analysis Prompt
        async def regulatory_prompt(arguments):
            framework = arguments.get("framework", "GDPR")
            return [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"Analyze regulatory compliance for {framework} framework. "
                                f"Include key requirements, potential gaps, and recommendations."
                    }
                }
            ]

        server.register_prompt(
            name="regulatory_analysis",
            description="Prompt template for regulatory compliance analysis",
            handler=regulatory_prompt,
            arguments=[
                {
                    "name": "framework",
                    "description": "Regulatory framework to analyze (e.g., GDPR, HIPAA, SOX)",
                    "required": False
                }
            ]
        )

        # Expert Persona Prompt
        async def expert_persona_prompt(arguments):
            domain = arguments.get("domain", "Technology")
            question = arguments.get("question", "")

            return [
                {
                    "role": "system",
                    "content": {
                        "type": "text",
                        "text": f"You are an expert in the {domain} domain with deep knowledge "
                                f"and years of experience. Provide authoritative guidance."
                    }
                },
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": question
                    }
                }
            ]

        server.register_prompt(
            name="expert_persona",
            description="Prompt template for expert persona simulation",
            handler=expert_persona_prompt,
            arguments=[
                {
                    "name": "domain",
                    "description": "Expert domain (e.g., Technology, Healthcare, Finance)",
                    "required": True
                },
                {
                    "name": "question",
                    "description": "Question to ask the expert",
                    "required": True
                }
            ]
        )

    async def _run_simulation(self, query: str) -> str:
        """Run a simulation using the AppOrchestrator"""
        if not self.app_orchestrator:
            return "Simulation not available"

        try:
            # In a full implementation, call the AppOrchestrator
            result = f"Simulation result for query: {query}"
            self.stats["successful_requests"] += 1
            return result
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"Simulation error: {e}")
            return f"Simulation failed: {str(e)}"
