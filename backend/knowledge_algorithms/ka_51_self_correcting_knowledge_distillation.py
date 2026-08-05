"""KA-051: bounded knowledge-distillation proposal generation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.knowledge_algorithms.production_utils import stable_identifier
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA051Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    traces: list[dict[str, Any]] = Field(default_factory=list, max_length=10_000)
    minimum_measured_score: float = Field(default=0.9, ge=0, le=1)
    maximum_candidates: int = Field(default=5, ge=1, le=100)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)


class KA051SelfCorrectingKnowledgeDistillation(KnowledgeAlgorithm):
    """Propose reusable pattern identifiers from explicitly measured traces."""

    input_schema = KA051Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-051"

    def _run_logic(self, input_data: KA051Input) -> dict[str, Any]:
        candidates = []
        for trace in sorted(
            input_data.traces,
            key=lambda row: str(row.get("trace_id") or row.get("id") or ""),
        ):
            trace_id = str(trace.get("trace_id") or trace.get("id") or "").strip()
            pattern_id = str(trace.get("pattern_id") or "").strip()
            score = trace.get("measured_score", trace.get("confidence"))
            if not trace_id or not pattern_id or not isinstance(score, (int, float)):
                continue
            if (
                not 0 <= float(score) <= 1
                or float(score) < input_data.minimum_measured_score
            ):
                continue
            candidates.append(
                {
                    "candidate_id": stable_identifier(
                        "distillation", {"trace_id": trace_id, "pattern_id": pattern_id}
                    ),
                    "source_trace_id": trace_id,
                    "pattern_id": pattern_id,
                    "measured_score": round(float(score), 8),
                    "requires_release_review": True,
                }
            )
        candidates = candidates[: input_data.maximum_candidates]
        return {
            "success": True,
            "status": "distillation_candidates_proposed",
            "distillation_candidates": candidates,
            "candidate_count": len(candidates),
            "dependencies_consumed": sorted(input_data.dependency_results),
            "knowledge_changes_applied": False,
            "provider_subcalls_used": 0,
            "deterministic": True,
            "limitations": (
                "Candidates require explicit measured trace scores and contain "
                "identifiers only. They are not learned rules and no knowledge "
                "content is persisted or promoted."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA051SelfCorrectingKnowledgeDistillation(context).run(context)
