"""
System Tools MCP Server

Provides essential system capabilities to the MCP ecosystem:
1. File System Access (read-only, sandboxed)
2. Web Search (wrapper)
3. System Information
"""

import logging
from pathlib import Path

from core.mcp.mcp_server import MCPServer
from core.mcp.mcp_protocol import MCPError, MCPErrorCode

logger = logging.getLogger(__name__)

class SystemServer(MCPServer):
    """
    MCP Server for System Tools
    """

    def __init__(self, name="System", version="1.0.0", root_dir: str = None):
        super().__init__(name, version, description="System utilities (File System, Search)")
        # Default restricted root to current working directory.
        self.root_dir = Path(root_dir or Path.cwd()).resolve(strict=True)
        if not self.root_dir.exists():
            logger.warning(f"SystemServer root dir does not exist: {self.root_dir}")
        self._register_tools()

    def _resolve_path(self, raw_path: str) -> Path:
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = self.root_dir / candidate
        try:
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(self.root_dir)
        except (OSError, ValueError) as exc:
            raise MCPError(MCPErrorCode.INVALID_PARAMS, "Access denied: Path outside allowed root") from exc
        return resolved
        
    def _register_tools(self):
        """Register system tools"""
        
        # --- File System Tools ---

        async def read_file(arguments):
            path = arguments.get("path")
            if not path:
                raise MCPError(MCPErrorCode.INVALID_PARAMS, "Missing 'path'")
            
            # Security check: Ensure path is within root_dir
            abs_path = self._resolve_path(path)
            if not abs_path.is_file():
                 raise MCPError(MCPErrorCode.INVALID_PARAMS, "Path is not a file")
            
            # Read content
            try:
                with abs_path.open('r', encoding='utf-8') as f:
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
            handler=read_file,
            metadata={
                "connector": "filesystem",
                "required_scopes": ["mcp:execute", "connector:filesystem:read"],
            },
        )

        async def list_directory(arguments):
            path = arguments.get("path", ".")
            
            # Security check
            abs_path = self._resolve_path(path)
            if not abs_path.is_dir():
                 raise MCPError(MCPErrorCode.INVALID_PARAMS, "Path is not a directory")
            
            try:
                items = []
                for entry in abs_path.iterdir():
                    items.append({
                        "name": entry.name,
                        "is_dir": entry.is_dir(),
                        "size": entry.stat().st_size if entry.is_file() else 0,
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
            handler=list_directory,
            metadata={
                "connector": "filesystem",
                "required_scopes": ["mcp:execute", "connector:filesystem:read"],
            },
        )

