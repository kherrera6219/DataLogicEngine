"""
Latency SLO baseline evaluation for AI and connector paths.
"""

from __future__ import annotations

import os
from typing import Any, Dict

from backend.llm_gateway.latency_metrics import ai_latency_metrics_snapshot
from backend.mcp_server.connector_metrics import connector_metrics_snapshot


def _float_env(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return float(default)
    try:
        return float(raw)
    except (TypeError, ValueError):
        return float(default)


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return int(default)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return int(default)


def latency_slo_thresholds() -> Dict[str, float]:
    return {
        "ai_p95_ms": _float_env("AI_LATENCY_SLO_P95_MS", 2000.0),
        "ai_p99_ms": _float_env("AI_LATENCY_SLO_P99_MS", 5000.0),
        "connector_p95_ms": _float_env("CONNECTOR_LATENCY_SLO_P95_MS", 1500.0),
        "connector_p99_ms": _float_env("CONNECTOR_LATENCY_SLO_P99_MS", 4000.0),
        "min_samples": float(_int_env("LATENCY_SLO_MIN_SAMPLES", 20)),
    }


def evaluate_latency_slos(
    *,
    ai_snapshot: Dict[str, Any] | None = None,
    connector_snapshot: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    thresholds = latency_slo_thresholds()
    min_samples = int(thresholds["min_samples"])
    ai = ai_snapshot if ai_snapshot is not None else ai_latency_metrics_snapshot()
    connectors = connector_snapshot if connector_snapshot is not None else connector_metrics_snapshot()

    ai_results: Dict[str, Dict[str, Any]] = {}
    for provider, metrics in {"all": ai.get("all", {}), **(ai.get("providers", {}) or {})}.items():
        calls = int(metrics.get("calls", 0))
        p95 = float(metrics.get("p95_latency_ms", 0.0))
        p99 = float(metrics.get("p99_latency_ms", 0.0))
        active = calls >= min_samples
        ai_results[provider] = {
            "calls": calls,
            "active": active,
            "p95_violation": bool(active and p95 > thresholds["ai_p95_ms"]),
            "p99_violation": bool(active and p99 > thresholds["ai_p99_ms"]),
        }

    connector_results: Dict[str, Dict[str, Any]] = {}
    any_p95 = False
    any_p99 = False
    for connector_id, metrics in (connectors or {}).items():
        calls = int(metrics.get("calls", 0))
        p95 = float(metrics.get("p95_latency_ms", 0.0))
        p99 = float(metrics.get("p99_latency_ms", 0.0))
        active = calls >= min_samples
        p95_violation = bool(active and p95 > thresholds["connector_p95_ms"])
        p99_violation = bool(active and p99 > thresholds["connector_p99_ms"])
        any_p95 = any_p95 or p95_violation
        any_p99 = any_p99 or p99_violation
        connector_results[connector_id] = {
            "calls": calls,
            "active": active,
            "p95_violation": p95_violation,
            "p99_violation": p99_violation,
        }

    connector_results["all"] = {
        "calls": int(sum(int(item.get("calls", 0)) for item in connector_results.values() if isinstance(item, dict) and "calls" in item)),
        "active": bool(connector_results),
        "p95_violation": any_p95,
        "p99_violation": any_p99,
    }

    return {
        "thresholds": thresholds,
        "ai": ai_results,
        "connectors": connector_results,
    }


def latency_slo_prometheus_lines(prefix: str = "datalogicengine") -> list[str]:
    evaluation = evaluate_latency_slos()
    thresholds = evaluation["thresholds"]
    lines = [
        f"# HELP {prefix}_latency_slo_ai_p95_ms_target Configured AI latency SLO p95 threshold in milliseconds.",
        f"# TYPE {prefix}_latency_slo_ai_p95_ms_target gauge",
        f"{prefix}_latency_slo_ai_p95_ms_target {thresholds['ai_p95_ms']:.3f}",
        f"# HELP {prefix}_latency_slo_ai_p99_ms_target Configured AI latency SLO p99 threshold in milliseconds.",
        f"# TYPE {prefix}_latency_slo_ai_p99_ms_target gauge",
        f"{prefix}_latency_slo_ai_p99_ms_target {thresholds['ai_p99_ms']:.3f}",
        f"# HELP {prefix}_latency_slo_connector_p95_ms_target Configured connector latency SLO p95 threshold in milliseconds.",
        f"# TYPE {prefix}_latency_slo_connector_p95_ms_target gauge",
        f"{prefix}_latency_slo_connector_p95_ms_target {thresholds['connector_p95_ms']:.3f}",
        f"# HELP {prefix}_latency_slo_connector_p99_ms_target Configured connector latency SLO p99 threshold in milliseconds.",
        f"# TYPE {prefix}_latency_slo_connector_p99_ms_target gauge",
        f"{prefix}_latency_slo_connector_p99_ms_target {thresholds['connector_p99_ms']:.3f}",
        f"# HELP {prefix}_ai_latency_slo_violation AI latency SLO violation flag (1=violation, 0=within target).",
        f"# TYPE {prefix}_ai_latency_slo_violation gauge",
        f"# HELP {prefix}_connector_latency_slo_violation Connector latency SLO violation flag (1=violation, 0=within target).",
        f"# TYPE {prefix}_connector_latency_slo_violation gauge",
    ]

    for provider, data in sorted(evaluation["ai"].items()):
        labels = f'{{provider="{provider}",percentile="p95"}}'
        lines.append(f"{prefix}_ai_latency_slo_violation{labels} {1 if data['p95_violation'] else 0}")
        labels = f'{{provider="{provider}",percentile="p99"}}'
        lines.append(f"{prefix}_ai_latency_slo_violation{labels} {1 if data['p99_violation'] else 0}")

    for connector, data in sorted(evaluation["connectors"].items()):
        labels = f'{{connector="{connector}",percentile="p95"}}'
        lines.append(f"{prefix}_connector_latency_slo_violation{labels} {1 if data['p95_violation'] else 0}")
        labels = f'{{connector="{connector}",percentile="p99"}}'
        lines.append(f"{prefix}_connector_latency_slo_violation{labels} {1 if data['p99_violation'] else 0}")

    return lines
