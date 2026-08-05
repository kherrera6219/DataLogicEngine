"""KA-055: content-free multimodal evidence integration proposals."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA055Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    modal_evidence: list[dict[str, Any]] = Field(
        default_factory=list, max_length=10_000
    )
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)


class KA055AdaptiveMultiModalIntegration(KnowledgeAlgorithm):
    """Summarize declared modality measurements without copying evidence content."""

    input_schema = KA055Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-055"

    def _run_logic(self, input_data: KA055Input) -> dict[str, Any]:
        by_topic: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for index, item in enumerate(input_data.modal_evidence, start=1):
            evidence_id = str(item.get("evidence_id") or f"evidence-{index}")
            topic_id = str(item.get("topic_id") or item.get("topic") or "unspecified")
            score = item.get("measured_score", item.get("confidence"))
            by_topic[topic_id].append(
                {
                    "evidence_id": evidence_id,
                    "modality": str(item.get("modality") or "unknown"),
                    "declared_verdict": str(item.get("verdict") or "unspecified"),
                    "measured_score": (
                        round(max(0.0, min(1.0, float(score))), 8)
                        if isinstance(score, (int, float))
                        else None
                    ),
                }
            )
        topic_reviews = []
        for topic_id, rows in sorted(by_topic.items()):
            verdicts = {row["declared_verdict"] for row in rows}
            topic_reviews.append(
                {
                    "topic_id": topic_id,
                    "evidence_ids": sorted(row["evidence_id"] for row in rows),
                    "modalities": sorted({row["modality"] for row in rows}),
                    "declared_verdict_count": len(verdicts),
                    "disagreement_detected": len(verdicts) > 1,
                    "measured_score_count": sum(
                        row["measured_score"] is not None for row in rows
                    ),
                }
            )
        return {
            "success": True,
            "status": "multimodal_integration_reviewed",
            "topic_reviews": topic_reviews,
            "disagreement_topic_ids": [
                row["topic_id"] for row in topic_reviews if row["disagreement_detected"]
            ],
            "dependencies_consumed": sorted(input_data.dependency_results),
            "source_content_returned": False,
            "fusion_applied": False,
            "deterministic": True,
            "limitations": (
                "The review uses declared modality metadata and scores. It does "
                "not inspect media, authenticate evidence, resolve disagreements, "
                "or persist a fused record."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA055AdaptiveMultiModalIntegration(context).run(context)
