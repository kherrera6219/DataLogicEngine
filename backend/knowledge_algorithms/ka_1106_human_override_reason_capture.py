"""KA-1106: structured human-override reason capture."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class HumanOverride(BaseModel):
    model_config = ConfigDict(extra="forbid")

    override_id: str = Field(min_length=1, max_length=200)
    decision_ref: str = Field(min_length=1, max_length=2_000)
    original_outcome: str = Field(min_length=1, max_length=2_000)
    corrected_outcome: str = Field(min_length=1, max_length=2_000)
    reason_code: Literal[
        "incorrect_evidence",
        "policy_exception",
        "safety_intervention",
        "context_missing",
        "operator_judgment",
    ]
    rationale: str = Field(min_length=10, max_length=10_000)
    reviewer_role: str = Field(min_length=1, max_length=200)
    evidence_refs: list[str] = Field(default_factory=list, max_length=1_000)


class KA1106Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "overrides": [
                        {
                            "override_id": "override-1",
                            "decision_ref": "decision-1",
                            "original_outcome": "deny",
                            "corrected_outcome": "review",
                            "reason_code": "context_missing",
                            "rationale": "Required owner context was unavailable.",
                            "reviewer_role": "owner",
                            "evidence_refs": ["trace-1"],
                        }
                    ]
                }
            ]
        },
    )

    overrides: list[HumanOverride] = Field(min_length=1, max_length=10_000)

    @model_validator(mode="after")
    def validate_ids(self) -> KA1106Input:
        identifiers = [item.override_id for item in self.overrides]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("override IDs must be unique")
        return self


class KA1106HumanOverrideReasonCapture(KnowledgeAlgorithm):
    """Normalize human corrections into stable, unapplied training signals."""

    input_schema = KA1106Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1106"

    def _run_logic(self, input_data: KA1106Input) -> dict[str, Any]:
        records = []
        for item in sorted(input_data.overrides, key=lambda row: row.override_id):
            signal = {
                "override_id": item.override_id,
                "decision_ref": item.decision_ref,
                "original_outcome": item.original_outcome,
                "corrected_outcome": item.corrected_outcome,
                "reason_code": item.reason_code,
                "rationale": item.rationale,
                "reviewer_role": item.reviewer_role,
                "evidence_refs": sorted(set(item.evidence_refs)),
            }
            digest = hashlib.sha256(
                json.dumps(signal, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            records.append({**signal, "training_signal_sha256": digest})
        return {
            "success": True,
            "status": "human_override_reasons_structured",
            "records": records,
            "records_persisted": 0,
            "training_updates_applied": 0,
            "deterministic": True,
            "limitations": (
                "The capability structures supplied human rationale; it does not "
                "authenticate the reviewer or apply a model or policy update."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1106HumanOverrideReasonCapture(context).run(context)
