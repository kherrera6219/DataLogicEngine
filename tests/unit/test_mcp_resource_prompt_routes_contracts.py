from __future__ import annotations

import inspect
from types import SimpleNamespace

from flask import Flask


class _Query:
    def __init__(self, *, first=None, rows=(), error=None):
        self.first_value = first
        self.rows = list(rows)
        self.error = error

    def filter_by(self, **_values):
        if self.error:
            raise self.error
        return self

    def first(self):
        if self.error:
            raise self.error
        return self.first_value

    def all(self):
        if self.error:
            raise self.error
        return self.rows


class _Model:
    query = _Query()


class _Session:
    def __init__(self):
        self.added = []
        self.commits = 0
        self.refresh_status = None

    def add(self, value):
        self.added.append(value)

    def flush(self):
        return None

    def commit(self):
        self.commits += 1

    def refresh(self, value):
        if self.refresh_status:
            value.status = self.refresh_status


class _Execution:
    counter = 0

    def __init__(self, **values):
        _Execution.counter += 1
        self.execution_id = f"execution-{_Execution.counter}"
        self.status = values.pop("status", "running")
        for key, value in values.items():
            setattr(self, key, value)

    def to_dict(self):
        return {"execution_id": self.execution_id, "status": self.status}


def _route(function, *args):
    return inspect.unwrap(function)(*args)


def _install(monkeypatch, *, server=None, resource=None, prompt=None, manager_server=True):
    import backend.routes.mcp_routes as module

    server = server or SimpleNamespace(
        id=1, server_id="server-1", status="active", config={},
        total_requests=0, successful_requests=0, failed_requests=0,
    )
    resource = resource or SimpleNamespace(
        id=2, uri="dle://resource", resource_metadata={"required_scopes": ["resource:read"]},
        access_count=0, last_accessed=None, to_dict=lambda: {"id": 2, "uri": "dle://resource"},
    )
    prompt = prompt or SimpleNamespace(
        id=3, name="review", prompt_metadata={"required_scopes": ["prompt:read"]},
        usage_count=0, last_used=None, to_dict=lambda: {"id": 3, "name": "review"},
    )
    server_model = type("ServerModel", (_Model,), {"query": _Query(first=server)})
    resource_model = type("ResourceModel", (_Model,), {"query": _Query(first=resource, rows=[resource])})
    prompt_model = type("PromptModel", (_Model,), {"query": _Query(first=prompt, rows=[prompt])})
    tool = SimpleNamespace(to_dict=lambda: {"id": 4, "name": "tool"})
    tool_model = type("ToolModel", (_Model,), {"query": _Query(rows=[tool])})
    session = _Session()
    monkeypatch.setattr(module, "MCPServerModel", server_model)
    monkeypatch.setattr(module, "MCPResource", resource_model)
    monkeypatch.setattr(module, "MCPPrompt", prompt_model)
    monkeypatch.setattr(module, "MCPTool", tool_model)
    monkeypatch.setattr(module, "MCPExecutionRecord", _Execution)
    monkeypatch.setattr(module, "db", SimpleNamespace(session=session))
    monkeypatch.setattr(module, "_active_consent", lambda _server: SimpleNamespace(approved_scopes=["resource:read", "prompt:read"]))
    monkeypatch.setattr(module, "_principal_id", lambda: "principal")
    monkeypatch.setattr(module, "_publish_execution_state", lambda *_args: None)
    monkeypatch.setattr(module, "govern_connector_result", lambda content, **_values: {
        "sha256": "hash", "size_bytes": 10, "content": content,
        "trust": "untrusted", "prompt_injection_risk": "none",
    })
    live_server = SimpleNamespace(
        _handle_resources_read=lambda _args: {"contents": ["resource"]},
        _handle_prompts_get=lambda _args: {"messages": ["prompt"]},
    ) if manager_server else None
    manager = SimpleNamespace(
        external_clients={},
        get_server=lambda _id: live_server,
        read_external_resource_sync=lambda *_args, **_kwargs: {"contents": ["external"]},
        get_external_prompt_sync=lambda *_args, **_kwargs: {"messages": ["external"]},
    )
    monkeypatch.setattr(module, "get_mcp_manager", lambda: manager)
    monkeypatch.setattr(module, "run_async", lambda value: value)
    return module, session, server, resource, prompt, manager


