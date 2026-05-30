"""
MCP Server Implementation

Implements a Model Context Protocol server that can expose resources,
tools, and prompts to LLM applications.
"""

import uuid
import inspect
import time
from typing import Dict, List, Optional, Any, Callable
import logging

from backend.mcp_server.connector_metrics import infer_connector_id, record_connector_execution
from backend.mcp_server.contract_validation import (
    ContractValidationError,
    validate_tool_arguments,
    validate_tool_result,
)
from backend.mcp_server.scope_enforcement import enforce_scopes, parse_execution_context
from .mcp_protocol import (
    MCPResource, MCPTool, MCPPrompt,
    MCPServerInfo, MCPCapabilities, MCPMethod,
    MCPRequestHandler, MCPError, MCPErrorCode,
    MCPMessage
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
        self.client_callback = None

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

    def register_client_callback(self, callback: Callable):
        """Register a callback to send requests/notifications to the client"""
        self.client_callback = callback

    async def sample_completions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Request model completions from the connected client (sampling)"""
        if not self.client_callback:
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, "No client callback registered for sampling")

        message = MCPMessage(
            method=MCPMethod.SAMPLING_CREATE_MESSAGE.value,
            params=params
        )
        response = await self.client_callback(message)
        if response.error:
            raise MCPError(
                response.error.get("code", MCPErrorCode.INTERNAL_ERROR),
                response.error.get("message", "Sampling failed")
            )
        return response.result

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

        # Track subscription
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
        context_payload = params.get("context", {})

        if not tool_name:
            raise MCPError(MCPErrorCode.INVALID_PARAMS, "Missing 'name' parameter")

        if tool_name not in self.tool_handlers:
            raise MCPError(MCPErrorCode.TOOL_NOT_FOUND, f"Tool not found: {tool_name}")

        tool_definition = self.tools[tool_name]
        required_scopes = tool_definition.metadata.get("required_scopes", [])
        execution_context = parse_execution_context(context_payload)
        enforce_scopes(
            tool_name=tool_name,
            required_scopes=required_scopes,
            context=execution_context,
            permissive_on_missing_context=True,
        )
        try:
            validate_tool_arguments(tool_name, tool_definition.input_schema, arguments)
        except ContractValidationError as exc:
            raise MCPError(MCPErrorCode.INVALID_PARAMS, str(exc)) from exc

        started = time.perf_counter()
        success = False
        try:
            handler = self.tool_handlers[tool_name]
            call_arguments = dict(arguments or {})
            try:
                signature = inspect.signature(handler)
                if "_execution_context" in signature.parameters and "_execution_context" not in call_arguments:
                    call_arguments["_execution_context"] = execution_context.to_dict()
            except (ValueError, TypeError):
                pass

            handler_result = handler(call_arguments)
            if inspect.isawaitable(handler_result):
                result = await handler_result
            else:
                result = handler_result
            try:
                validate_tool_result(tool_name, tool_definition.metadata.get("output_schema"), result)
            except ContractValidationError as exc:
                raise MCPError(MCPErrorCode.TOOL_EXECUTION_ERROR, str(exc)) from exc
            success = True

            # Audit Log (Enterprise)
            try:
                from extensions import audit_logger
                if audit_logger:
                    audit_logger.log_event(
                        event_type='mcp_tool_execution',
                        user_id='system',
                        details={
                            'server': self.name,
                            'tool': tool_name,
                            'arguments': str(arguments),
                            'status': 'success'
                        },
                        ip_address='127.0.0.1'
                    )
            except Exception as audit_err:
                logger.warning(f"Failed to audit tool call: {audit_err}")

            return {
                "content": [
                    {
                        "type": "text",
                        "text": str(result)
                    }
                ]
            }
        except Exception as e:
            # Audit Log Failure
            try:
                from extensions import audit_logger
                if audit_logger:
                    audit_logger.log_event(
                        event_type='mcp_tool_execution',
                        user_id='system',
                        details={
                            'server': self.name,
                            'tool': tool_name,
                            'arguments': str(arguments),
                            'status': 'failure',
                            'error': str(e)
                        },
                        ip_address='127.0.0.1'
                    )
            except Exception:
                pass

            logger.error(f"Tool execution error ({tool_name}): {e}")
            raise MCPError(MCPErrorCode.TOOL_EXECUTION_ERROR, f"Tool execution failed: {str(e)}")
        finally:
            record_connector_execution(
                tool_name=tool_name,
                connector_id=infer_connector_id(
                    tool_name,
                    declared_connector=tool_definition.metadata.get("connector"),
                ),
                duration_ms=(time.perf_counter() - started) * 1000.0,
                success=success,
            )

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
            logger.info(f"Resource updated notification: {uri}")
            # Dynamic notifications support
            if self.client_callback:
                try:
                    notification = MCPMessage(
                        method=MCPMethod.RESOURCES_UPDATED.value,
                        params={"uri": uri}
                    )
                    await self.client_callback(notification)
                except Exception as e:
                    logger.warning(f"Failed to send JSON-RPC update notification for {uri}: {e}")

        # Also trigger the global SSE subscription manager
        try:
            from backend.mcp_server.subscriptions import subscription_manager
            subscription_manager.notify(uri, {"updated": True})
        except Exception as e:
            logger.warning(f"Failed to notify global subscription_manager: {e}")

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
