from backend.llm_gateway.latency_metrics import (
    record_ai_request,
    reset_ai_latency_metrics,
)
from backend.mcp_server.connector_metrics import (
    connector_metrics_prometheus_lines,
    connector_metrics_snapshot,
    record_connector_execution,
    reset_connector_metrics,
)
from backend.observability.latency_slo import (
    evaluate_latency_slos,
    latency_slo_prometheus_lines,
)


def test_connector_metrics_include_p99_latency():
    reset_connector_metrics()
    record_connector_execution(tool_name="jira_search", duration_ms=50, success=True)
    record_connector_execution(tool_name="jira_search", duration_ms=200, success=True)

    snapshot = connector_metrics_snapshot()
    assert snapshot["jira"]["p99_latency_ms"] >= snapshot["jira"]["p95_latency_ms"]

    payload = "\n".join(connector_metrics_prometheus_lines(prefix="datalogicengine"))
    assert 'datalogicengine_connector_latency_ms_p99{connector="jira"}' in payload


def test_latency_slo_evaluation_flags_ai_and_connector_violations(monkeypatch):
    reset_ai_latency_metrics()
    reset_connector_metrics()

    monkeypatch.setenv("LATENCY_SLO_MIN_SAMPLES", "2")
    monkeypatch.setenv("AI_LATENCY_SLO_P95_MS", "100")
    monkeypatch.setenv("AI_LATENCY_SLO_P99_MS", "150")
    monkeypatch.setenv("CONNECTOR_LATENCY_SLO_P95_MS", "80")
    monkeypatch.setenv("CONNECTOR_LATENCY_SLO_P99_MS", "120")

    record_ai_request(provider="openai", duration_ms=120, success=True)
    record_ai_request(provider="openai", duration_ms=220, success=True)

    record_connector_execution(tool_name="jira_search", duration_ms=90, success=True)
    record_connector_execution(tool_name="jira_search", duration_ms=220, success=True)

    evaluation = evaluate_latency_slos()
    assert evaluation["ai"]["openai"]["p95_violation"] is True
    assert evaluation["ai"]["openai"]["p99_violation"] is True
    assert evaluation["connectors"]["jira"]["p95_violation"] is True
    assert evaluation["connectors"]["jira"]["p99_violation"] is True

    lines = "\n".join(latency_slo_prometheus_lines(prefix="datalogicengine"))
    assert 'datalogicengine_ai_latency_slo_violation{provider="openai",percentile="p95"} 1' in lines
    assert 'datalogicengine_connector_latency_slo_violation{connector="jira",percentile="p99"} 1' in lines
