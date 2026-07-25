"""KA-184: deterministic incident-response plan construction."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class IncidentRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    incident_id: str = Field(min_length=1, max_length=200)
    severity: Literal["low", "medium", "high", "critical"]
    incident_type: Literal[
        "account_compromise",
        "malware",
        "data_exposure",
        "service_disruption",
        "policy_violation",
    ]
    affected_asset_refs: list[str] = Field(min_length=1, max_length=10_000)
    owner_assigned: bool
    containment_ready: bool
    evidence_preservation_ready: bool


class KA184Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "incidents": [
                        {
                            "incident_id": "inc-1",
                            "severity": "critical",
                            "incident_type": "data_exposure",
                            "affected_asset_refs": ["store-1"],
                            "owner_assigned": True,
                            "containment_ready": True,
                            "evidence_preservation_ready": True,
                        }
                    ]
                }
            ]
        },
    )

    incidents: list[IncidentRecord] = Field(min_length=1, max_length=10_000)


class KA184IncidentResponse(KnowledgeAlgorithm):
    """Construct response steps while leaving operational actions unapplied."""

    input_schema = KA184Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-184"

    def _run_logic(self, input_data: KA184Input) -> dict[str, Any]:
        plans = []
        for item in sorted(input_data.incidents, key=lambda row: row.incident_id):
            blockers = []
            if not item.owner_assigned:
                blockers.append("incident_owner_missing")
            if not item.containment_ready:
                blockers.append("containment_not_ready")
            if not item.evidence_preservation_ready:
                blockers.append("evidence_preservation_not_ready")
            steps = [
                "preserve_evidence",
                "contain_affected_assets",
                "eradicate_verified_cause",
                "recover_and_validate",
                "post_incident_review",
            ]
            if item.severity in {"high", "critical"}:
                steps.insert(2, "notify_required_stakeholders")
            plans.append(
                {
                    "incident_id": item.incident_id,
                    "decision": "activate_plan" if not blockers else "block",
                    "blockers": blockers,
                    "ordered_steps": steps,
                }
            )
        return {
            "success": True,
            "status": "incident_response_planned",
            "plans": plans,
            "actions_applied": 0,
            "deterministic": True,
            "limitations": (
                "The KA creates a generic response plan; authorized incident "
                "services and humans must execute, verify, and document each step."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA184IncidentResponse(context).run(context)
