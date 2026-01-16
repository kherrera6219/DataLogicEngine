"""
MCP Protocol Base Classes and Utilities

Implements the core Model Context Protocol specification for
standardized communication between LLM applications and integrations.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime


class MCPMessageType(Enum):
    """MCP message types"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


class MCPMethod(Enum):
    """Standard MCP methods"""
    # Initialization
    INITIALIZE = "initialize"
    INITIALIZED = "initialized"

    # Resources
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    RESOURCES_SUBSCRIBE = "resources/subscribe"
    RESOURCES_UNSUBSCRIBE = "resources/unsubscribe"

    # Tools
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"

    # Prompts
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"

    # Completion
    COMPLETION_COMPLETE = "completion/complete"

    # Logging
    LOGGING_SET_LEVEL = "logging/setLevel"

    # Sampling
    SAMPLING_CREATE_MESSAGE = "sampling/createMessage"

    # Notifications
    PROGRESS = "notifications/progress"
    MESSAGE = "notifications/message"
    RESOURCES_UPDATED = "notifications/resources/updated"
    TOOLS_UPDATED = "notifications/tools/updated"
    PROMPTS_UPDATED = "notifications/prompts/updated"


@dataclass
class MCPCapabilities:
    """MCP server/client capabilities"""
    resources: bool = False
    tools: bool = False
    prompts: bool = False
    logging: bool = False
    experimental: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPServerInfo:
    """MCP server information"""
    name: str
    version: str
    protocol_version: str = "2024-11-05"
    capabilities: MCPCapabilities = field(default_factory=MCPCapabilities)


@dataclass
class MCPClientInfo:
    """MCP client information"""
    name: str
    version: str
    protocol_version: str = "2024-11-05"


@dataclass
class MCPResource:
    """MCP resource definition"""
    uri: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPTool:
    """MCP tool definition"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPPrompt:
    """MCP prompt template"""
    name: str
    description: str
    arguments: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPMessage:
    """Base MCP message"""
    jsonrpc: str = "2.0"
    id: Optional[str] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        msg = {"jsonrpc": self.jsonrpc}
        if self.id is not None:
            msg["id"] = self.id
        if self.method is not None:
            msg["method"] = self.method
        if self.params is not None:
            msg["params"] = self.params
        if self.result is not None:
            msg["result"] = self.result
        if self.error is not None:
            msg["error"] = self.error
        return msg

    def to_json(self) -> str:
        """Convert message to JSON string"""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPMessage':
        """Create message from dictionary"""
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            method=data.get("method"),
            params=data.get("params"),
            result=data.get("result"),
            error=data.get("error")
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'MCPMessage':
        """Create message from JSON string"""
        return cls.from_dict(json.loads(json_str))


class MCPError(Exception):
    """Base MCP error"""
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary"""
        error = {"code": self.code, "message": self.message}
        if self.data is not None:
            error["data"] = self.data
        return error


class MCPErrorCode:
    """Standard JSON-RPC error codes"""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # MCP-specific errors
    RESOURCE_NOT_FOUND = -32001
    TOOL_NOT_FOUND = -32002
    PROMPT_NOT_FOUND = -32003
    TOOL_EXECUTION_ERROR = -32004


class MCPRequestHandler:
    """Base class for handling MCP requests"""

    def __init__(self):
        self.handlers: Dict[str, Callable] = {}

    def register_handler(self, method: str, handler: Callable):
        """Register a method handler"""
        self.handlers[method] = handler

    async def handle_request(self, message: MCPMessage) -> MCPMessage:
        """Handle an incoming MCP request"""
        if message.method not in self.handlers:
            error = MCPError(
                MCPErrorCode.METHOD_NOT_FOUND,
                f"Method not found: {message.method}"
            )
            return MCPMessage(
                id=message.id,
                error=error.to_dict()
            )

        try:
            handler = self.handlers[message.method]
            result = await handler(message.params or {})
            return MCPMessage(
                id=message.id,
                result=result
            )
        except MCPError as e:
            return MCPMessage(
                id=message.id,
                error=e.to_dict()
            )
        except Exception as e:
            error = MCPError(
                MCPErrorCode.INTERNAL_ERROR,
                str(e)
            )
            return MCPMessage(
                id=message.id,
                error=error.to_dict()
            )
