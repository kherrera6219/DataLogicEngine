"""
MCP Client Implementation

Implements a Model Context Protocol client that can connect to
MCP servers and access their resources, tools, and prompts.
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from .mcp_protocol import (
    MCPMessage, MCPClientInfo, MCPMethod,
    MCPError, MCPErrorCode
)


logger = logging.getLogger(__name__)


class MCPClient:
    """
    MCP Client implementation for DataLogicEngine

    Connects to MCP servers to access resources, tools, and prompts
    """

    def __init__(
        self,
        name: str = "DataLogicEngine",
        version: str = "1.0.0"
    ):
        self.name = name
        self.version = version
        self.client_id = str(uuid.uuid4())

        # Connection state
        self.connected = False
        self.server_info = None
        self.server_capabilities = None

        # Request tracking
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.message_id_counter = 0

        logger.info(f"MCP Client '{self.name}' created with ID: {self.client_id}")

    def _get_next_message_id(self) -> str:
        """Generate next message ID"""
        self.message_id_counter += 1
        return f"{self.client_id}-{self.message_id_counter}"

    async def initialize(self, server_handler: Any) -> Dict[str, Any]:
        """
        Initialize connection with an MCP server

        Args:
            server_handler: The MCP server instance to connect to

        Returns:
            Server initialization response
        """
        client_info = MCPClientInfo(
            name=self.name,
            version=self.version
        )

        message = MCPMessage(
            id=self._get_next_message_id(),
            method=MCPMethod.INITIALIZE.value,
            params={
                "protocolVersion": client_info.protocol_version,
                "capabilities": {},
                "clientInfo": {
                    "name": client_info.name,
                    "version": client_info.version
                }
            }
        )

        response = await server_handler.handle_request(message)

        if response.error:
            raise MCPError(
                response.error.get("code", MCPErrorCode.INTERNAL_ERROR),
                response.error.get("message", "Unknown error")
            )

        self.connected = True
        self.server_info = response.result.get("serverInfo")
        self.server_capabilities = response.result.get("capabilities")

        logger.info(f"Connected to MCP server: {self.server_info.get('name')}")

        return response.result

    async def list_resources(self, server_handler: Any) -> List[Dict[str, Any]]:
        """List available resources from the server"""
        if not self.connected:
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, "Client not connected")

        message = MCPMessage(
            id=self._get_next_message_id(),
            method=MCPMethod.RESOURCES_LIST.value,
            params={}
        )

        response = await server_handler.handle_request(message)

        if response.error:
            raise MCPError(
                response.error.get("code", MCPErrorCode.INTERNAL_ERROR),
                response.error.get("message", "Unknown error")
            )

        return response.result.get("resources", [])

    async def read_resource(
        self,
        server_handler: Any,
        uri: str
    ) -> Dict[str, Any]:
        """Read a resource from the server"""
        if not self.connected:
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, "Client not connected")

        message = MCPMessage(
            id=self._get_next_message_id(),
            method=MCPMethod.RESOURCES_READ.value,
            params={"uri": uri}
        )

        response = await server_handler.handle_request(message)

        if response.error:
            raise MCPError(
                response.error.get("code", MCPErrorCode.INTERNAL_ERROR),
                response.error.get("message", "Unknown error")
            )

        return response.result

    async def subscribe_resource(
        self,
        server_handler: Any,
        uri: str
    ) -> Dict[str, Any]:
        """Subscribe to resource updates"""
        if not self.connected:
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, "Client not connected")

        message = MCPMessage(
            id=self._get_next_message_id(),
            method=MCPMethod.RESOURCES_SUBSCRIBE.value,
            params={"uri": uri}
        )

        response = await server_handler.handle_request(message)

        if response.error:
            raise MCPError(
                response.error.get("code", MCPErrorCode.INTERNAL_ERROR),
                response.error.get("message", "Unknown error")
            )

        logger.info(f"Subscribed to resource: {uri}")
        return response.result

    async def unsubscribe_resource(
        self,
        server_handler: Any,
        uri: str
    ) -> Dict[str, Any]:
        """Unsubscribe from resource updates"""
        if not self.connected:
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, "Client not connected")

        message = MCPMessage(
            id=self._get_next_message_id(),
            method=MCPMethod.RESOURCES_UNSUBSCRIBE.value,
            params={"uri": uri}
        )

        response = await server_handler.handle_request(message)

        if response.error:
            raise MCPError(
                response.error.get("code", MCPErrorCode.INTERNAL_ERROR),
                response.error.get("message", "Unknown error")
            )

        logger.info(f"Unsubscribed from resource: {uri}")
        return response.result

    async def list_tools(self, server_handler: Any) -> List[Dict[str, Any]]:
        """List available tools from the server"""
        if not self.connected:
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, "Client not connected")

        message = MCPMessage(
            id=self._get_next_message_id(),
            method=MCPMethod.TOOLS_LIST.value,
            params={}
        )

        response = await server_handler.handle_request(message)

        if response.error:
            raise MCPError(
                response.error.get("code", MCPErrorCode.INTERNAL_ERROR),
                response.error.get("message", "Unknown error")
            )

        return response.result.get("tools", [])

    async def call_tool(
        self,
        server_handler: Any,
        name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Call a tool on the server"""
        if not self.connected:
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, "Client not connected")

        message = MCPMessage(
            id=self._get_next_message_id(),
            method=MCPMethod.TOOLS_CALL.value,
            params={
                "name": name,
                "arguments": arguments or {}
            }
        )

        response = await server_handler.handle_request(message)

        if response.error:
            raise MCPError(
                response.error.get("code", MCPErrorCode.INTERNAL_ERROR),
                response.error.get("message", "Unknown error")
            )

        return response.result

    async def list_prompts(self, server_handler: Any) -> List[Dict[str, Any]]:
        """List available prompts from the server"""
        if not self.connected:
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, "Client not connected")

        message = MCPMessage(
            id=self._get_next_message_id(),
            method=MCPMethod.PROMPTS_LIST.value,
            params={}
        )

        response = await server_handler.handle_request(message)

        if response.error:
            raise MCPError(
                response.error.get("code", MCPErrorCode.INTERNAL_ERROR),
                response.error.get("message", "Unknown error")
            )

        return response.result.get("prompts", [])

    async def get_prompt(
        self,
        server_handler: Any,
        name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get a prompt from the server"""
        if not self.connected:
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, "Client not connected")

        message = MCPMessage(
            id=self._get_next_message_id(),
            method=MCPMethod.PROMPTS_GET.value,
            params={
                "name": name,
                "arguments": arguments or {}
            }
        )

        response = await server_handler.handle_request(message)

        if response.error:
            raise MCPError(
                response.error.get("code", MCPErrorCode.INTERNAL_ERROR),
                response.error.get("message", "Unknown error")
            )

        return response.result

    def disconnect(self):
        """Disconnect from the server"""
        self.connected = False
        self.server_info = None
        self.server_capabilities = None
        logger.info(f"Disconnected from MCP server")

    def get_client_info(self) -> Dict[str, Any]:
        """Get client information"""
        return {
            "id": self.client_id,
            "name": self.name,
            "version": self.version,
            "connected": self.connected,
            "server_info": self.server_info,
            "server_capabilities": self.server_capabilities
        }
