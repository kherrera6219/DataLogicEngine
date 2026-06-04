import asyncio

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


# NOTE: test_jira_client_prefers_managed_oauth and
# test_salesforce_client_prefers_managed_oauth were removed. The Jira and
# Salesforce MCP connectors are legacy external SaaS integrations removed
# from this local-first / desktop-only build. Managed-OAuth contract
# behaviour remains covered by the connector framework tests above.
