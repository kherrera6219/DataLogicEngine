"""KA-1078: deterministic memory-tier classification."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class TierCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    knowledge_id: str = Field(min_length=1, max_length=200)
    validation_status: Literal["candidate", "validated", "disputed", "obsolete"]
    importance: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    age_days: int = Field(ge=0, le=100_000)
    reuse_count: int = Field(ge=0, le=1_000_000)


class KA1078Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "candidates": [
                        {
                            "knowledge_id": "knowledge-1",
                            "validation_status": "validated",
                            "importance": 0.9,
                            "confidence": 0.95,
                            "age_days": 5,
                            "reuse_count": 10,
                        }
                    ]
                }
            ]
        },
    )

    candidates: list[TierCandidate] = Field(min_length=1, max_length=20_000)
    long_term_importance: float = Field(default=0.7, ge=0, le=1)
    long_term_confidence: float = Field(default=0.8, ge=0, le=1)
    archive_age_days: int = Field(default=365, ge=0, le=100_000)

    @model_validator(mode="after")
    def validate_ids(self) -> KA1078Input:
        identifiers = [item.knowledge_id for item in self.candidates]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("knowledge IDs must be unique")
        return self


class KA1078MemoryTierClassifier(KnowledgeAlgorithm):
    """Classify memory tier without moving or persisting a record."""

    input_schema = KA1078Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1078"

    def _run_logic(self, input_data: KA1078Input) -> dict[str, Any]:
        classifications = []
        for item in sorted(input_data.candidates, key=lambda row: row.knowledge_id):
            if item.validation_status == "disputed":
                tier, reason = "quarantine", "disputed"
            elif item.validation_status == "obsolete":
                tier, reason = "archive", "obsolete"
            elif (
                item.age_days >= input_data.archive_age_days
                and item.reuse_count == 0
                and item.importance < input_data.long_term_importance
            ):
                tier, reason = "archive", "stale_unused_low_importance"
            elif (
                item.validation_status == "validated"
                and item.importance >= input_data.long_term_importance
                and item.confidence >= input_data.long_term_confidence
            ):
                tier, reason = "long_term", "validated_high_value"
            else:
                tier, reason = "working", "pending_or_active_context"
            classifications.append(
                {
                    "knowledge_id": item.knowledge_id,
                    "recommended_tier": tier,
                    "reason": reason,
                }
            )
        return {
            "success": True,
            "status": "memory_tiers_classified",
            "classifications": classifications,
            "tier_changes_applied": False,
            "deterministic": True,
            "limitations": (
                "Tier recommendations use supplied lifecycle metrics. The memory "
                "service must authorize and apply any movement."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1078MemoryTierClassifier(context).run(context)
