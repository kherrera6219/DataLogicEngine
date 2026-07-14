"""
MCP Router (JSON-RPC 2.0)
------------------------
Handles incoming MCP requests and routes them to the Tool Registry.
"""

import logging
from typing import Dict, Any
from backend.mcp_server.registry import registry
from backend.mcp_server.sampling import MCPSamplingService
from backend.mcp_server.subscriptions import MCPSubscriptionManager
from backend.mcp_server.policy import SUPPORTED_MCP_PROTOCOL_VERSION

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
    
    def __init__(self, *, tool_registry=None, sampling_service=None, subscription_manager=None):
        self.registry = tool_registry or registry
        self.sampling_service = sampling_service or MCPSamplingService()
        self.subscription_manager = subscription_manager or MCPSubscriptionManager()

    async def handle_message(
        self,
        message: Dict[str, Any],
        *,
        execution_context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Process an incoming JSON-RPC message."""
        if not isinstance(message, dict):
            return self._error(None, -32600, "Invalid Request")
        if message.get("jsonrpc", "2.0") != "2.0":
            return self._error(message.get("id"), -32600, "Invalid Request: jsonrpc must be 2.0")

        request_id = message.get("id")
        method = message.get("method")
        params = message.get("params", {})

        if not method:
            return self._error(request_id, -32600, "Invalid Request: method is required")

        # MCP Handshake
        if method == "initialize":
            return self._response(request_id, {
                "protocolVersion": SUPPORTED_MCP_PROTOCOL_VERSION,
                "serverInfo": {
                    "name": "DataLogicEngine-UKG",
                    "version": "1.0.0"
                },
                "capabilities": {
                    "tools": {},
                }
            })

        if not isinstance(execution_context, dict) or not str(execution_context.get("user_id") or "").strip():
            return self._error(request_id, -32001, "Authenticated server-owned context is required")

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
