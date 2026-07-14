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
import inspect
import os
from typing import Dict, List, Optional, Any, Callable

from backend.mcp_server.policy import (
    SUPPORTED_MCP_PROTOCOL_VERSION,
    redact_sensitive_text,
)
from .process_containment import ProcessTreeGuard, attach_process_tree_guard

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
        self.process_guard: Optional[ProcessTreeGuard] = None
        self._disconnect_task: Optional[asyncio.Task] = None
        self.request_timeout_seconds = 30
        self.max_message_bytes = 65_536
        self.max_stderr_bytes = 16_384
        self.stderr_bytes_seen = 0
        self.containment_status = "not_started"

        # Register protocol handlers
        self.register_handler(MCPMethod.SAMPLING_CREATE_MESSAGE.value, self._handle_sampling_create_message)
        self.register_handler(MCPMethod.RESOURCES_UPDATED.value, self._handle_resources_updated)

        logger.info(f"MCP Client '{self.name}' created with ID: {self.client_id}")

    def _get_next_message_id(self) -> str:
        """Generate next message ID"""
        self.message_id_counter += 1
        return f"{self.client_id}-{self.message_id_counter}"

    async def connect_via_stdio(
        self,
        command: List[str],
        env: Optional[Dict[str, str]] = None,
        *,
        cwd: Optional[str] = None,
        limits: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Any]:
        """Connect to an owner-approved external server without a shell."""
        if not command or not os.path.isabs(str(command[0])):
            raise MCPError(
                MCPErrorCode.INVALID_PARAMS,
                "An absolute executable is required",
                {"reason": "MCP_EXECUTABLE_ABSOLUTE_REQUIRED"},
            )
        limits = limits or {}
        self.request_timeout_seconds = int(limits.get("request_timeout_seconds", 30))
        self.max_message_bytes = int(limits.get("max_message_bytes", 65_536))
        self.max_stderr_bytes = int(limits.get("max_stderr_bytes", 16_384))
        max_process_memory_mb = int(limits.get("max_process_memory_mb", 256))
        self.stderr_bytes_seen = 0

        # Do not pass the full parent environment to an untrusted connector.
        inherited_names = (
            "SystemRoot", "WINDIR", "TEMP", "TMP", "LOCALAPPDATA", "APPDATA", "USERPROFILE"
        )
        sub_env = {key: os.environ[key] for key in inherited_names if os.environ.get(key)}
        sub_env.update({"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})
        if env:
            sub_env.update({str(key): str(value) for key, value in env.items()})

        creationflags = 0
        if os.name == "nt":
            creationflags = getattr(__import__("subprocess"), "CREATE_NEW_PROCESS_GROUP", 0)

        try:
            self.process = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=sub_env,
                cwd=cwd,
                limit=self.max_message_bytes + 1,
                creationflags=creationflags,
            )
        except Exception as e:
            logger.error(f"Failed to spawn external MCP server process: {e}")
            raise MCPError(
                MCPErrorCode.INTERNAL_ERROR,
                "Process spawn failed",
                {"reason": "MCP_PROCESS_SPAWN_FAILED"},
            ) from e

        try:
            self.process_guard = attach_process_tree_guard(
                self.process,
                max_process_memory_mb=max_process_memory_mb,
            )
            self.containment_status = self.process_guard.status
        except Exception as exc:
            try:
                self.process.terminate()
            except Exception:
                pass
            self.process = None
            raise MCPError(
                MCPErrorCode.INTERNAL_ERROR,
                "Process containment could not be established",
                {"reason": "MCP_PROCESS_CONTAINMENT_FAILED"},
            ) from exc

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
            if response.error:
                raise MCPError(
                    response.error.get("code", MCPErrorCode.INTERNAL_ERROR),
                    response.error.get("message", "Initialization failed"),
                )
            negotiated = str((response.result or {}).get("protocolVersion") or "")
            if negotiated != SUPPORTED_MCP_PROTOCOL_VERSION:
                raise MCPError(
                    MCPErrorCode.INVALID_REQUEST,
                    "Unsupported MCP protocol version",
                    {"reason": "MCP_PROTOCOL_UNSUPPORTED", "received": negotiated},
                )
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
            await self.disconnect_async()
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
            try:
                return await asyncio.wait_for(future, timeout=self.request_timeout_seconds)
            except asyncio.CancelledError:
                self.pending_requests.pop(message.id, None)
                await self._send_cancel_notification(message.id, "Owner cancelled the operation")
                raise
            except TimeoutError as exc:
                self.pending_requests.pop(message.id, None)
                await self._send_cancel_notification(message.id, "Request deadline exceeded")
                raise MCPError(
                    MCPErrorCode.INTERNAL_ERROR,
                    "MCP request timed out",
                    {"reason": "MCP_REQUEST_TIMEOUT"},
                ) from exc
        
        raise MCPError(MCPErrorCode.INTERNAL_ERROR, "No external subprocess transport active")

    async def _send_cancel_notification(self, request_id: str, reason: str) -> None:
        """Best-effort MCP cancellation notification without request content."""
        if not self.connected or not self.process:
            return
        try:
            await self._write_message(MCPMessage(
                method="notifications/cancelled",
                params={"requestId": request_id, "reason": reason},
            ))
        except Exception:
            logger.warning("MCP cancellation notification could not be delivered")

    async def _read_loop(self):
        """Stdout reading loop for JSON-RPC messages from external server"""
        while self.connected and self.process and self.process.stdout:
            try:
                line = await self.process.stdout.readline()
                if not line:
                    break
                if len(line) > self.max_message_bytes:
                    raise MCPError(
                        MCPErrorCode.INVALID_REQUEST,
                        "MCP message exceeded configured size",
                        {"reason": "MCP_OUTPUT_LIMIT_EXCEEDED"},
                    )
                data = json.loads(line.decode("utf-8", errors="strict").strip())
                if not isinstance(data, dict) or data.get("jsonrpc", "2.0") != "2.0":
                    raise MCPError(
                        MCPErrorCode.INVALID_REQUEST,
                        "Malformed MCP JSON-RPC message",
                        {"reason": "MCP_MALFORMED_JSON_RPC"},
                    )
                await self._handle_incoming_message(data)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("MCP stdio reader stopped: %s", type(e).__name__)
                self._fail_pending(e)
                break
        self.disconnect()

    async def _stderr_loop(self):
        """Stderr reading loop to capture external server logging output"""
        while self.connected and self.process and self.process.stderr:
            try:
                line = await self.process.stderr.readline()
                if not line:
                    break
                self.stderr_bytes_seen += len(line)
                if self.stderr_bytes_seen > self.max_stderr_bytes:
                    logger.warning("MCP server stderr limit exceeded; remaining stderr is suppressed")
                    break
                err_msg = redact_sensitive_text(line.decode("utf-8", errors="replace").strip())
                logger.warning("[MCP-Server-Stderr] %s", err_msg[:2_000])
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
                encoded = payload.encode("utf-8")
                if len(encoded) > self.max_message_bytes:
                    raise MCPError(
                        MCPErrorCode.INVALID_PARAMS,
                        "MCP request exceeded configured size",
                        {"reason": "MCP_INPUT_LIMIT_EXCEEDED"},
                    )
                write_result = self.process.stdin.write(encoded)
                if inspect.isawaitable(write_result):
                    await write_result
                await self.process.stdin.drain()
            except Exception as e:
                logger.error("Failed to write stdio message: %s", type(e).__name__)
                raise

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
            method=MCPMethod.TOOLS_LIST.value,
            params={},
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

    async def _disconnect_impl(self) -> None:
        """Close pipes, terminate the process tree, and reap the child."""
        self.connected = False
        self.server_info = None
        self.server_capabilities = None
        current_task = None
        try:
            current_task = asyncio.current_task()
        except RuntimeError:
            pass
        if self.read_task and self.read_task is not current_task:
            self.read_task.cancel()
        self.read_task = None
        if self.stderr_task:
            self.stderr_task.cancel()
            self.stderr_task = None
        process = self.process
        guard = self.process_guard
        self.process = None
        self.process_guard = None
        if process:
            try:
                if process.stdin:
                    close_result = process.stdin.close()
                    if inspect.isawaitable(close_result):
                        await close_result
                    wait_closed = getattr(process.stdin, "wait_closed", None)
                    if callable(wait_closed):
                        await wait_closed()
            except Exception:
                pass
            try:
                termination = process.terminate()
                if inspect.isawaitable(termination):
                    await termination
            except Exception:
                pass
        if guard:
            try:
                guard.close()
            except Exception:
                pass
        if process:
            try:
                await asyncio.wait_for(process.wait(), timeout=5)
            except Exception:
                transport = getattr(process, "_transport", None)
                if transport is not None:
                    try:
                        transport.close()
                    except Exception:
                        pass
        self.containment_status = "stopped"

        # Clean pending requests futures
        for fut in list(self.pending_requests.values()):
            if not fut.done():
                fut.cancel()
        self.pending_requests.clear()

        logger.info("Disconnected from MCP server and terminated all active subprocesses")

    async def disconnect_async(self) -> None:
        task = self._disconnect_task
        current = asyncio.current_task()
        if task is None:
            task = asyncio.create_task(self._disconnect_impl())
            self._disconnect_task = task
        if task is not current:
            await task

    def disconnect(self):
        """Begin disconnect immediately; async owners should await disconnect_async."""
        self.connected = False
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            if self.process is None:
                self.server_info = None
                self.server_capabilities = None
                self.containment_status = "stopped"
                return
            raise RuntimeError("MCP process disconnect requires its owning runtime loop")
        if self._disconnect_task is None:
            self._disconnect_task = loop.create_task(self._disconnect_impl())

    def _fail_pending(self, error: Exception) -> None:
        for future in list(self.pending_requests.values()):
            if not future.done():
                future.set_exception(error)
        self.pending_requests.clear()

    def get_client_info(self) -> Dict[str, Any]:
        """Get client information"""
        return {
            "id": self.client_id,
            "name": self.name,
            "version": self.version,
            "connected": self.connected,
            "server_info": self.server_info,
            "server_capabilities": self.server_capabilities,
            "containment_status": self.containment_status,
        }

    async def _handle_sampling_create_message(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle sampling createMessage request from server"""
        try:
            from backend.mcp_server.sampling import sampling_service  # inversion:ok — lazy optional sampling backend
            return await sampling_service.create_message(params)
        except MCPError:
            raise
        except Exception as e:
            logger.error(f"Sampling createMessage failed: {e}")
            raise MCPError(
                MCPErrorCode.INTERNAL_ERROR,
                "Sampling failed",
                {"reason": "MCP_SAMPLING_FAILED"},
            ) from e

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
