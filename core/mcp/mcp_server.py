"""
MCP Server Implementation

Implements a Model Context Protocol server that can expose resources,
tools, and prompts to LLM applications.
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import logging

from .mcp_protocol import (
    MCPMessage, MCPResource, MCPTool, MCPPrompt,
    MCPServerInfo, MCPCapabilities, MCPMethod,
    MCPRequestHandler, MCPError, MCPErrorCode
)


logger = logging.getLogger(__name__)


class MCPServer(MCPRequestHandler):
    """
    MCP Server implementation for DataLogicEngine

    Exposes knowledge graph resources, tools, and prompts via MCP protocol
    """

    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        description: Optional[str] = None
    ):
        super().__init__()
        self.name = name
        self.version = version
        self.description = description or f"DataLogicEngine MCP Server: {name}"

        # Server state
        self.server_id = str(uuid.uuid4())
        self.initialized = False
        self.client_info = None

        # Resource, tool, and prompt registries
        self.resources: Dict[str, MCPResource] = {}
        self.resource_handlers: Dict[str, Callable] = {}
        self.tools: Dict[str, MCPTool] = {}
        self.tool_handlers: Dict[str, Callable] = {}
        self.prompts: Dict[str, MCPPrompt] = {}
        self.prompt_handlers: Dict[str, Callable] = {}

        # Subscriptions
        self.resource_subscriptions: Dict[str, List[str]] = {}

        # Initialize capabilities
        self.capabilities = MCPCapabilities(
            resources=True,
            tools=True,
            prompts=True,
            logging=True,
            experimental={
                "ukg_integration": True,
                "simulation_engine": True,
                "knowledge_algorithms": True
            }
        )

        # Register standard handlers
        self._register_standard_handlers()

    def _register_standard_handlers(self):
        """Register standard MCP method handlers"""
        self.register_handler(MCPMethod.INITIALIZE.value, self._handle_initialize)
        self.register_handler(MCPMethod.RESOURCES_LIST.value, self._handle_resources_list)
        self.register_handler(MCPMethod.RESOURCES_READ.value, self._handle_resources_read)
        self.register_handler(MCPMethod.RESOURCES_SUBSCRIBE.value, self._handle_resources_subscribe)
        self.register_handler(MCPMethod.RESOURCES_UNSUBSCRIBE.value, self._handle_resources_unsubscribe)
        self.register_handler(MCPMethod.TOOLS_LIST.value, self._handle_tools_list)
        self.register_handler(MCPMethod.TOOLS_CALL.value, self._handle_tools_call)
        self.register_handler(MCPMethod.PROMPTS_LIST.value, self._handle_prompts_list)
        self.register_handler(MCPMethod.PROMPTS_GET.value, self._handle_prompts_get)

    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialization request"""
        self.client_info = params.get("clientInfo")
        self.initialized = True

        logger.info(f"MCP Server '{self.name}' initialized with client: {self.client_info}")

        server_info = MCPServerInfo(
            name=self.name,
            version=self.version,
            capabilities=self.capabilities
        )

        return {
            "protocolVersion": server_info.protocol_version,
            "capabilities": {
                "resources": {"subscribe": True} if self.capabilities.resources else None,
                "tools": {} if self.capabilities.tools else None,
                "prompts": {} if self.capabilities.prompts else None,
                "logging": {} if self.capabilities.logging else None,
                "experimental": self.capabilities.experimental
            },
            "serverInfo": {
                "name": server_info.name,
                "version": server_info.version
            }
        }

    async def _handle_resources_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources list request"""
        resources = [
            {
                "uri": resource.uri,
                "name": resource.name,
                "description": resource.description,
                "mimeType": resource.mime_type,
                "metadata": resource.metadata
            }
            for resource in self.resources.values()
        ]

        return {"resources": resources}

    async def _handle_resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resource read request"""
        uri = params.get("uri")
        if not uri:
            raise MCPError(MCPErrorCode.INVALID_PARAMS, "Missing 'uri' parameter")

        if uri not in self.resource_handlers:
            raise MCPError(MCPErrorCode.RESOURCE_NOT_FOUND, f"Resource not found: {uri}")

        handler = self.resource_handlers[uri]
        content = await handler(params)

        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": self.resources[uri].mime_type or "text/plain",
                    "text": content if isinstance(content, str) else str(content)
                }
            ]
        }

    async def _handle_resources_subscribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resource subscription request"""
        uri = params.get("uri")
        if not uri:
            raise MCPError(MCPErrorCode.INVALID_PARAMS, "Missing 'uri' parameter")

        if uri not in self.resources:
            raise MCPError(MCPErrorCode.RESOURCE_NOT_FOUND, f"Resource not found: {uri}")

        # Track subscription (in production, you'd track by client/session)
        if uri not in self.resource_subscriptions:
            self.resource_subscriptions[uri] = []

        logger.info(f"Resource subscribed: {uri}")
        return {}

    async def _handle_resources_unsubscribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resource unsubscription request"""
        uri = params.get("uri")
        if not uri:
            raise MCPError(MCPErrorCode.INVALID_PARAMS, "Missing 'uri' parameter")

        if uri in self.resource_subscriptions:
            del self.resource_subscriptions[uri]

        logger.info(f"Resource unsubscribed: {uri}")
        return {}

    async def _handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools list request"""
        tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema,
                "metadata": tool.metadata
            }
            for tool in self.tools.values()
        ]

        return {"tools": tools}

    async def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool call request"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if not tool_name:
            raise MCPError(MCPErrorCode.INVALID_PARAMS, "Missing 'name' parameter")

        if tool_name not in self.tool_handlers:
            raise MCPError(MCPErrorCode.TOOL_NOT_FOUND, f"Tool not found: {tool_name}")

        try:
            handler = self.tool_handlers[tool_name]
            result = await handler(arguments)

            return {
                "content": [
                    {
                        "type": "text",
                        "text": str(result)
                    }
                ]
            }
        except Exception as e:
            logger.error(f"Tool execution error ({tool_name}): {e}")
            raise MCPError(MCPErrorCode.TOOL_EXECUTION_ERROR, f"Tool execution failed: {str(e)}")

    async def _handle_prompts_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts list request"""
        prompts = [
            {
                "name": prompt.name,
                "description": prompt.description,
                "arguments": prompt.arguments,
                "metadata": prompt.metadata
            }
            for prompt in self.prompts.values()
        ]

        return {"prompts": prompts}

    async def _handle_prompts_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompt get request"""
        prompt_name = params.get("name")
        arguments = params.get("arguments", {})

        if not prompt_name:
            raise MCPError(MCPErrorCode.INVALID_PARAMS, "Missing 'name' parameter")

        if prompt_name not in self.prompt_handlers:
            raise MCPError(MCPErrorCode.PROMPT_NOT_FOUND, f"Prompt not found: {prompt_name}")

        handler = self.prompt_handlers[prompt_name]
        messages = await handler(arguments)

        return {
            "description": self.prompts[prompt_name].description,
            "messages": messages
        }

    # Public API for registering resources, tools, and prompts

    def register_resource(
        self,
        uri: str,
        name: str,
        handler: Callable,
        description: Optional[str] = None,
        mime_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Register a resource with the MCP server"""
        resource = MCPResource(
            uri=uri,
            name=name,
            description=description,
            mime_type=mime_type,
            metadata=metadata or {}
        )
        self.resources[uri] = resource
        self.resource_handlers[uri] = handler
        logger.info(f"Registered resource: {uri}")

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Register a tool with the MCP server"""
        tool = MCPTool(
            name=name,
            description=description,
            input_schema=input_schema,
            metadata=metadata or {}
        )
        self.tools[name] = tool
        self.tool_handlers[name] = handler
        logger.info(f"Registered tool: {name}")

    def register_prompt(
        self,
        name: str,
        description: str,
        handler: Callable,
        arguments: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Register a prompt template with the MCP server"""
        prompt = MCPPrompt(
            name=name,
            description=description,
            arguments=arguments or [],
            metadata=metadata or {}
        )
        self.prompts[name] = prompt
        self.prompt_handlers[name] = handler
        logger.info(f"Registered prompt: {name}")

    async def notify_resource_updated(self, uri: str):
        """Notify subscribers that a resource has been updated"""
        if uri in self.resource_subscriptions:
            # In a full implementation, this would send notifications to subscribed clients
            logger.info(f"Resource updated notification: {uri}")

    def get_server_info(self) -> Dict[str, Any]:
        """Get server information"""
        return {
            "id": self.server_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "initialized": self.initialized,
            "capabilities": {
                "resources": self.capabilities.resources,
                "tools": self.capabilities.tools,
                "prompts": self.capabilities.prompts,
                "logging": self.capabilities.logging,
                "experimental": self.capabilities.experimental
            },
            "stats": {
                "resources": len(self.resources),
                "tools": len(self.tools),
                "prompts": len(self.prompts),
                "subscriptions": len(self.resource_subscriptions)
            }
        }
