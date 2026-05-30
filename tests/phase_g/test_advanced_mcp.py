import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from flask import Flask

from core.mcp import MCPManager, MCPClient


@pytest.mark.asyncio
async def test_mcp_bidirectional_sampling():
    """Verify in-memory client-server bidirectional completions sampling works perfectly"""
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
    
    result = await server.sample_completions(params)
    assert result["role"] == "assistant"
    assert "content" in result
    assert "local" in result["metadata"]["provider"]


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
async def test_stdio_transport_lifecycle():
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
            "protocolVersion": "2024-11-05",
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

    with patch("asyncio.create_subprocess_exec", return_value=mock_process) as mock_exec:
        command = ["npx", "git-server"]
        init_result = await client.connect_via_stdio(command)
        
        # Verify execution
        mock_exec.assert_called_once()
        assert init_result["serverInfo"]["name"] == "mock-external-server"
        assert client.connected is True
        
        # Cleanup
        client.disconnect()
        assert client.connected is False
        assert client.process is None


def test_dynamic_config_manager(tmp_path):
    """Verify MCP config loading, dynamic servers discovery, and load flow"""
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
        manager.load_external_config()
        assert "test-fs" in manager.external_configs
        assert manager.external_configs["test-fs"]["command"] == "python"


def test_mcp_routes_admin_endpoints(monkeypatch):
    """Test administrative dynamic configuration Flask routes"""
    app = Flask(__name__)
    app.config["TESTING"] = True
    
    # Mock Blueprint imports and routing decorators
    from routes.mcp_routes import mcp_bp
    app.register_blueprint(mcp_bp, url_prefix="/api/mcp")
    
    manager = MCPManager()
    manager.external_configs = {
        "dummy": {"command": "echo", "args": ["hello"]}
    }
    # Mock load_external_config to return the mock configuration
    manager.load_external_config = MagicMock(return_value=manager.external_configs)
    
    with patch("routes.mcp_routes.get_mcp_manager", return_value=manager), \
         patch("flask_login.utils._get_user", return_value=MagicMock(is_authenticated=True, is_admin=True)):
        
        with patch("routes.mcp_routes.login_required", lambda f: f), \
             patch("routes.mcp_routes.api_admin_required", lambda f: f):
            
            # Re-register blueprint without authenticators for testing
            test_app = Flask(__name__)
            test_bp = mcp_bp
            test_app.register_blueprint(test_bp, url_prefix="/api/mcp")
            test_client = test_app.test_client()
            
            resp = test_client.get("/api/mcp/config")
            assert resp.status_code == 200
            assert resp.json["success"] is True
            assert "dummy" in resp.json["config"]
