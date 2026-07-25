"""KA-1094: deterministic knowledge-quarantine admission proposals."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class QuarantineCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    knowledge_id: str = Field(min_length=1, max_length=200)
    validation_status: Literal["validated", "unvalidated", "disputed", "failed"]
    confidence: float = Field(ge=0, le=1)
    contradiction_count: int = Field(ge=0, le=1_000_000)
    integrity_valid: bool
    provenance_complete: bool


class KA1094Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "candidates": [
                        {
                            "knowledge_id": "knowledge-1",
                            "validation_status": "disputed",
                            "confidence": 0.5,
                            "contradiction_count": 1,
                            "integrity_valid": True,
                            "provenance_complete": True,
                        }
                    ]
                }
            ]
        },
    )

    candidates: list[QuarantineCandidate] = Field(min_length=1, max_length=20_000)
    minimum_confidence: float = Field(default=0.5, ge=0, le=1)

    @model_validator(mode="after")
    def validate_ids(self) -> KA1094Input:
        identifiers = [item.knowledge_id for item in self.candidates]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("knowledge IDs must be unique")
        return self


class KA1094KnowledgeQuarantineEngine(KnowledgeAlgorithm):
    """Return quarantine and release-review proposals without moving records."""

    input_schema = KA1094Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1094"

    def _run_logic(self, input_data: KA1094Input) -> dict[str, Any]:
        decisions = []
        for item in sorted(input_data.candidates, key=lambda row: row.knowledge_id):
            reasons = []
            if item.validation_status in {"disputed", "failed"}:
                reasons.append(f"validation_{item.validation_status}")
            if item.confidence < input_data.minimum_confidence:
                reasons.append("confidence_below_threshold")
            if item.contradiction_count:
                reasons.append("unresolved_contradictions")
            if not item.integrity_valid:
                reasons.append("integrity_invalid")
            if not item.provenance_complete:
                reasons.append("provenance_incomplete")
            decisions.append(
                {
                    "knowledge_id": item.knowledge_id,
                    "decision": "quarantine" if reasons else "retain",
                    "reasons": reasons,
                    "human_release_review_required": bool(reasons),
                }
            )
        return {
            "success": True,
            "status": "knowledge_quarantine_evaluated",
            "decisions": decisions,
            "records_moved": 0,
            "effect_service_required": True,
            "deterministic": True,
            "limitations": (
                "This is an admission proposal based on supplied validation "
                "signals. The knowledge service must transact any quarantine."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1094KnowledgeQuarantineEngine(context).run(context)
