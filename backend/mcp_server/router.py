"""
MCP Router (JSON-RPC 2.0)
------------------------
Handles incoming MCP requests and routes them to the Tool Registry.
"""

import logging
from typing import Dict, Any
from backend.mcp_server.registry import registry
from backend.mcp_server.sampling import sampling_service
from backend.mcp_server.subscriptions import subscription_manager

logger = logging.getLogger(__name__)


def _safe_error_message(exc: Exception) -> str:
    """Return a public-safe message for MCP tool execution failures."""
    text = str(exc).strip()
    if not text:
        return "Tool execution failed"
    lowered = text.lower()
    sensitive_markers = (
        "traceback",
        "password",
        "secret",
        "token",
        "api key",
        "database",
        "connection refused",
    )
    if any(marker in lowered for marker in sensitive_markers):
        return "Tool execution failed"
    return text[:240]

class MCPRouter:
    """
    Handles JSON-RPC 2.0 messages for the Model Context Protocol.
    """
    
    def __init__(self):
        self.registry = registry

    async def handle_message(
        self,
        message: Dict[str, Any],
        *,
        execution_context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Process an incoming JSON-RPC message."""
        if not isinstance(message, dict):
            return self._error(None, -32600, "Invalid Request")

        request_id = message.get("id")
        method = message.get("method")
        params = message.get("params", {})

        if not method:
            return self._error(request_id, -32600, "Invalid Request: method is required")

        # MCP Handshake
        if method == "initialize":
            return self._response(request_id, {
                "protocolVersion": "0.1.0",
                "serverInfo": {
                    "name": "DataLogicEngine-UKG",
                    "version": "1.0.0"
                },
                "capabilities": {
                    "tools": {},
                    "resources": {"subscribe": True},
                    "sampling": {}
                }
            })

        # Tool Discovery
        if method == "tools/list":
            tools = self.registry.list_tools()
            return self._response(request_id, {
                "tools": tools
            })

        # Tool Execution
        if method == "tools/call":
            name = params.get("name")
            args = params.get("arguments", {})
            try:
                result = await self.registry.execute_tool(
                    name,
                    args,
                    context=execution_context or {},
                )
                return self._response(request_id, {
                    "content": [
                        {
                            "type": "text",
                            "text": str(result)
                        }
                    ]
                })
            except Exception as e:
                logger.exception("MCP tools/call failed for tool=%s", name)
                return self._error(request_id, -32603, _safe_error_message(e))

        if method == "sampling/createMessage":
            try:
                return self._response(request_id, await sampling_service.create_message(params))
            except Exception as e:
                logger.exception("MCP sampling/createMessage failed")
                return self._error(request_id, -32603, _safe_error_message(e))

        if method == "resources/subscribe":
            uri = params.get("uri")
            if not uri:
                return self._error(request_id, -32602, "Missing required parameter: uri")
            return self._response(request_id, subscription_manager.subscribe(uri, client_id=params.get("clientId")))

        if method == "resources/unsubscribe":
            subscription_id = params.get("subscriptionId")
            if not subscription_id:
                return self._error(request_id, -32602, "Missing required parameter: subscriptionId")
            return self._response(request_id, {"unsubscribed": subscription_manager.unsubscribe(subscription_id)})

        return self._error(request_id, -32601, f"Method not found: {method}")

    def _response(self, request_id: Any, result: Any) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }

    def _error(self, request_id: Any, code: int, message: str) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }
