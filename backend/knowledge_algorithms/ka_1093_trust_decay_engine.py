"""KA-1093: deterministic trust-decay proposal calculation."""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class TrustRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    knowledge_id: str = Field(min_length=1, max_length=200)
    current_trust: float = Field(ge=0, le=1)
    last_used_on: date
    risk_class: Literal["low", "medium", "high", "critical"]
    active_evidence_count: int = Field(ge=0, le=1_000_000)


class KA1093Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "reference_date": "2026-07-25",
                    "records": [
                        {
                            "knowledge_id": "knowledge-1",
                            "current_trust": 0.8,
                            "last_used_on": "2025-07-25",
                            "risk_class": "medium",
                            "active_evidence_count": 1,
                        }
                    ],
                }
            ]
        },
    )

    reference_date: date
    records: list[TrustRecord] = Field(min_length=1, max_length=20_000)
    half_life_days: int = Field(default=365, ge=1, le=100_000)
    evidence_floor: float = Field(default=0.1, ge=0, le=1)

    @model_validator(mode="after")
    def validate_records(self) -> KA1093Input:
        identifiers = [item.knowledge_id for item in self.records]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("knowledge IDs must be unique")
        if any(item.last_used_on > self.reference_date for item in self.records):
            raise ValueError("last-used dates cannot be after the reference date")
        return self


class KA1093TrustDecayEngine(KnowledgeAlgorithm):
    """Calculate time-based trust proposals without updating stored trust."""

    input_schema = KA1093Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1093"

    def _run_logic(self, input_data: KA1093Input) -> dict[str, Any]:
        risk_factor = {"low": 0.75, "medium": 1.0, "high": 1.5, "critical": 2.0}
        proposals = []
        for item in sorted(input_data.records, key=lambda row: row.knowledge_id):
            unused_days = (input_data.reference_date - item.last_used_on).days
            effective_days = unused_days * risk_factor[item.risk_class]
            decayed = item.current_trust * (
                0.5 ** (effective_days / input_data.half_life_days)
            )
            if item.active_evidence_count:
                decayed = max(decayed, input_data.evidence_floor)
            proposals.append(
                {
                    "knowledge_id": item.knowledge_id,
                    "unused_days": unused_days,
                    "current_trust": item.current_trust,
                    "proposed_trust": round(max(0.0, min(decayed, 1.0)), 8),
                    "risk_factor": risk_factor[item.risk_class],
                }
            )
        return {
            "success": True,
            "status": "trust_decay_calculated",
            "proposals": proposals,
            "trust_updates_applied": False,
            "deterministic": True,
            "limitations": (
                "Decay uses declared usage, risk, and evidence counts. It does "
                "not measure factual correctness or apply trust changes."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1093TrustDecayEngine(context).run(context)
