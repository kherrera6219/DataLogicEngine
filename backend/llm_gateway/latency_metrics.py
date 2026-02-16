"""
Low-cardinality AI latency and reliability metrics for gateway requests.
"""

from __future__ import annotations

import re
from collections import deque
from threading import Lock
from typing import Any, Dict, Optional

KNOWN_PROVIDER_LABELS = {
    "openai",
    "azure_openai",
    "anthropic",
    "google",
    "gemini",
    "mistral",
    "local_slm",
    "ollama",
    "vllm",
    "cohere",
    "bedrock",
    "unknown",
    "none",
}

_LOCK = Lock()
_GLOBAL_METRICS: Dict[str, Any] = {
    "calls": 0,
    "errors": 0,
    "total_latency_ms": 0.0,
    "max_latency_ms": 0.0,
    "latencies_ms": deque(maxlen=4096),
}
_PROVIDER_METRICS: Dict[str, Dict[str, Any]] = {}


def record_ai_request(
    *,
    provider: Optional[str],
    duration_ms: float,
    success: bool,
) -> None:
    """Record a gateway provider attempt for operational telemetry."""
    provider_label = _normalize_provider_label(provider)
    latency_ms = max(0.0, float(duration_ms))
    with _LOCK:
        _record(_GLOBAL_METRICS, latency_ms, success)
        provider_state = _PROVIDER_METRICS.get(provider_label)
        if provider_state is None:
            provider_state = {
                "calls": 0,
                "errors": 0,
                "total_latency_ms": 0.0,
                "max_latency_ms": 0.0,
                "latencies_ms": deque(maxlen=2048),
            }
            _PROVIDER_METRICS[provider_label] = provider_state
        _record(provider_state, latency_ms, success)


def ai_latency_metrics_snapshot() -> Dict[str, Any]:
    """Return aggregate + provider-level AI latency metrics snapshot."""
    with _LOCK:
        return {
            "all": _summarize(_GLOBAL_METRICS),
            "providers": {provider: _summarize(state) for provider, state in _PROVIDER_METRICS.items()},
        }


def reset_ai_latency_metrics() -> None:
    """Reset in-memory AI latency metrics (used by deterministic tests)."""
    with _LOCK:
        _GLOBAL_METRICS["calls"] = 0
        _GLOBAL_METRICS["errors"] = 0
        _GLOBAL_METRICS["total_latency_ms"] = 0.0
        _GLOBAL_METRICS["max_latency_ms"] = 0.0
        _GLOBAL_METRICS["latencies_ms"].clear()
        _PROVIDER_METRICS.clear()


def ai_latency_metrics_prometheus_lines(prefix: str = "datalogicengine") -> list[str]:
    """Render AI latency metrics as Prometheus exposition lines."""
    snapshot = ai_latency_metrics_snapshot()
    aggregate = snapshot["all"]
    providers = snapshot["providers"]

    lines = [
        f"# HELP {prefix}_ai_requests_total Total AI provider requests.",
        f"# TYPE {prefix}_ai_requests_total counter",
        f"# HELP {prefix}_ai_errors_total Total AI provider request failures.",
        f"# TYPE {prefix}_ai_errors_total counter",
        f"# HELP {prefix}_ai_latency_ms_avg Average AI request latency in milliseconds.",
        f"# TYPE {prefix}_ai_latency_ms_avg gauge",
        f"# HELP {prefix}_ai_latency_ms_p50 P50 AI request latency in milliseconds.",
        f"# TYPE {prefix}_ai_latency_ms_p50 gauge",
        f"# HELP {prefix}_ai_latency_ms_p95 P95 AI request latency in milliseconds.",
        f"# TYPE {prefix}_ai_latency_ms_p95 gauge",
        f"# HELP {prefix}_ai_latency_ms_p99 P99 AI request latency in milliseconds.",
        f"# TYPE {prefix}_ai_latency_ms_p99 gauge",
        f"# HELP {prefix}_ai_latency_ms_max Maximum AI request latency in milliseconds.",
        f"# TYPE {prefix}_ai_latency_ms_max gauge",
    ]

    lines.extend(_render_prometheus_row(prefix, "all", aggregate))
    for provider in sorted(providers):
        lines.extend(_render_prometheus_row(prefix, provider, providers[provider]))
    return lines


def _record(state: Dict[str, Any], latency_ms: float, success: bool) -> None:
    state["calls"] += 1
    if not success:
        state["errors"] += 1
    state["total_latency_ms"] += latency_ms
    state["max_latency_ms"] = max(float(state["max_latency_ms"]), latency_ms)
    state["latencies_ms"].append(latency_ms)


def _summarize(state: Dict[str, Any]) -> Dict[str, float]:
    calls = int(state.get("calls", 0))
    total_latency = float(state.get("total_latency_ms", 0.0))
    latencies = list(state.get("latencies_ms", []))
    avg_latency = (total_latency / calls) if calls > 0 else 0.0
    return {
        "calls": float(calls),
        "errors": float(int(state.get("errors", 0))),
        "avg_latency_ms": avg_latency,
        "p50_latency_ms": _percentile(latencies, 0.50),
        "p95_latency_ms": _percentile(latencies, 0.95),
        "p99_latency_ms": _percentile(latencies, 0.99),
        "max_latency_ms": float(state.get("max_latency_ms", 0.0)),
    }


def _render_prometheus_row(prefix: str, provider: str, data: Dict[str, float]) -> list[str]:
    labels = f'{{provider="{provider}"}}'
    return [
        f"{prefix}_ai_requests_total{labels} {int(data['calls'])}",
        f"{prefix}_ai_errors_total{labels} {int(data['errors'])}",
        f"{prefix}_ai_latency_ms_avg{labels} {data['avg_latency_ms']:.3f}",
        f"{prefix}_ai_latency_ms_p50{labels} {data['p50_latency_ms']:.3f}",
        f"{prefix}_ai_latency_ms_p95{labels} {data['p95_latency_ms']:.3f}",
        f"{prefix}_ai_latency_ms_p99{labels} {data['p99_latency_ms']:.3f}",
        f"{prefix}_ai_latency_ms_max{labels} {data['max_latency_ms']:.3f}",
    ]


def _percentile(values: list[float], quantile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = int(round((len(ordered) - 1) * quantile))
    index = max(0, min(index, len(ordered) - 1))
    return float(ordered[index])


def _normalize_provider_label(provider: Optional[str]) -> str:
    raw = str(provider or "").strip().lower()
    if not raw:
        return "unknown"
    cleaned = re.sub(r"[^a-z0-9_]+", "_", raw).strip("_")
    if not cleaned:
        return "unknown"
    if cleaned in KNOWN_PROVIDER_LABELS:
        return cleaned
    return "other"

