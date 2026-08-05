"""KA-176: deterministic governance-record validation."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class GovernanceDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_id: str = Field(min_length=1, max_length=200)
    risk_class: Literal["low", "medium", "high", "critical"]
    policy_refs: list[str] = Field(default_factory=list, max_length=1_000)
    evidence_refs: list[str] = Field(default_factory=list, max_length=1_000)
    approval_roles: list[str] = Field(default_factory=list, max_length=1_000)
    owner_recorded: bool


class KA176Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "decisions": [
                        {
                            "decision_id": "d1",
                            "risk_class": "high",
                            "policy_refs": ["policy-1"],
                            "evidence_refs": ["trace-1"],
                            "approval_roles": ["owner", "security"],
                            "owner_recorded": True,
                        }
                    ],
                    "required_approval_roles": {
                        "high": ["owner", "security"],
                        "critical": ["owner", "security"],
                    },
                }
            ]
        },
    )

    decisions: list[GovernanceDecision] = Field(min_length=1, max_length=10_000)
    required_approval_roles: dict[str, list[str]] = Field(default_factory=dict)


class KA176GovernanceValidation(KnowledgeAlgorithm):
    """Validate governance completeness without recording an approval."""

    input_schema = KA176Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-176"

    def _run_logic(self, input_data: KA176Input) -> dict[str, Any]:
        assessments = []
        for item in sorted(input_data.decisions, key=lambda row: row.decision_id):
            missing_roles = sorted(
                set(input_data.required_approval_roles.get(item.risk_class, []))
                - set(item.approval_roles)
            )
            reasons = []
            if not item.policy_refs:
                reasons.append("policy_reference_missing")
            if not item.evidence_refs:
                reasons.append("evidence_missing")
            if not item.owner_recorded:
                reasons.append("owner_missing")
            if missing_roles:
                reasons.append("required_approval_role_missing")
            assessments.append(
                {
                    "decision_id": item.decision_id,
                    "valid": not reasons,
                    "reasons": reasons,
                    "missing_approval_roles": missing_roles,
                }
            )
        return {
            "success": True,
            "status": "governance_validated",
            "assessments": assessments,
            "approvals_recorded": 0,
            "governance_state_updated": False,
            "deterministic": True,
            "limitations": (
                "The KA validates supplied governance records and does not "
                "authenticate approvers or authorize a decision."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA176GovernanceValidation(context).run(context)
