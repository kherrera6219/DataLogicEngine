"""
MCP Tool Registry
----------------
Manages the registration, discovery, and execution of MCP tools.
"""

import inspect
import logging
import time
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel

from backend.mcp_server.connector_metrics import record_connector_execution
from backend.mcp_server.contract_validation import validate_tool_arguments, validate_tool_result
from backend.mcp_server.scope_enforcement import (
    ExecutionContext,
    enforce_scopes,
    parse_execution_context,
)

logger = logging.getLogger(__name__)


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]] = None
    required_scopes: List[str] = []
    connector: Optional[str] = None


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._definitions: Dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        output_schema: Optional[Dict[str, Any]] = None,
        required_scopes: Optional[List[str]] = None,
        connector: Optional[str] = None,
    ):
        """Decorator to register a function as an MCP tool."""

        def decorator(func: Callable):
            self._tools[name] = func
            self._definitions[name] = ToolDefinition(
                name=name,
                description=description,
                input_schema=input_schema,
                output_schema=output_schema,
                required_scopes=required_scopes or [],
                connector=connector,
            )
            logger.info("Registered MCP Tool: %s", name)
            return func

        return decorator

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return list of available tools in MCP format."""
        return [
            {
                "name": definition.name,
                "description": definition.description,
                "inputSchema": definition.input_schema,
                "outputSchema": definition.output_schema,
                "requiredScopes": definition.required_scopes,
                "connector": definition.connector,
            }
            for definition in self._definitions.values()
        ]

    def get_tool(self, name: str) -> Optional[Callable]:
        return self._tools.get(name)

    def get_definition(self, name: str) -> Optional[ToolDefinition]:
        return self._definitions.get(name)

    @staticmethod
    def _build_call_arguments(
        tool_func: Callable,
        arguments: Dict[str, Any],
        execution_context: ExecutionContext,
    ) -> Dict[str, Any]:
        payload = dict(arguments or {})
        try:
            signature = inspect.signature(tool_func)
            if "_execution_context" in signature.parameters and "_execution_context" not in payload:
                payload["_execution_context"] = execution_context.to_dict()
        except (ValueError, TypeError):
            # Some callables do not expose signatures.
            pass
        return payload

    async def execute_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        tool_func = self.get_tool(name)
        tool_definition = self.get_definition(name)
        if not tool_func or not tool_definition:
            raise ValueError(f"Tool not found: {name}")

        execution_context = parse_execution_context(context)
        enforce_scopes(
            tool_name=name,
            required_scopes=tool_definition.required_scopes,
            context=execution_context,
            permissive_on_missing_context=False,
        )
        raw_arguments = arguments if isinstance(arguments, dict) else {}
        validate_tool_arguments(name, tool_definition.input_schema, raw_arguments)
        call_arguments = self._build_call_arguments(tool_func, raw_arguments, execution_context)

        started = time.perf_counter()
        success = False
        try:
            # Handle both async and sync tools
            if inspect.iscoroutinefunction(tool_func):
                result = await tool_func(**call_arguments)
            else:
                result = tool_func(**call_arguments)
            validate_tool_result(name, tool_definition.output_schema, result)
            success = True
            return result
        except Exception as e:
            logger.error("Error executing tool %s: %s", name, e)
            raise e
        finally:
            record_connector_execution(
                tool_name=name,
                connector_id=tool_definition.connector,
                duration_ms=(time.perf_counter() - started) * 1000.0,
                success=success,
            )


# Global Registry Instance
registry = ToolRegistry()
