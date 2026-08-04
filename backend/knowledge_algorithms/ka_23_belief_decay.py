"""KA-023: deterministic belief-decay proposal calculation."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

DOMAIN_DECAY_RATES = {
    "finance": 0.02,
    "general": 0.001,
    "healthcare": 0.05,
}
EXCLUDED_CATEGORIES = {"ETERNAL_FACT", "SYSTEM_RULE"}


class BeliefRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    knowledge_id: str = Field(min_length=1, max_length=200)
    current_confidence: float = Field(ge=0, le=1)
    observed_at: datetime
    domain: str = Field(default="general", min_length=1, max_length=100)
    category: str = Field(default="knowledge", min_length=1, max_length=100)


class KA023Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "reference_time": "2026-07-25T00:00:00Z",
                    "knowledge_items": [
                        {
                            "knowledge_id": "knowledge-1",
                            "current_confidence": 0.9,
                            "observed_at": "2026-06-25T00:00:00Z",
                            "domain": "general",
                            "category": "knowledge",
                        }
                    ],
                }
            ]
        },
    )

    reference_time: datetime
    knowledge_items: list[BeliefRecord] = Field(min_length=1, max_length=20_000)
    minimum_confidence: float = Field(default=0.1, ge=0, le=1)

    @model_validator(mode="after")
    def validate_records(self) -> KA023Input:
        identifiers = [item.knowledge_id for item in self.knowledge_items]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("knowledge IDs must be unique")
        if any(item.observed_at > self.reference_time for item in self.knowledge_items):
            raise ValueError("observation times cannot be after the reference time")
        return self


class KA023BeliefDecay(KnowledgeAlgorithm):
    """Calculate bounded confidence-decay proposals without updating memory."""

    input_schema = KA023Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-023"

    def _run_logic(self, input_data: KA023Input) -> dict[str, Any]:
        proposals = []
        total_loss = 0.0
        eligible_count = 0
        for item in sorted(
            input_data.knowledge_items,
            key=lambda row: row.knowledge_id,
        ):
            excluded = item.category.upper() in EXCLUDED_CATEGORIES
            age_days = max(
                0.0,
                (input_data.reference_time - item.observed_at).total_seconds() / 86_400,
            )
            decay_rate = DOMAIN_DECAY_RATES.get(
                item.domain.lower(),
                DOMAIN_DECAY_RATES["general"],
            )
            proposed = item.current_confidence
            reasons = []
            if excluded:
                reasons.append("category_excluded")
            else:
                proposed = max(
                    input_data.minimum_confidence,
                    item.current_confidence * math.exp(-decay_rate * age_days),
                )
                eligible_count += 1
                total_loss += item.current_confidence - proposed
                reasons.append("time_decay_calculated")
            proposals.append(
                {
                    "knowledge_id": item.knowledge_id,
                    "current_confidence": item.current_confidence,
                    "proposed_confidence": round(proposed, 8),
                    "age_days": round(age_days, 8),
                    "decay_rate": decay_rate,
                    "eligible": not excluded,
                    "reasons": reasons,
                    "decay_applied": False,
                }
            )
        plan_sha256 = hashlib.sha256(
            json.dumps(
                proposals,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        return {
            "success": True,
            "status": "belief_decay_proposed",
            "reference_time": input_data.reference_time.isoformat(),
            "proposals": proposals,
            "average_proposed_loss": round(
                total_loss / eligible_count if eligible_count else 0.0,
                8,
            ),
            "plan_sha256": plan_sha256,
            "confidence_updates_applied": False,
            "deterministic": True,
            "limitations": (
                "Decay is a policy proposal derived from supplied timestamps and "
                "fixed domain rates. It does not establish factual correctness or "
                "update stored confidence."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA023BeliefDecay(context).run(context)
