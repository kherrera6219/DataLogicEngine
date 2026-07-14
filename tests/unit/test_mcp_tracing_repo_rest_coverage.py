import asyncio
from datetime import datetime, UTC
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from flask import Flask
from sqlalchemy.exc import SQLAlchemyError

import backend.mcp_server.registry as registry_module
import backend.mcp_server.router as router_module
import backend.repositories.node_repository as node_repo_module
import backend.rest_api as rest_api_module


def test_tool_registry_sync_async_and_errors():
    registry = registry_module.ToolRegistry()

    @registry.register(
        name="sync_tool",
        description="sync tool",
        input_schema={"type": "object", "properties": {}},
    )
    def sync_tool():
        return {"ok": True}

    @registry.register(
        name="async_tool",
        description="async tool",
        input_schema={"type": "object", "properties": {}},
    )
    async def async_tool():
        return {"async": True}

    assert registry.get_tool("sync_tool") is not None
    tools = registry.list_tools()
    assert any(t["name"] == "sync_tool" for t in tools)
    assert any(t["name"] == "async_tool" for t in tools)

    sync_result = asyncio.run(registry.execute_tool("sync_tool", {}))
    assert sync_result == {"ok": True}

    async_result = asyncio.run(registry.execute_tool("async_tool", {}))
    assert async_result == {"async": True}

    with pytest.raises(ValueError):
        asyncio.run(registry.execute_tool("missing", {}))

    @registry.register(
        name="failing_tool",
        description="failing",
        input_schema={"type": "object", "properties": {}},
    )
    def failing_tool():
        raise RuntimeError("tool error")

    with pytest.raises(RuntimeError):
        asyncio.run(registry.execute_tool("failing_tool", {}))


def test_mcp_router_paths(monkeypatch):
    router = router_module.MCPRouter()
    mock_registry = MagicMock()
    mock_registry.list_tools.return_value = [{"name": "t1"}]
    mock_registry.execute_tool = AsyncMock(return_value={"message": "done"})
    monkeypatch.setattr(router, "registry", mock_registry)

    invalid = asyncio.run(router.handle_message("bad"))
    assert invalid["error"]["code"] == -32600

    missing_method = asyncio.run(router.handle_message({"id": 1}))
    assert missing_method["error"]["code"] == -32600

    initialized = asyncio.run(router.handle_message({"id": 1, "method": "initialize"}))
    assert initialized["result"]["protocolVersion"] == "2025-11-25"

    context = {"user_id": "owner", "scopes": ["*"]}
    tools = asyncio.run(router.handle_message({"id": 2, "method": "tools/list"}, execution_context=context))
    assert tools["result"]["tools"] == [{"name": "t1"}]

    call_result = asyncio.run(
        router.handle_message(
            {"id": 3, "method": "tools/call", "params": {"name": "tool", "arguments": {}}},
            execution_context=context,
        )
    )
    assert call_result["result"]["content"][0]["text"] == "{'message': 'done'}"

    mock_registry.execute_tool.side_effect = RuntimeError("execution failed")
    call_error = asyncio.run(
        router.handle_message(
            {"id": 4, "method": "tools/call", "params": {"name": "tool", "arguments": {}}},
            execution_context=context,
        )
    )
    assert call_error["error"]["code"] == -32603
    assert call_error["error"]["message"] == "execution failed"

    # Sensitive/internal errors should be sanitized before returning to clients.
    mock_registry.execute_tool.side_effect = RuntimeError("database password leaked in traceback")
    sanitized_error = asyncio.run(
        router.handle_message(
            {"id": 6, "method": "tools/call", "params": {"name": "tool", "arguments": {}}},
            execution_context=context,
        )
    )
    assert sanitized_error["error"]["code"] == -32603
    assert sanitized_error["error"]["message"] == "Tool execution failed"

    unknown = asyncio.run(
        router.handle_message({"id": 5, "method": "unknown/method"}, execution_context=context)
    )
    assert unknown["error"]["code"] == -32601


# NOTE: test_jira_tools_paths and test_salesforce_tools_paths were removed.
# The Jira and Salesforce MCP connectors are legacy external SaaS
# integrations that have been removed from this local-first / desktop-only
# build.