def test_mcp_resource_tool_and_prompt_inventory(monkeypatch):
    module, _session, _server, _resource, _prompt, _manager = _install(monkeypatch)
    app = Flask(__name__)
    with app.test_request_context("/"):
        assert _route(module.list_resources, "server-1")[0].get_json()["count"] == 1
        assert _route(module.list_tools, "server-1")[0].get_json()["count"] == 1
        assert _route(module.list_prompts, "server-1")[0].get_json()["count"] == 1

    module.MCPServerModel.query = _Query(first=None)
    with app.test_request_context("/"):
        assert _route(module.list_resources, "missing")[1] == 404
        assert _route(module.list_tools, "missing")[1] == 404
        assert _route(module.list_prompts, "missing")[1] == 404


def test_mcp_internal_resource_and_prompt_success(monkeypatch):
    module, session, server, resource, prompt, _manager = _install(monkeypatch)
    app = Flask(__name__)
    with app.test_request_context("/resource"):
        result = _route(module.read_resource, "server-1", 2)
        assert result[1] == 200 and result[0].get_json()["result"]["sha256"] == "hash"
    assert resource.access_count == 1 and server.successful_requests == 1

    with app.test_request_context("/prompt", method="POST", json={"arguments": {"topic": "coverage"}}):
        result = _route(module.get_prompt, "server-1", 3)
        assert result[1] == 200 and result[0].get_json()["prompt"]["name"] == "review"
    assert prompt.usage_count == 1 and session.commits >= 4


def test_mcp_external_resource_and_prompt_success(monkeypatch):
    module, _session, server, _resource, _prompt, manager = _install(monkeypatch, manager_server=False)
    manager.external_clients["server-1"] = object()
    server.config = {"limits": {"request_timeout_seconds": 4, "max_message_bytes": 100}}
    app = Flask(__name__)
    with app.test_request_context("/resource"):
        assert _route(module.read_resource, "server-1", 2)[1] == 200
    with app.test_request_context("/prompt", method="POST", json={}):
        assert _route(module.get_prompt, "server-1", 3)[1] == 200


def test_mcp_resource_and_prompt_validation_boundaries(monkeypatch):
    module, _session, server, _resource, _prompt, _manager = _install(monkeypatch)
    app = Flask(__name__)
    module.MCPServerModel.query = _Query(first=None)
    with app.test_request_context("/resource"):
        assert _route(module.read_resource, "missing", 2)[1] == 404
    with app.test_request_context("/prompt", method="POST", json={}):
        assert _route(module.get_prompt, "missing", 3)[1] == 404

    module, _session, server, _resource, _prompt, _manager = _install(monkeypatch)
    module.MCPResource.query = _Query(first=None)
    module.MCPPrompt.query = _Query(first=None)
    with app.test_request_context("/resource"):
        assert _route(module.read_resource, "server-1", 99)[1] == 404
    with app.test_request_context("/prompt", method="POST", json={}):
        assert _route(module.get_prompt, "server-1", 99)[1] == 404

    module, _session, server, _resource, _prompt, _manager = _install(monkeypatch)
    monkeypatch.setattr(module, "_active_consent", lambda _server: None)
    with app.test_request_context("/resource"):
        assert _route(module.read_resource, "server-1", 2)[1] == 403
    with app.test_request_context("/prompt", method="POST", json={}):
        assert _route(module.get_prompt, "server-1", 3)[1] == 403

    module, _session, server, _resource, _prompt, _manager = _install(monkeypatch)
    server.status = "inactive"
    with app.test_request_context("/resource"):
        assert _route(module.read_resource, "server-1", 2)[1] == 409
    with app.test_request_context("/prompt", method="POST", json={}):
        assert _route(module.get_prompt, "server-1", 3)[1] == 409
    server.status = "active"
    with app.test_request_context("/prompt", method="POST", json={"arguments": []}):
        assert _route(module.get_prompt, "server-1", 3)[1] == 400


def test_mcp_resource_and_prompt_failure_and_cancel_paths(monkeypatch):
    module, session, server, _resource, _prompt, manager = _install(monkeypatch, manager_server=False)
    app = Flask(__name__)
    with app.test_request_context("/resource"):
        result = _route(module.read_resource, "server-1", 2)
        assert result[1] == 500 and result[0].get_json()["code"] == "MCP_SERVER_NOT_RUNNING"
    with app.test_request_context("/prompt", method="POST", json={}):
        result = _route(module.get_prompt, "server-1", 3)
        assert result[1] == 500 and result[0].get_json()["code"] == "MCP_SERVER_NOT_RUNNING"
    assert server.failed_requests == 2

    module, session, _server, _resource, _prompt, _manager = _install(monkeypatch, manager_server=False)
    session.refresh_status = "cancelled"
    with app.test_request_context("/resource"):
        assert _route(module.read_resource, "server-1", 2)[1] == 409
    with app.test_request_context("/prompt", method="POST", json={}):
        assert _route(module.get_prompt, "server-1", 3)[1] == 409
