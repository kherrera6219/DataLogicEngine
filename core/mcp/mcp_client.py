"""
MCP Client Implementation

Implements a Model Context Protocol client that can connect to
MCP servers and access their resources, tools, and prompts.
Supports both in-memory servers and dynamic stdio subprocesses.
"""

import asyncio
import uuid
import json
import logging
from typing import Dict, List, Optional, Any, Callable

from .mcp_protocol import (
    MCPMessage, MCPClientInfo, MCPMethod,
    MCPError, MCPErrorCode, MCPRequestHandler
)


logger = logging.getLogger(__name__)


class MCPClient(MCPRequestHandler):
    """
    MCP Client implementation for DataLogicEngine

    Connects to MCP servers to access resources, tools, and prompts.
    Supports in-memory and subprocess stdio transport topologies.
    """

    def __init__(
        self,
        name: str = "DataLogicEngine",
        version: str = "1.0.0"
    ):
        super().__init__()
        self.name = name
        self.version = version
        self.client_id = str(uuid.uuid4())

        # Connection state
        self.connected = False
        self.server_info = None
        self.server_capabilities = None

        # Request tracking
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.message_id_counter = 0

        # Subscriptions
        self.resource_updated_callbacks: List[Callable] = []

        # Stdio process tracking
        self.process: Optional[asyncio.subprocess.Process] = None
        self.read_task: Optional[asyncio.Task] = None
        self.stderr_task: Optional[asyncio.Task] = None

        # Register protocol handlers
        self.register_handler(MCPMethod.SAMPLING_CREATE_MESSAGE.value, self._handle_sampling_create_message)
        self.register_handler(MCPMethod.RESOURCES_UPDATED.value, self._handle_resources_updated)

        logger.info(f"MCP Client '{self.name}' created with ID: {self.client_id}")

    def _get_next_message_id(self) -> str:
        """Generate next message ID"""
        self.message_id_counter += 1
        return f"{self.client_id}-{self.message_id_counter}"

    async def connect_via_stdio(self, command: List[str], env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Connect to an external MCP server via standard I/O (stdio) transport"""
        import os
        sub_env = dict(os.environ)
        if env:
            sub_env.update(env)

        # Resolve npx command on Windows
        exec_cmd = command
        if os.name == 'nt' and command and command[0] == 'npx':
            exec_cmd = ['cmd.exe', '/c'] + command

        try:
            self.process = await asyncio.create_subprocess_exec(
                *exec_cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=sub_env
            )
        except Exception as e:
            logger.error(f"Failed to spawn external MCP server process: {e}")
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, f"Process spawn failed: {e}")

        self.connected = True
        
        # Start stdio background readers
        self.read_task = asyncio.create_task(self._read_loop())
        self.stderr_task = asyncio.create_task(self._stderr_loop())

        # Send initialize handshake request
        client_info = MCPClientInfo(name=self.name, version=self.version)
        init_msg = MCPMessage(
            id=self._get_next_message_id(),
            method=MCPMethod.INITIALIZE.value,
            params={
                "protocolVersion": client_info.protocol_version,
                "capabilities": {},
                "clientInfo": {
                    "name": client_info.name,
                    "version": client_info.version
                }
            }
        )

        try:
            response = await self._send_request(init_msg)
            self.server_info = response.result.get("serverInfo")
            self.server_capabilities = response.result.get("capabilities")
            logger.info(f"Connected via stdio to external MCP server: {self.server_info.get('name') if self.server_info else 'Unknown'}")
            
            # Send initialized notification (standard protocol message)
            initialized_msg = MCPMessage(
                method=MCPMethod.INITIALIZED.value,
                params={}
            )
            await self._write_message(initialized_msg)
            
            return response.result
        except Exception as e:
            self.disconnect()
            raise e

    async def _send_request(self, message: MCPMessage) -> MCPMessage:
        """Route request through external stdio process"""
        if not self.connected:
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, "Client not connected")

        if self.process:
            loop = asyncio.get_running_loop()
            future = loop.create_future()
            self.pending_requests[message.id] = future
            await self._write_message(message)
            return await future
        
        raise MCPError(MCPErrorCode.INTERNAL_ERROR, "No external subprocess transport active")

    async def _read_loop(self):
        """Stdout reading loop for JSON-RPC messages from external server"""
        while self.connected and self.process and self.process.stdout:
            try:
                line = await self.process.stdout.readline()
                if not line:
                    break
                data = json.loads(line.decode("utf-8").strip())
                await self._handle_incoming_message(data)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in stdio stdout read loop: {e}")
        self.disconnect()

    async def _stderr_loop(self):
        """Stderr reading loop to capture external server logging output"""
        while self.connected and self.process and self.process.stderr:
            try:
                line = await self.process.stderr.readline()
                if not line:
                    break
                err_msg = line.decode("utf-8", errors="replace").strip()
                logger.warning(f"[MCP-Server-Stderr] {err_msg}")
            except asyncio.CancelledError:
                break
            except Exception:
                break

    async def _handle_incoming_message(self, data: Dict[str, Any]):
        """Parse and route messages received from external server"""
        msg_id = data.get("id")
        method = data.get("method")

        if "result" in data or "error" in data:
            # Response to a client request
            if msg_id in self.pending_requests:
                future = self.pending_requests.pop(msg_id)
                if not future.done():
                    future.set_result(MCPMessage.from_dict(data))
        elif method:
            # Request or notification from server
            msg = MCPMessage.from_dict(data)
            response = await self.handle_request(msg)
            if msg_id is not None:
                await self._write_message(response)

    async def _write_message(self, message: MCPMessage):
        """Write JSON-RPC message to process stdin"""
        if self.process and self.process.stdin:
            try:
                payload = message.to_json() + "\n"
                self.process.stdin.write(payload.encode("utf-8"))
                await self.process.stdin.drain()
            except Exception as e:
                logger.error(f"Failed to write stdio message: {e}")

    async def initialize(self, server_handler: Any) -> Dict[str, Any]:
        """Initialize connection with an in-memory MCP server"""
        client_info = MCPClientInfo(
            name=self.name,
            version=self.version
        )

        message = MCPMessage(
            id=self._get_next_message_id(),
            method=MCPMethod.INITIALIZE.value,
            params={
                "protocolVersion": client_info.protocol_version,
                "capabilities": {},
                "clientInfo": {
                    "name": client_info.name,
                    "version": client_info.version
                }
            }
        )

        response = await server_handler.handle_request(message)

        if response.error:
            raise MCPError(
                response.error.get("code", MCPErrorCode.INTERNAL_ERROR),
                response.error.get("message", "Unknown error")
            )

        self.connected = True
        self.server_info = response.result.get("serverInfo")
        self.server_capabilities = response.result.get("capabilities")

        logger.info(f"Connected to in-memory MCP server: {self.server_info.get('name')}")

        return response.result

    async def list_resources(self, server_handler: Any = None) -> List[Dict[str, Any]]:
        """List available resources from the server"""
        if not self.connected:
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, "Client not connected")

        message = MCPMessage(
            id=self._get_next_message_id(),
            method=MCPMethod.RESOURCES_LIST.value,
            params={}
        )

        if self.process:
            response = await self._send_request(message)
        else:
            response = await server_handler.handle_request(message)

        if response.error:
            raise MCPError(
                response.error.get("code", MCPErrorCode.INTERNAL_ERROR),
                response.error.get("message", "Unknown error")
            )

        return response.result.get("resources", [])

    async def read_resource(
        self,
        server_handler: Any = None,
        uri: str = ""
    ) -> Dict[str, Any]:
        """Read a resource from the server"""
        if not self.connected:
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, "Client not connected")

        message = MCPMessage(
            id=self._get_next_message_id(),
            method=MCPMethod.RESOURCES_READ.value,
            params={"uri": uri}
        )

        if self.process:
            response = await self._send_request(message)
        else:
            response = await server_handler.handle_request(message)

        if response.error:
            raise MCPError(
                response.error.get("code", MCPErrorCode.INTERNAL_ERROR),
                response.error.get("message", "Unknown error")
            )

        return response.result

    async def subscribe_resource(
        self,
        server_handler: Any = None,
        uri: str = ""
    ) -> Dict[str, Any]:
        """Subscribe to resource updates"""
        if not self.connected:
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, "Client not connected")

        message = MCPMessage(
            id=self._get_next_message_id(),
            method=MCPMethod.RESOURCES_SUBSCRIBE.value,
            params={"uri": uri}
        )

        if self.process:
            response = await self._send_request(message)
        else:
            response = await server_handler.handle_request(message)

        if response.error:
            raise MCPError(
                response.error.get("code", MCPErrorCode.INTERNAL_ERROR),
                response.error.get("message", "Unknown error")
            )

        logger.info(f"Subscribed to resource: {uri}")
        return response.result

    async def unsubscribe_resource(
        self,
        server_handler: Any = None,
        uri: str = ""
    ) -> Dict[str, Any]:
        """Unsubscribe from resource updates"""
        if not self.connected:
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, "Client not connected")

        message = MCPMessage(
            id=self._get_next_message_id(),
            method=MCPMethod.RESOURCES_UNSUBSCRIBE.value,
            params={"uri": uri}
        )

        if self.process:
            response = await self._send_request(message)
        else:
            response = await server_handler.handle_request(message)

        if response.error:
            raise MCPError(
                response.error.get("code", MCPErrorCode.INTERNAL_ERROR),
                response.error.get("message", "Unknown error")
            )

        logger.info(f"Unsubscribed from resource: {uri}")
        return response.result

    async def list_tools(self, server_handler: Any = None) -> List[Dict[str, Any]]:
        """List available tools from the server"""
        if not self.connected:
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, "Client not connected")

        message = MCPMessage(
            id=self._get_next_message_id(),
            method=MCPMethod.RESOURCES_LIST.value, # Falls back to TOOLS_LIST or standard protocol method
            method_override=True
        )
        # Use exact TOOLS_LIST protocol method
        message.method = MCPMethod.TOOLS_LIST.value

        if self.process:
            response = await self._send_request(message)
        else:
            response = await server_handler.handle_request(message)

        if response.error:
            raise MCPError(
                response.error.get("code", MCPErrorCode.INTERNAL_ERROR),
                response.error.get("message", "Unknown error")
            )

        return response.result.get("tools", [])

    async def call_tool(
        self,
        server_handler: Any = None,
        name: str = "",
        arguments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Call a tool on the server"""
        if not self.connected:
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, "Client not connected")

        message = MCPMessage(
            id=self._get_next_message_id(),
            method=MCPMethod.TOOLS_CALL.value,
            params={
                "name": name,
                "arguments": arguments or {}
            }
        )

        if self.process:
            response = await self._send_request(message)
        else:
            response = await server_handler.handle_request(message)

        if response.error:
            raise MCPError(
                response.error.get("code", MCPErrorCode.INTERNAL_ERROR),
                response.error.get("message", "Unknown error")
            )

        return response.result

    async def list_prompts(self, server_handler: Any = None) -> List[Dict[str, Any]]:
        """List available prompts from the server"""
        if not self.connected:
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, "Client not connected")

        message = MCPMessage(
            id=self._get_next_message_id(),
            method=MCPMethod.PROMPTS_LIST.value,
            params={}
        )

        if self.process:
            response = await self._send_request(message)
        else:
            response = await server_handler.handle_request(message)

        if response.error:
            raise MCPError(
                response.error.get("code", MCPErrorCode.INTERNAL_ERROR),
                response.error.get("message", "Unknown error")
            )

        return response.result.get("prompts", [])

    async def get_prompt(
        self,
        server_handler: Any = None,
        name: str = "",
        arguments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get a prompt from the server"""
        if not self.connected:
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, "Client not connected")

        message = MCPMessage(
            id=self._get_next_message_id(),
            method=MCPMethod.PROMPTS_GET.value,
            params={
                "name": name,
                "arguments": arguments or {}
            }
        )

        if self.process:
            response = await self._send_request(message)
        else:
            response = await server_handler.handle_request(message)

        if response.error:
            raise MCPError(
                response.error.get("code", MCPErrorCode.INTERNAL_ERROR),
                response.error.get("message", "Unknown error")
            )

        return response.result

    def disconnect(self):
        """Disconnect from the server and terminate subprocesses"""
        self.connected = False
        self.server_info = None
        self.server_capabilities = None

        # Terminate stdio process
        if self.read_task:
            self.read_task.cancel()
            self.read_task = None
        if self.stderr_task:
            self.stderr_task.cancel()
            self.stderr_task = None
        if self.process:
            try:
                self.process.terminate()
            except Exception:
                pass
            self.process = None

        # Clean pending requests futures
        for fut in list(self.pending_requests.values()):
            if not fut.done():
                fut.cancel()
        self.pending_requests.clear()

        logger.info("Disconnected from MCP server and terminated all active subprocesses")

    def get_client_info(self) -> Dict[str, Any]:
        """Get client information"""
        return {
            "id": self.client_id,
            "name": self.name,
            "version": self.version,
            "connected": self.connected,
            "server_info": self.server_info,
            "server_capabilities": self.server_capabilities
        }

    async def _handle_sampling_create_message(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle sampling createMessage request from server"""
        try:
            from backend.mcp_server.sampling import sampling_service
            return await sampling_service.create_message(params)
        except Exception as e:
            logger.error(f"Sampling createMessage failed: {e}")
            raise MCPError(MCPErrorCode.INTERNAL_ERROR, f"Sampling failed: {e}")

    async def _handle_resources_updated(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle notifications/resources/updated notification from server"""
        uri = params.get("uri")
        if uri:
            for cb in self.resource_updated_callbacks:
                try:
                    if asyncio.iscoroutinefunction(cb):
                        await cb(uri, params.get("payload"))
                    else:
                        cb(uri, params.get("payload"))
                except Exception as e:
                    logger.error(f"Error in resource updated callback: {e}")
        return {}
