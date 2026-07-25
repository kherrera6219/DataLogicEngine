"""KA-172: deterministic task safety check."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class SafetyCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_id: str = Field(min_length=1, max_length=200)
    risk_level: Literal["low", "medium", "high", "critical"]
    hazard_ids: list[str] = Field(default_factory=list, max_length=1_000)
    required_safeguard_ids: list[str] = Field(default_factory=list, max_length=1_000)
    verified_safeguard_ids: list[str] = Field(default_factory=list, max_length=1_000)
    human_reviewed: bool = False


class KA172Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "candidates": [
                        {
                            "candidate_id": "candidate-1",
                            "risk_level": "high",
                            "hazard_ids": ["hazard-1"],
                            "required_safeguard_ids": ["guard-1"],
                            "verified_safeguard_ids": ["guard-1"],
                            "human_reviewed": True,
                        }
                    ]
                }
            ]
        },
    )

    candidates: list[SafetyCandidate] = Field(min_length=1, max_length=10_000)


class KA172SafetyCheck(KnowledgeAlgorithm):
    """Admit only candidates with verified safeguards and required review."""

    input_schema = KA172Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-172"

    def _run_logic(self, input_data: KA172Input) -> dict[str, Any]:
        decisions = []
        for item in sorted(input_data.candidates, key=lambda row: row.candidate_id):
            blockers = []
            missing = sorted(
                set(item.required_safeguard_ids) - set(item.verified_safeguard_ids)
            )
            if item.hazard_ids and not item.required_safeguard_ids:
                blockers.append("hazards_without_required_safeguards")
            if missing:
                blockers.append("required_safeguard_not_verified")
            if item.risk_level in {"high", "critical"} and not item.human_reviewed:
                blockers.append("human_review_required")
            decisions.append(
                {
                    "candidate_id": item.candidate_id,
                    "decision": "allow" if not blockers else "block",
                    "blockers": blockers,
                    "missing_safeguard_ids": missing,
                }
            )
        return {
            "success": True,
            "status": "safety_checked",
            "decisions": decisions,
            "actions_applied": 0,
            "deterministic": True,
            "limitations": (
                "The check validates declared hazards and safeguards; it does not "
                "discover physical, clinical, or domain-specific hazards."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA172SafetyCheck(context).run(context)
