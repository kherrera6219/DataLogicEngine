"""MCP helpers (Model Context Protocol).

This module is intentionally thin: it provides interface types only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class MCPToolCall:
    name: str
    arguments: Dict[str, Any]


@dataclass
class MCPResult:
    content: Any
    metadata: Optional[Dict[str, Any]] = None
