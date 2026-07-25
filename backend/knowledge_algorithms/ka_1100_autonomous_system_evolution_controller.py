"""KA-1100: bounded system-evolution change admission."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class EvolutionProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str = Field(min_length=1, max_length=200)
    change_class: Literal["configuration", "algorithm", "schema", "security"]
    validation_passed: bool
    rollback_plan_ref: str | None = Field(default=None, max_length=2_000)
    affected_capability_count: int = Field(ge=0, le=213)
    expected_improvement: float = Field(ge=0, le=1)
    risk_score: float = Field(ge=0, le=1)
    human_approved: bool = False


class KA1100Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "proposals": [
                        {
                            "proposal_id": "proposal-1",
                            "change_class": "configuration",
                            "validation_passed": True,
                            "rollback_plan_ref": "rollback-1",
                            "affected_capability_count": 1,
                            "expected_improvement": 0.2,
                            "risk_score": 0.1,
                        }
                    ]
                }
            ]
        },
    )

    proposals: list[EvolutionProposal] = Field(min_length=1, max_length=1_000)
    maximum_risk_score: float = Field(default=0.25, ge=0, le=1)
    maximum_affected_capabilities: int = Field(default=10, ge=1, le=213)

    @model_validator(mode="after")
    def validate_ids(self) -> KA1100Input:
        identifiers = [item.proposal_id for item in self.proposals]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("evolution proposal IDs must be unique")
        return self


class KA1100AutonomousSystemEvolutionController(KnowledgeAlgorithm):
    """Admit only bounded proposals; never modify code or configuration."""

    input_schema = KA1100Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1100"

    def _run_logic(self, input_data: KA1100Input) -> dict[str, Any]:
        decisions = []
        for item in sorted(input_data.proposals, key=lambda row: row.proposal_id):
            blockers = []
            if not item.validation_passed:
                blockers.append("validation_not_passed")
            if not item.rollback_plan_ref:
                blockers.append("rollback_plan_missing")
            if item.risk_score > input_data.maximum_risk_score:
                blockers.append("risk_above_limit")
            if item.affected_capability_count > input_data.maximum_affected_capabilities:
                blockers.append("scope_above_limit")
            if item.change_class in {"algorithm", "schema", "security"} and not item.human_approved:
                blockers.append("human_approval_required")
            decisions.append(
                {
                    "proposal_id": item.proposal_id,
                    "decision": "admit_to_canary" if not blockers else "block",
                    "blockers": blockers,
                }
            )
        return {
            "success": True,
            "status": "system_evolution_evaluated",
            "decisions": decisions,
            "changes_applied": 0,
            "autonomous_code_change": False,
            "deterministic": True,
            "limitations": (
                "Admission permits only a separately authorized canary workflow; "
                "this capability never edits, deploys, or promotes a change."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1100AutonomousSystemEvolutionController(context).run(context)
