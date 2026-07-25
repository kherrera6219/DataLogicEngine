"""KA-1079: deterministic policy gate for long-term knowledge promotion."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA1079Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "knowledge_id": "knowledge-1",
                    "validation_status": "validated",
                    "confidence": 0.9,
                    "evidence_count": 3,
                    "citation_count": 2,
                    "contradiction_count": 0,
                    "provenance_complete": True,
                    "risk_class": "medium",
                }
            ]
        },
    )

    knowledge_id: str = Field(min_length=1, max_length=200)
    validation_status: Literal["unvalidated", "validated", "disputed"]
    confidence: float = Field(ge=0, le=1)
    evidence_count: int = Field(ge=0, le=1_000_000)
    citation_count: int = Field(ge=0, le=1_000_000)
    contradiction_count: int = Field(ge=0, le=1_000_000)
    provenance_complete: bool
    risk_class: Literal["low", "medium", "high", "critical"]
    minimum_confidence: float = Field(default=0.8, ge=0, le=1)
    minimum_evidence_count: int = Field(default=2, ge=0, le=10_000)
    minimum_citation_count: int = Field(default=1, ge=0, le=10_000)


class KA1079KnowledgePromotionGate(KnowledgeAlgorithm):
    """Return a promotion decision without writing or promoting knowledge."""

    input_schema = KA1079Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1079"

    def _run_logic(self, input_data: KA1079Input) -> dict[str, Any]:
        failures = []
        if input_data.validation_status != "validated":
            failures.append("validation_not_passed")
        if input_data.confidence < input_data.minimum_confidence:
            failures.append("confidence_below_threshold")
        if input_data.evidence_count < input_data.minimum_evidence_count:
            failures.append("insufficient_evidence")
        if input_data.citation_count < input_data.minimum_citation_count:
            failures.append("insufficient_citations")
        if input_data.contradiction_count:
            failures.append("unresolved_contradictions")
        if not input_data.provenance_complete:
            failures.append("provenance_incomplete")
        if input_data.risk_class == "critical":
            failures.append("critical_risk_requires_human_approval")

        review_only = failures == ["critical_risk_requires_human_approval"]
        decision = (
            "approve" if not failures else "human_review" if review_only else "reject"
        )
        return {
            "success": True,
            "status": "promotion_evaluated",
            "knowledge_id": input_data.knowledge_id,
            "decision": decision,
            "failed_criteria": failures,
            "promotion_applied": False,
            "deterministic": True,
            "limitations": (
                "This is a policy decision only. The owning knowledge service "
                "must authorize and apply any promotion."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1079KnowledgePromotionGate(context).run(context)
