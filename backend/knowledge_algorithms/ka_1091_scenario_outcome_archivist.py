"""KA-1091: deterministic scenario-outcome archive planning."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class ScenarioOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(min_length=1, max_length=200)
    outcome_id: str = Field(min_length=1, max_length=200)
    status: Literal["completed", "failed", "cancelled"]
    significance: float = Field(ge=0, le=1)
    summary: str = Field(min_length=1, max_length=50_000)
    artifact_refs: list[str] = Field(default_factory=list, max_length=1_000)


class KA1091Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "outcomes": [
                        {
                            "scenario_id": "scenario-1",
                            "outcome_id": "outcome-1",
                            "status": "completed",
                            "significance": 0.9,
                            "summary": "Recovery completed.",
                            "artifact_refs": ["artifact-1"],
                        }
                    ]
                }
            ]
        },
    )

    outcomes: list[ScenarioOutcome] = Field(min_length=1, max_length=10_000)
    minimum_significance: float = Field(default=0.7, ge=0, le=1)

    @model_validator(mode="after")
    def validate_ids(self) -> KA1091Input:
        identifiers = [item.outcome_id for item in self.outcomes]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("outcome IDs must be unique")
        return self


class KA1091ScenarioOutcomeArchivist(KnowledgeAlgorithm):
    """Create content-addressed archive proposals without writing artifacts."""

    input_schema = KA1091Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1091"

    def _run_logic(self, input_data: KA1091Input) -> dict[str, Any]:
        plans = []
        for item in sorted(input_data.outcomes, key=lambda row: row.outcome_id):
            if item.significance < input_data.minimum_significance:
                continue
            payload = {
                "scenario_id": item.scenario_id,
                "outcome_id": item.outcome_id,
                "status": item.status,
                "summary": item.summary,
                "artifact_refs": sorted(item.artifact_refs),
            }
            digest = hashlib.sha256(
                json.dumps(payload, sort_keys=True).encode()
            ).hexdigest()
            plans.append(
                {
                    **payload,
                    "content_sha256": digest,
                    "object_key": f"scenario-outcomes/{item.outcome_id}/{digest}.json",
                    "action": "archive_proposal",
                }
            )
        return {
            "success": True,
            "status": "scenario_archive_planned",
            "archive_plans": plans,
            "archive_count": len(plans),
            "artifacts_written": 0,
            "effect_service_required": True,
            "deterministic": True,
            "limitations": (
                "Archive plans are content-addressed proposals. The object-store "
                "service must authorize, write, verify, and receipt each object."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1091ScenarioOutcomeArchivist(context).run(context)
