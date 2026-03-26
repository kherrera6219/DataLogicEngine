import asyncio
import importlib
import sys
import types
import uuid
from datetime import datetime, UTC
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from flask import Flask
from sqlalchemy.exc import SQLAlchemyError

import backend.mcp_server.registry as registry_module
import backend.mcp_server.router as router_module
import backend.repositories.node_repository as node_repo_module
import backend.rest_api as rest_api_module
import backend.tracing.logger as tracing_logger_module


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
    assert initialized["result"]["protocolVersion"] == "0.1.0"

    tools = asyncio.run(router.handle_message({"id": 2, "method": "tools/list"}))
    assert tools["result"]["tools"] == [{"name": "t1"}]

    call_result = asyncio.run(
        router.handle_message({"id": 3, "method": "tools/call", "params": {"name": "tool", "arguments": {}}})
    )
    assert call_result["result"]["content"][0]["text"] == "{'message': 'done'}"

    mock_registry.execute_tool.side_effect = RuntimeError("execution failed")
    call_error = asyncio.run(
        router.handle_message({"id": 4, "method": "tools/call", "params": {"name": "tool", "arguments": {}}})
    )
    assert call_error["error"]["code"] == -32603
    assert call_error["error"]["message"] == "execution failed"

    # Sensitive/internal errors should be sanitized before returning to clients.
    mock_registry.execute_tool.side_effect = RuntimeError("database password leaked in traceback")
    sanitized_error = asyncio.run(
        router.handle_message({"id": 6, "method": "tools/call", "params": {"name": "tool", "arguments": {}}})
    )
    assert sanitized_error["error"]["code"] == -32603
    assert sanitized_error["error"]["message"] == "Tool execution failed"

    unknown = asyncio.run(router.handle_message({"id": 5, "method": "unknown/method"}))
    assert unknown["error"]["code"] == -32601


