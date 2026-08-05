"""KA-1108: deterministic capability-escalation detection."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class CapabilityInteraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    interaction_id: str = Field(min_length=1, max_length=200)
    source_capability_id: str = Field(min_length=1, max_length=200)
    target_capability_id: str = Field(min_length=1, max_length=200)
    observed_invocations: int = Field(ge=0, le=1_000_000_000)
    authorized_invocations: int = Field(ge=0, le=1_000_000_000)
    emergence_flag: bool = False
    crossed_privilege_boundary: bool = False


class KA1108Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "interactions": [
                        {
                            "interaction_id": "interaction-1",
                            "source_capability_id": "KA-001",
                            "target_capability_id": "KA-002",
                            "observed_invocations": 5,
                            "authorized_invocations": 2,
                            "crossed_privilege_boundary": True,
                        }
                    ]
                }
            ]
        },
    )

    interactions: list[CapabilityInteraction] = Field(
        min_length=1, max_length=100_000
    )
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_dependencies(self) -> KA1108Input:
        if self.dependency_results and set(self.dependency_results) != {"KA-1112"}:
            raise ValueError("dependency_results must contain KA-1112")
        return self


class KA1108CapabilityEscalationDetector(KnowledgeAlgorithm):
    """Detect overuse and privilege-crossing patterns without containment."""

    input_schema = KA1108Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1108"

    def _run_logic(self, input_data: KA1108Input) -> dict[str, Any]:
        introspection_passed = input_data.dependency_results.get(
            "KA-1112", {}
        ).get("audit_passed", True) is True
        alerts = []
        for item in sorted(
            input_data.interactions, key=lambda row: row.interaction_id
        ):
            reasons = []
            if item.observed_invocations > item.authorized_invocations:
                reasons.append("authorized_invocation_limit_exceeded")
            if item.emergence_flag:
                reasons.append("emergence_flag")
            if item.crossed_privilege_boundary:
                reasons.append("privilege_boundary_crossed")
            if reasons:
                severity = "critical" if item.crossed_privilege_boundary else "high"
                alerts.append(
                    {
                        "interaction_id": item.interaction_id,
                        "severity": severity,
                        "reasons": reasons,
                        "proposed_action": "contain_and_review",
                    }
                )
        if not introspection_passed:
            alerts.append(
                {
                    "interaction_id": "system-self-introspection",
                    "severity": "critical",
                    "reasons": ["self_introspection_audit_failed"],
                    "proposed_action": "contain_and_review",
                }
            )
        return {
            "success": True,
            "status": "capability_escalation_assessed",
            "escalation_detected": bool(alerts),
            "alerts": alerts,
            "containment_actions_applied": 0,
            "dependencies_consumed": sorted(input_data.dependency_results),
            "deterministic": True,
            "limitations": (
                "The detector evaluates supplied interaction counters and flags; "
                "an authoritative policy service must enforce containment."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1108CapabilityEscalationDetector(context).run(context)
