import asyncio
import importlib
import sys
import types
from unittest.mock import MagicMock, patch

import pytest

from backend.llm_gateway.latency_metrics import (
    ai_latency_metrics_prometheus_lines,
    ai_latency_metrics_snapshot,
    record_ai_request,
    reset_ai_latency_metrics,
)
from backend.mcp_server.contract_validation import ContractValidationError
from backend.mcp_server.registry import ToolRegistry


def test_registry_rejects_input_contract_violation():
    registry = ToolRegistry()

    @registry.register(
        name="contract_input_tool",
        description="contract input",
        input_schema={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        output_schema={"type": "object", "properties": {"status": {"type": "string"}}, "required": ["status"]},
    )
    def contract_input_tool(query: str):
        return {"status": f"ok:{query}"}

    with pytest.raises(ContractValidationError):
        asyncio.run(registry.execute_tool("contract_input_tool", {}))


def test_registry_rejects_output_contract_violation():
    registry = ToolRegistry()

    @registry.register(
        name="contract_output_tool",
        description="contract output",
        input_schema={"type": "object", "properties": {}},
        output_schema={"type": "object", "properties": {"status": {"type": "string"}}, "required": ["status"]},
    )
    def contract_output_tool():
        return {"unexpected": True}

    with pytest.raises(ContractValidationError):
        asyncio.run(registry.execute_tool("contract_output_tool", {}))


def test_ai_latency_metrics_export_percentiles():
    reset_ai_latency_metrics()
    record_ai_request(provider="openai", duration_ms=100.0, success=True)
    record_ai_request(provider="openai", duration_ms=200.0, success=True)
    record_ai_request(provider="openai", duration_ms=400.0, success=False)

    snapshot = ai_latency_metrics_snapshot()
    assert snapshot["all"]["calls"] == 3
    assert snapshot["providers"]["openai"]["errors"] == 1
    assert snapshot["providers"]["openai"]["p95_latency_ms"] >= 200.0

    lines = "\n".join(ai_latency_metrics_prometheus_lines(prefix="datalogicengine"))
    assert 'datalogicengine_ai_latency_ms_p95{provider="openai"}' in lines
    assert 'datalogicengine_ai_requests_total{provider="all"} 3' in lines


def test_jira_client_prefers_managed_oauth(monkeypatch):
    fake_jira_module = types.SimpleNamespace(JIRA=MagicMock())
    with patch.dict(sys.modules, {"jira": fake_jira_module}):
        sys.modules.pop("backend.mcp_server.tools.jira", None)
        jira_tools = importlib.import_module("backend.mcp_server.tools.jira")

    monkeypatch.setenv("JIRA_SERVER_URL", "https://jira.example.com")

    mock_client = MagicMock()
    with patch.object(jira_tools, "JIRA", return_value=mock_client) as jira_ctor, patch.object(
        jira_tools,
        "get_connector_oauth_token",
        return_value={"access_token": "oauth-token"},
    ):
        client = jira_tools.get_jira_client({"user_id": "12"})
        assert client is mock_client
        jira_ctor.assert_called_once()
        assert jira_ctor.call_args.kwargs["token_auth"] == "oauth-token"


def test_salesforce_client_prefers_managed_oauth(monkeypatch):
    fake_sf_module = types.SimpleNamespace(Salesforce=MagicMock())
    with patch.dict(sys.modules, {"simple_salesforce": fake_sf_module}):
        sys.modules.pop("backend.mcp_server.tools.salesforce", None)
        sf_tools = importlib.import_module("backend.mcp_server.tools.salesforce")

    monkeypatch.setenv("SALESFORCE_DOMAIN", "login")

    mock_client = MagicMock()
    with patch.object(sf_tools, "Salesforce", return_value=mock_client) as sf_ctor, patch.object(
        sf_tools,
        "get_connector_oauth_token",
        return_value={"access_token": "oauth-token", "instance_url": "https://instance.salesforce.com"},
    ):
        client = sf_tools.get_salesforce_client({"user_id": "99"})
        assert client is mock_client
        sf_ctor.assert_called_once()
        assert sf_ctor.call_args.kwargs["session_id"] == "oauth-token"
        assert sf_ctor.call_args.kwargs["instance_url"] == "https://instance.salesforce.com"