def test_jira_tools_paths(monkeypatch):
    fake_jira_module = types.SimpleNamespace(JIRA=MagicMock())
    with patch.dict(sys.modules, {"jira": fake_jira_module}):
        sys.modules.pop("backend.mcp_server.tools.jira", None)
        jira_tools = importlib.import_module("backend.mcp_server.tools.jira")

    # Missing credentials
    monkeypatch.delenv("JIRA_SERVER_URL", raising=False)
    monkeypatch.delenv("JIRA_USER_EMAIL", raising=False)
    monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
    assert jira_tools.get_jira_client() is None
    assert jira_tools.ticket_create("UKG", "summary")["status"] == "fail"
    assert jira_tools.status_check("UKG-1")["status"] == "fail"

    # Successful connection and tool calls
    monkeypatch.setenv("JIRA_SERVER_URL", "https://jira.example.com")
    monkeypatch.setenv("JIRA_USER_EMAIL", "user@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "token")

    mock_issue = MagicMock()
    mock_issue.key = "UKG-42"
    mock_issue.fields.status.name = "In Progress"
    mock_issue.fields.summary = "Task"
    mock_issue.fields.assignee = None
    mock_issue.fields.updated = "2024-01-01T00:00:00"

    mock_client = MagicMock()
    mock_client.create_issue.return_value = mock_issue
    mock_client.client_info.return_value = "https://jira.example.com"
    mock_client.issue.return_value = mock_issue

    with patch.object(jira_tools, "JIRA", return_value=mock_client):
        created = jira_tools.ticket_create("UKG", "summary", "desc", "Task")
        assert created["status"] == "created"
        assert created["key"] == "UKG-42"

        status = jira_tools.status_check("UKG-42")
        assert status["status"] == "In Progress"

        mock_client.issue.side_effect = RuntimeError("jira down")
        status_error = jira_tools.status_check("UKG-42")
        assert status_error["status"] == "error"


def test_salesforce_tools_paths(monkeypatch):
    fake_sf_module = types.SimpleNamespace(Salesforce=MagicMock())
    with patch.dict(sys.modules, {"simple_salesforce": fake_sf_module}):
        sys.modules.pop("backend.mcp_server.tools.salesforce", None)
        sf_tools = importlib.import_module("backend.mcp_server.tools.salesforce")

    monkeypatch.delenv("SALESFORCE_USERNAME", raising=False)
    monkeypatch.delenv("SALESFORCE_PASSWORD", raising=False)
    monkeypatch.delenv("SALESFORCE_SECURITY_TOKEN", raising=False)
    assert sf_tools.get_salesforce_client() is None
    assert sf_tools.crm_lookup("acme")["status"] == "fail"
    assert sf_tools.lead_create("A", "B", "C", "a@b.com")["status"] == "fail"

    monkeypatch.setenv("SALESFORCE_USERNAME", "user")
    monkeypatch.setenv("SALESFORCE_PASSWORD", "pass")
    monkeypatch.setenv("SALESFORCE_SECURITY_TOKEN", "token")
    monkeypatch.setenv("SALESFORCE_DOMAIN", "test")

    mock_sf = MagicMock()
    mock_sf.sf_instance = "instance-1"
    mock_sf.search.return_value = {"searchRecords": [{"Id": "1"}]}
    mock_sf.Lead.create.return_value = {"id": "lead-1"}

    with patch.object(sf_tools, "Salesforce", return_value=mock_sf):
        lookup = sf_tools.crm_lookup("acme")
        assert lookup["status"] == "success"
        assert len(lookup["results"]) == 1

        lead = sf_tools.lead_create("Jane", "Doe", "Acme", "jane@example.com")
        assert lead["status"] == "success"
        assert lead["lead_id"] == "lead-1"

        mock_sf.search.side_effect = RuntimeError("search fail")
        lookup_error = sf_tools.crm_lookup("acme")
        assert lookup_error["status"] == "error"

        mock_sf.Lead.create.side_effect = RuntimeError("lead fail")
        lead_error = sf_tools.lead_create("Jane", "Doe", "Acme", "jane@example.com")
        assert lead_error["status"] == "error"


def test_trace_logger_paths(monkeypatch):
    session = MagicMock()
    monkeypatch.setattr(tracing_logger_module.db, "session", session)

    assert tracing_logger_module.TraceLogger.log_ka_invocation("KA-1", {}, {}, run_id=None) is None

    invocation_obj = SimpleNamespace(invocation_id=uuid.uuid4())
    monkeypatch.setattr(tracing_logger_module, "TraceKAInvocation", lambda **kwargs: invocation_obj)
    inv_id = tracing_logger_module.TraceLogger.log_ka_invocation(
        "KA-2",
        {"q": 1},
        {"a": 2},
        run_id=str(uuid.uuid4()),
        stage_id=str(uuid.uuid4()),
        duration_ms=12.0,
        success=True,
    )
    assert isinstance(inv_id, str)
    session.add.assert_called()
    session.commit.assert_called()

    monkeypatch.setattr(tracing_logger_module, "TraceKAInvocation", MagicMock(side_effect=RuntimeError("insert fail")))
    assert tracing_logger_module.TraceLogger.log_ka_invocation("KA-3", {}, {}, run_id=str(uuid.uuid4())) is None
    session.rollback.assert_called()

    run_obj = SimpleNamespace(run_id=uuid.uuid4())
    monkeypatch.setattr(tracing_logger_module, "TraceRun", lambda **kwargs: run_obj)
    created_run_id = tracing_logger_module.TraceLogger.create_run(1, "query", tier="moderate")
    assert isinstance(created_run_id, str)

    monkeypatch.setattr(tracing_logger_module, "TraceRun", MagicMock(side_effect=RuntimeError("run fail")))
    fallback_id = tracing_logger_module.TraceLogger.create_run(1, "query")
    assert isinstance(fallback_id, str)

    mock_run = SimpleNamespace(status="processing", confidence=0.0, completed_at=None)
    trace_run_model = MagicMock()
    trace_run_model.query.filter_by.return_value.first.return_value = mock_run
    monkeypatch.setattr(tracing_logger_module, "TraceRun", trace_run_model)
    tracing_logger_module.TraceLogger.update_run_status(created_run_id, "completed", confidence=0.9)
    assert mock_run.status == "completed"
    assert mock_run.confidence == 0.9
    assert mock_run.completed_at is not None

    trace_run_model.query.filter_by.return_value.first.side_effect = RuntimeError("update fail")
    tracing_logger_module.TraceLogger.update_run_status(created_run_id, "failed")
    session.rollback.assert_called()


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


def test_rest_api_paths():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(rest_api_module.rest_api)
    client = app.test_client()

    graph_manager = MagicMock()
    graph_manager.get_statistics.return_value = {"nodes": 10}
    app.config["GRAPH_MANAGER"] = graph_manager

    orchestrator = MagicMock()
    orchestrator.process_request.return_value = {"answer": "ok"}
    app.config["APP_ORCHESTRATOR"] = orchestrator

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

    app.config["APP_ORCHESTRATOR"] = None
    resp = client.post("/api/v1/query", json={"query": "hello"})
    assert resp.status_code == 500

    app.config["APP_ORCHESTRATOR"] = orchestrator
    resp = client.post(
        "/api/v1/query",
        json={"query": "hello", "confidence": 0.8, "max_passes": 2, "max_layer": 3},
    )
    assert resp.status_code == 200
    assert resp.json["success"] is True

    app.config["APP_ORCHESTRATOR"] = MagicMock(process_request=MagicMock(side_effect=RuntimeError("query failed")))
    resp = client.post("/api/v1/query", json={"query": "hello"})
    assert resp.status_code == 500
