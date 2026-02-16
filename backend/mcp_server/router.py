"""
MCP Router (JSON-RPC 2.0)
------------------------
Handles incoming MCP requests and routes them to the Tool Registry.
"""

import logging
from typing import Dict, Any, List
from backend.mcp_server.registry import registry

logger = logging.getLogger(__name__)

class MCPRouter:
    """
    Handles JSON-RPC 2.0 messages for the Model Context Protocol.
    """
    
    def __init__(self):
        self.registry = registry

    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
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
                    "resources": {}
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
            context = params.get("context", {})
            try:
                result = await self.registry.execute_tool(name, args, context=context)
                return self._response(request_id, {
                    "content": [
                        {
                            "type": "text",
                            "text": str(result)
                        }
                    ]
                })
            except Exception as e:
                return self._error(request_id, -32603, str(e))

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