def test_node_repository_paths(monkeypatch):
    cache = MagicMock()
    db_session = MagicMock()
    db = SimpleNamespace(session=db_session)
    monkeypatch.setattr(node_repo_module, "cache", cache)
    monkeypatch.setattr(node_repo_module, "db", db)

    class DummyNode:
        uid = "uid"
        tenant_id = "tenant_id"

        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
            self.created_at = datetime.now(UTC)
            self.updated_at = datetime.now(UTC)

    monkeypatch.setattr(node_repo_module, "Node", DummyNode)
    repo = node_repo_module.NodeRepository(tenant_id="tenant-1")

    created = repo.create(
        {
            "uid": "n1",
            "node_type": "type",
            "label": "Label",
            "description": "Desc",
            "original_id": "orig",
            "axis_number": 1,
            "level": "L1",
            "attributes": {"a": 1},
        }
    )
    assert created["uid"] == "n1"
    cache.set.assert_called()

    cache.get.return_value = {"uid": "cached-node"}
    cached = repo.get_by_uid("cached")
    assert cached["uid"] == "cached-node"

    cache.get.return_value = None
    db_node = DummyNode(
        uid="db-node",
        node_type="type",
        label="DB",
        description="d",
        original_id="o",
        axis_number=2,
        level="L2",
        attributes={},
        tenant_id="tenant-1",
    )
    db_session.query.return_value.filter.return_value.filter.return_value.first.return_value = db_node
    fetched = repo.get_by_uid("db-node")
    assert fetched["uid"] == "db-node"

    db_session.query.return_value.filter.return_value.filter.return_value.first.side_effect = SQLAlchemyError("boom")
    assert repo.get_by_uid("db-node") is None

    failing_node_cls = MagicMock(side_effect=SQLAlchemyError("insert fail"))
    monkeypatch.setattr(node_repo_module, "Node", failing_node_cls)
    assert repo.create({"uid": "fail"}) is None
    db_session.rollback.assert_called()


def test_rest_api_paths(monkeypatch):
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(rest_api_module.rest_api)
    client = app.test_client()

    graph_manager = MagicMock()
    graph_manager.get_statistics.return_value = {"nodes": 10}
    app.config["GRAPH_MANAGER"] = graph_manager

    resp = client.get("/api/v1/graph/stats")
    assert resp.status_code == 200
    assert resp.json["success"] is True

    app.config["GRAPH_MANAGER"] = None
    resp = client.get("/api/v1/graph/stats")
    assert resp.status_code == 500

    app.config["GRAPH_MANAGER"] = MagicMock(get_statistics=MagicMock(side_effect=RuntimeError("stats failed")))
    resp = client.get("/api/v1/graph/stats")
    assert resp.status_code == 500

    resp = client.post("/api/v1/query", json={})
    assert resp.status_code == 400

    resp = client.post("/api/v1/query", json={"confidence": 0.9})
    assert resp.status_code == 400

    failed_gateway = MagicMock()
    failed_gateway.process = AsyncMock(
        return_value=SimpleNamespace(
            ok=False,
            error="No active providers found",
            failure={"code": "PROVIDER_FAILURE"},
        )
    )
    monkeypatch.setattr(
        "backend.llm_gateway.gateway.get_gateway", lambda: failed_gateway
    )
    resp = client.post("/api/v1/query", json={"query": "hello"})
    assert resp.status_code == 503

    successful_gateway = MagicMock()
    successful_gateway.process = AsyncMock(
        return_value=SimpleNamespace(
            ok=True,
            content="ok",
            run_id="run-1",
            contract_version="governed.v1",
            status="completed",
            confidence=None,
            provider_used="test",
            model_used="test-model",
        )
    )
    monkeypatch.setattr(
        "backend.llm_gateway.gateway.get_gateway", lambda: successful_gateway
    )
    resp = client.post(
        "/api/v1/query",
        json={"query": "hello", "confidence": 0.8, "max_passes": 2, "max_layer": 3},
    )
    assert resp.status_code == 200
    assert resp.json["success"] is True

    exception_gateway = MagicMock()
    exception_gateway.process = AsyncMock(side_effect=RuntimeError("query failed"))
    monkeypatch.setattr(
        "backend.llm_gateway.gateway.get_gateway", lambda: exception_gateway
    )
    resp = client.post("/api/v1/query", json={"query": "hello"})
    assert resp.status_code == 500
