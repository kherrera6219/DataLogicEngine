"""
MCP Tool Registry
----------------
Manages the registration, discovery, and execution of MCP tools.
"""

import logging
import inspect
from typing import Dict, Any, Callable, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._definitions: Dict[str, ToolDefinition] = {}

    def register(self, name: str, description: str, input_schema: Dict[str, Any]):
        """Decorator to register a function as an MCP tool."""
        def decorator(func: Callable):
            self._tools[name] = func
            self._definitions[name] = ToolDefinition(
                name=name,
                description=description,
                input_schema=input_schema
            )
            logger.info(f"Registered MCP Tool: {name}")
            return func
        return decorator

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return list of available tools in MCP format."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "inputSchema": t.input_schema
            }
            for t in self._definitions.values()
        ]

    def get_tool(self, name: str) -> Optional[Callable]:
        return self._tools.get(name)

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        tool_func = self.get_tool(name)
        if not tool_func:
            raise ValueError(f"Tool not found: {name}")
        
        try:
            # Handle both async and sync tools
            if inspect.iscoroutinefunction(tool_func):
                return await tool_func(**arguments)
            else:
                return tool_func(**arguments)
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            raise e

# Global Registry Instance
registry = ToolRegistry()
