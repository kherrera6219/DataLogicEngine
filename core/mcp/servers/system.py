"""
System Tools MCP Server

Provides essential system capabilities to the MCP ecosystem:
1. File System Access (read-only, sandboxed)
2. Web Search (wrapper)
3. System Information
"""

import os
import logging

from core.mcp.mcp_server import MCPServer
from core.mcp.mcp_protocol import MCPError, MCPErrorCode

logger = logging.getLogger(__name__)

class SystemServer(MCPServer):
    """
    MCP Server for System Tools
    """

    def __init__(self, name="System", version="1.0.0", root_dir: str = None):
        super().__init__(name, version, description="System utilities (File System, Search)")
        # Default restricted root to current working directory
        self.root_dir = os.path.abspath(root_dir or os.getcwd())
        if not os.path.exists(self.root_dir):
            logger.warning(f"SystemServer root dir does not exist: {self.root_dir}")
        self._register_tools()
        
    def _register_tools(self):
        """Register system tools"""
        
        # --- File System Tools ---

        async def read_file(arguments):
            path = arguments.get("path")
            if not path:
                raise MCPError(MCPErrorCode.INVALID_PARAMS, "Missing 'path'")
            
            # Security check: Ensure path is within root_dir
            abs_path = os.path.abspath(os.path.join(self.root_dir, path))
            if not abs_path.startswith(self.root_dir):
                 raise MCPError(MCPErrorCode.INVALID_PARAMS, "Access denied: Path outside allowed root")
            
            if not os.path.exists(abs_path):
                 raise MCPError(MCPErrorCode.INTERNAL_ERROR, "File not found")
                 
            if not os.path.isfile(abs_path):
                 raise MCPError(MCPErrorCode.INVALID_PARAMS, "Path is not a file")
            
            # Read content
            try:
                with open(abs_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return content
            except UnicodeDecodeError:
                return "<Binary File Content>"
            except Exception as e:
                raise MCPError(MCPErrorCode.INTERNAL_ERROR, f"Error reading file: {str(e)}")

        self.register_tool(
            name="read_file",
            description="Read content of a file (safe restricted access)",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to file"}
                },
                "required": ["path"]
            },
            handler=read_file
        )

        async def list_directory(arguments):
            path = arguments.get("path", ".")
            
            # Security check
            abs_path = os.path.abspath(os.path.join(self.root_dir, path))
            if not abs_path.startswith(self.root_dir):
                 raise MCPError(MCPErrorCode.INVALID_PARAMS, "Access denied: Path outside allowed root")
            
            if not os.path.exists(abs_path):
                 raise MCPError(MCPErrorCode.INTERNAL_ERROR, "Directory not found")
                 
            if not os.path.isdir(abs_path):
                 raise MCPError(MCPErrorCode.INVALID_PARAMS, "Path is not a directory")
            
            try:
                items = []
                for entry in os.scandir(abs_path):
                    items.append({
                        "name": entry.name,
                        "is_dir": entry.is_dir(),
                        "size": entry.stat().st_size if entry.is_file() else 0
                    })
                return items
            except Exception as e:
                raise MCPError(MCPErrorCode.INTERNAL_ERROR, f"Error listing directory: {str(e)}")

        self.register_tool(
            name="list_directory",
            description="List contents of a directory",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to directory"}
                }
            },
            handler=list_directory
        )

        # --- Web Tools ---
        
        async def web_search(arguments):
            query = arguments.get("query")
            
            if not query:
                raise MCPError(MCPErrorCode.INVALID_PARAMS, "Missing 'query'")
                
            # Mock implementation calling a placeholder or public API
            # Ideally, use DuckDuckGo or Google Custom Search API if configured
            try:
                # Placeholder for actual implementation check
                api_key = os.environ.get("SEARCH_API_KEY")
                if not api_key:
                    return f"Simulation: Performed web search for '{query}'. (API Key not configured)"
                
                # If we had an API key, we would make a request here
                # response = requests.get(...)
                return f"Simulation: Real search disabled. Query: {query}"
                
            except Exception as e:
                logger.error(f"Search error: {e}")
                return f"Search failed: {str(e)}"

        self.register_tool(
            name="web_search",
            description="Search the web for information",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "limit": {"type": "integer", "description": "Max results"}
                },
                "required": ["query"]
            },
            handler=web_search
        )

