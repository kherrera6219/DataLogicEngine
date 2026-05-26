"""Bridge helpers for Phase C quad-persona pod orchestration."""

from __future__ import annotations

from typing import Any

from quad_persona.pod_models import ExpansionPlan, ScalingDecision, SufficiencySignals


def scaling_decision_from_sufficiency(sufficiency: dict[str, Any]) -> ScalingDecision:
    """Convert PersonaSufficiencyTool output into PodOrchestrator input."""
    spawn = sufficiency.get("spawn") if isinstance(sufficiency.get("spawn"), dict) else {}
    scores = sufficiency.get("scores") if isinstance(sufficiency.get("scores"), dict) else {}
    reasons = sufficiency.get("reasons") if isinstance(sufficiency.get("reasons"), list) else []

    expansion_plan = ExpansionPlan(
        spawn_counts={
            "knowledge": int(spawn.get("knowledge", 0) or 0),
            "sector": int(spawn.get("sector", 0) or 0),
            "regulatory": int(spawn.get("regulatory", 0) or 0),
            "compliance": int(spawn.get("compliance", 0) or 0),
        },
        subsystems_to_spawn=sufficiency.get("subsystems_to_spawn", {}) or {},
        reasons=[str(reason) for reason in reasons],
        caps=sufficiency.get("caps", {}) or {},
        stop_conditions=sufficiency.get("stop_conditions", []) or [],
    )

    signals = SufficiencySignals(
        complexity_score=float(scores.get("complexity", 0.0) or 0.0) * 100,
        stakes_score=float(scores.get("stake", 0.0) or 0.0) * 100,
        conflict_score=float(scores.get("conflict", 0.0) or 0.0),
        coverage_score=float(scores.get("coverage", 1.0) or 1.0),
    )

    return ScalingDecision(
        mode=str(sufficiency.get("mode") or "quad_only"),
        signals=signals,
        expansion_plan=expansion_plan,
        thresholds_used=sufficiency.get("thresholds", {}) or {},
    )


def orchestration_summary(state: Any) -> dict[str, Any]:
    """Return a compact, JSON-safe summary for traces and status surfaces."""
    pods = getattr(state, "pods", {}) or {}
    pod_summaries = {
        pod_type: {
            "persona_count": pod.persona_count,
            "collective_confidence": pod.collective_confidence,
            "status": pod.status,
        }
        for pod_type, pod in pods.items()
    }
    return {
        "mode": getattr(getattr(state, "scaling_decision", None), "mode", "quad_only"),
        "pod_count": len(pods),
        "collective_confidence": float(getattr(state, "final_confidence", 0.0) or 0.0),
        "threshold_met": bool(getattr(state, "threshold_met", False)),
        "pods": pod_summaries,
        "status": getattr(state, "status", "unknown"),
    }
