"""
Model Context Protocol (MCP) Core Module

This module implements the Model Context Protocol for DataLogicEngine,
enabling integration with LLM applications through standardized
server/client communication.
"""

from .mcp_server import MCPServer
from .mcp_client import MCPClient
from .mcp_manager import MCPManager

__all__ = ['MCPServer', 'MCPClient', 'MCPManager']
