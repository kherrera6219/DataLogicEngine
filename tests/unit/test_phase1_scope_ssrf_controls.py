import asyncio

import pytest

from backend.mcp_server.connector_metrics import connector_metrics_snapshot, reset_connector_metrics
from backend.mcp_server.registry import ToolRegistry
from backend.mcp_server.scope_enforcement import (
    ScopeEnforcementError,
    enforce_scopes,
    parse_execution_context,
)
from backend.security.ssrf import SSRFProtectionError, validate_outbound_url


def test_registry_connector_scope_enforcement_and_metrics():
    reset_connector_metrics()
    registry = ToolRegistry()

    @registry.register(
        name="jira_status_check",
        description="status",
        input_schema={"type": "object", "properties": {}},
        required_scopes=["mcp:execute", "connector:jira:read"],
        connector="jira",
    )
    def jira_status_check():
        return {"status": "ok"}

    with pytest.raises(ScopeEnforcementError):
        asyncio.run(
            registry.execute_tool(
                "jira_status_check",
                {},
                context={"scopes": ["mcp:execute"]},
            )
        )

    result = asyncio.run(
        registry.execute_tool(
            "jira_status_check",
            {},
            context={"scopes": ["mcp:execute", "connector:jira:read"]},
        )
    )
    assert result["status"] == "ok"

    metrics = connector_metrics_snapshot()
    assert metrics["jira"]["calls"] >= 1
    assert metrics["jira"]["avg_latency_ms"] >= 0


def test_scope_enforcement_strict_mode_requires_context(monkeypatch):
    monkeypatch.setenv("MCP_SCOPE_ENFORCEMENT_STRICT", "true")
    context = parse_execution_context({})
    with pytest.raises(ScopeEnforcementError):
        enforce_scopes(
            tool_name="salesforce_crm_lookup",
            required_scopes=["mcp:execute", "connector:salesforce:read"],
            context=context,
            permissive_on_missing_context=True,
        )


def test_ssrf_blocks_loopback_by_default():
    with pytest.raises(SSRFProtectionError):
        validate_outbound_url("http://127.0.0.1:5000/api/v1/graph/stats", allow_private_hosts=False)


def test_ssrf_allows_explicit_private_allowlist():
    result = validate_outbound_url(
        "http://127.0.0.1:5000/health",
        allowed_hosts={"127.0.0.1"},
        allow_private_hosts=True,
    )
    assert result.hostname == "127.0.0.1"
    assert result.resolved_ips
