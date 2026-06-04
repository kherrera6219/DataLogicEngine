"""
Low-cardinality connector latency metrics for MCP tool execution.
"""

from __future__ import annotations

from collections import deque
from threading import Lock
from typing import Any, Dict, Optional

KNOWN_CONNECTORS = {
    "github",
    "slack",
    "servicenow",
    "snowflake",
    "notion",
    "hubspot",
    "zendesk",
    "sap",
}

_METRICS_LOCK = Lock()
_CONNECTOR_METRICS: Dict[str, Dict[str, Any]] = {}


def infer_connector_id(tool_name: str, declared_connector: Optional[str] = None) -> Optional[str]:
    connector = (declared_connector or "").strip().lower()
    if connector:
        return connector
    if not tool_name:
        return None
    prefix = tool_name.split("_", 1)[0].strip().lower()
    if prefix in KNOWN_CONNECTORS:
        return prefix
    return None


def _init_connector_metrics(connector_id: str) -> Dict[str, Any]:
    existing = _CONNECTOR_METRICS.get(connector_id)
    if existing is not None:
        return existing
    state = {
        "calls": 0,
        "errors": 0,
        "total_latency_ms": 0.0,
        "max_latency_ms": 0.0,
        "latencies_ms": deque(maxlen=2048),
    }
    _CONNECTOR_METRICS[connector_id] = state
    return state


def record_connector_execution(
    *,
    tool_name: str,
    duration_ms: float,
    success: bool,
    connector_id: Optional[str] = None,
) -> None:
    """Record connector call metrics for observability dashboards and /metrics."""
    normalized_connector = infer_connector_id(tool_name, declared_connector=connector_id)
    if not normalized_connector:
        return

    latency_ms = max(0.0, float(duration_ms))
    with _METRICS_LOCK:
        state = _init_connector_metrics(normalized_connector)
        state["calls"] += 1
        if not success:
            state["errors"] += 1
        state["total_latency_ms"] += latency_ms
        state["max_latency_ms"] = max(state["max_latency_ms"], latency_ms)
        state["latencies_ms"].append(latency_ms)


def _percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = int(round((len(sorted_values) - 1) * quantile))
    index = max(0, min(index, len(sorted_values) - 1))
    return float(sorted_values[index])


def connector_metrics_snapshot() -> Dict[str, Dict[str, float]]:
    """Return summarized connector latency metrics."""
    with _METRICS_LOCK:
        snapshot: Dict[str, Dict[str, float]] = {}
        for connector_id, state in _CONNECTOR_METRICS.items():
            calls = int(state["calls"])
            errors = int(state["errors"])
            latencies = list(state["latencies_ms"])
            avg_latency = (float(state["total_latency_ms"]) / calls) if calls > 0 else 0.0
            snapshot[connector_id] = {
                "calls": float(calls),
                "errors": float(errors),
                "avg_latency_ms": avg_latency,
                "p95_latency_ms": _percentile(latencies, 0.95),
                "p99_latency_ms": _percentile(latencies, 0.99),
                "max_latency_ms": float(state["max_latency_ms"]),
            }
        return snapshot


def reset_connector_metrics() -> None:
    """Reset connector metrics (used by deterministic tests)."""
    with _METRICS_LOCK:
        _CONNECTOR_METRICS.clear()


def connector_metrics_prometheus_lines(prefix: str = "datalogicengine") -> list[str]:
    """Render connector metrics as Prometheus exposition lines."""
    snapshot = connector_metrics_snapshot()
    if not snapshot:
        return []

    lines = [
        f"# HELP {prefix}_connector_requests_total Total connector requests by connector.",
        f"# TYPE {prefix}_connector_requests_total counter",
        f"# HELP {prefix}_connector_errors_total Total connector failures by connector.",
        f"# TYPE {prefix}_connector_errors_total counter",
        f"# HELP {prefix}_connector_latency_ms_avg Average connector latency in milliseconds.",
        f"# TYPE {prefix}_connector_latency_ms_avg gauge",
        f"# HELP {prefix}_connector_latency_ms_p95 P95 connector latency in milliseconds.",
        f"# TYPE {prefix}_connector_latency_ms_p95 gauge",
        f"# HELP {prefix}_connector_latency_ms_p99 P99 connector latency in milliseconds.",
        f"# TYPE {prefix}_connector_latency_ms_p99 gauge",
        f"# HELP {prefix}_connector_latency_ms_max Maximum connector latency in milliseconds.",
        f"# TYPE {prefix}_connector_latency_ms_max gauge",
    ]

    for connector_id in sorted(snapshot):
        data = snapshot[connector_id]
        labels = f'{{connector="{connector_id}"}}'
        lines.append(f"{prefix}_connector_requests_total{labels} {int(data['calls'])}")
        lines.append(f"{prefix}_connector_errors_total{labels} {int(data['errors'])}")
        lines.append(f"{prefix}_connector_latency_ms_avg{labels} {data['avg_latency_ms']:.3f}")
        lines.append(f"{prefix}_connector_latency_ms_p95{labels} {data['p95_latency_ms']:.3f}")
        lines.append(f"{prefix}_connector_latency_ms_p99{labels} {data['p99_latency_ms']:.3f}")
        lines.append(f"{prefix}_connector_latency_ms_max{labels} {data['max_latency_ms']:.3f}")
    return lines
