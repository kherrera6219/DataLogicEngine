import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from core.mcp import MCPManager, MCPClient
from core.mcp.mcp_protocol import MCPError


@pytest.mark.asyncio
async def test_mcp_bidirectional_sampling_fails_closed_without_governed_provider():
    """Sampling is absent unless an approved governed provider is injected."""
    manager = MCPManager()
    server = manager.create_server(name="TestSamplingServer")
    client = manager.create_client(name="TestSamplingClient")

    # Connect client to server and register the bidirectional handler callback
    await manager.connect_client_to_server(client.client_id, server.server_id)
    assert server.client_callback is not None

    # Trigger a completions sampling call from the server back to the client
    params = {
        "messages": [
            {"role": "user", "content": {"type": "text", "text": "Hello, UKG expert."}}
        ],
        "modelPreferences": {"model": "local-deterministic"}
    }
    
    with pytest.raises(MCPError, match="Sampling is not enabled"):
        await server.sample_completions(params)


@pytest.mark.asyncio
async def test_mcp_realtime_resource_subscriptions():
    """Verify resource updates propagate to both client callbacks and global SSE manager"""
    manager = MCPManager()
    server = manager.create_server(name="TestNotifyServer")
    client = manager.create_client(name="TestNotifyClient")

    # Connect
    await manager.connect_client_to_server(client.client_id, server.server_id)

    # Register resource
    async def dummy_handler(params):
        return "some content"
        
    server.register_resource(
        uri="ukg://nodes/n123",
        name="Node 123",
        handler=dummy_handler
    )

    # Track callback execution
    received_updates = []
    
    async def resource_updated_cb(uri, payload):
        received_updates.append((uri, payload))
        
    client.resource_updated_callbacks.append(resource_updated_cb)

    # Subscribe to resource uri
    await client.subscribe_resource(server, "ukg://nodes/n123")

    # Trigger notification on the server
    await server.notify_resource_updated("ukg://nodes/n123")
    
    # Assert client callback fired
    assert len(received_updates) == 1
    assert received_updates[0][0] == "ukg://nodes/n123"


@pytest.mark.asyncio
async def test_stdio_transport_lifecycle(tmp_path):
    """Test standard I/O (stdio) subprocess transport and asynchronous JSON-RPC messaging"""
    client = MCPClient(name="TestStdioClient")
    
    mock_process = AsyncMock()
    mock_process.stdin = AsyncMock()
    mock_process.stdout = AsyncMock()
    mock_process.stderr = MagicMock() # Use MagicMock for stderr so return_value can be set easily
    
    # Handshake JSON response from external server
    handshake_response = {
        "jsonrpc": "2.0",
        "id": f"{client.client_id}-1",
        "result": {
            "protocolVersion": "2025-11-25",
            "serverInfo": {
                "name": "mock-external-server",
                "version": "0.1.0"
            },
            "capabilities": {}
        }
    }
    
    # Make readline return the response on the first call and hang indefinitely on subsequent calls
    # to avoid premature EOF disconnect race conditions.
    calls = [0]
    async def mock_readline():
        if calls[0] == 0:
            calls[0] += 1
            return json.dumps(handshake_response).encode("utf-8") + b"\n"
        while True:
            await asyncio.sleep(1)
            
    mock_process.stdout.readline = mock_readline
    mock_process.stderr.readline = AsyncMock(return_value=b"")

    executable = tmp_path / "safe-server.exe"
    executable.write_bytes(b"fixture")
    guard = MagicMock(status="windows_job_object_attached")
    with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec, \
         patch("core.mcp.mcp_client.attach_process_tree_guard", return_value=guard):
        command = [str(executable), "--stdio"]
        init_result = await client.connect_via_stdio(command)
        
        # Verify execution
        mock_exec.assert_called_once()
        assert init_result["serverInfo"]["name"] == "mock-external-server"
        assert client.connected is True
        
        # Cleanup
        await client.disconnect_async()
        assert client.connected is False
        assert client.process is None


def test_repository_dynamic_config_is_not_runtime_authority(tmp_path):
    """Tracked JSON cannot silently register or execute connectors."""
    manager = MCPManager()
    
    mock_config = {
        "mcpServers": {
            "test-fs": {
                "command": "python",
                "args": ["-m", "http.server", "8000"],
                "env": {"TEST_VAR": "1"}
            }
        }
    }
    
    config_file = tmp_path / "mcp_servers.json"
    config_file.write_text(json.dumps(mock_config), encoding="utf-8")
    
    with patch("os.path.join", return_value=str(config_file)), \
         patch("os.path.exists", return_value=True):
        assert manager.load_external_config() == {}
        assert manager.external_configs == {}


def test_mcp_config_endpoint_reports_postgresql_authority(authenticated_client, monkeypatch):
    """The owner sees database-owned connector configuration, not repository JSON."""
    manager = MCPManager()
    monkeypatch.setattr("backend.routes.mcp_routes.get_mcp_manager", lambda: manager)

    resp = authenticated_client.get("/api/v1/mcp/config")

    assert resp.status_code == 200
    assert resp.json["success"] is True
    assert resp.json["authority"] == "postgresql"
    assert resp.json["repository_config_enabled"] is False
