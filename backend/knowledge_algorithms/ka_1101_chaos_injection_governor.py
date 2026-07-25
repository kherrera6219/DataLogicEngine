"""KA-1101: deterministic chaos-injection policy admission."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class ChaosProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_id: str = Field(min_length=1, max_length=200)
    environment: Literal["development", "test", "staging", "production"]
    fault_type: Literal["latency", "service_stop", "packet_loss", "disk_pressure"]
    target_service: str = Field(min_length=1, max_length=200)
    magnitude: float = Field(gt=0, le=1)
    duration_seconds: int = Field(gt=0, le=86_400)
    rollback_verified: bool
    monitoring_ready: bool
    human_approved: bool = False


class KA1101Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "proposals": [
                        {
                            "proposal_id": "chaos-1",
                            "environment": "test",
                            "fault_type": "latency",
                            "target_service": "redis",
                            "magnitude": 0.1,
                            "duration_seconds": 30,
                            "rollback_verified": True,
                            "monitoring_ready": True,
                        }
                    ],
                    "allowed_services": ["redis"],
                }
            ]
        },
    )

    proposals: list[ChaosProposal] = Field(min_length=1, max_length=1_000)
    allowed_services: list[str] = Field(min_length=1, max_length=100)
    maximum_magnitude: float = Field(default=0.25, gt=0, le=1)
    maximum_duration_seconds: int = Field(default=300, gt=0, le=86_400)

    @model_validator(mode="after")
    def validate_ids(self) -> KA1101Input:
        identifiers = [item.proposal_id for item in self.proposals]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("chaos proposal IDs must be unique")
        return self


class KA1101ChaosInjectionGovernor(KnowledgeAlgorithm):
    """Enforce chaos scope and safety preconditions without injecting faults."""

    input_schema = KA1101Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1101"

    def _run_logic(self, input_data: KA1101Input) -> dict[str, Any]:
        allowed = set(input_data.allowed_services)
        decisions = []
        for item in sorted(input_data.proposals, key=lambda row: row.proposal_id):
            blockers = []
            if item.target_service not in allowed:
                blockers.append("service_not_allowed")
            if item.magnitude > input_data.maximum_magnitude:
                blockers.append("magnitude_above_limit")
            if item.duration_seconds > input_data.maximum_duration_seconds:
                blockers.append("duration_above_limit")
            if not item.rollback_verified:
                blockers.append("rollback_not_verified")
            if not item.monitoring_ready:
                blockers.append("monitoring_not_ready")
            if item.environment == "production" and not item.human_approved:
                blockers.append("production_human_approval_required")
            decisions.append(
                {
                    "proposal_id": item.proposal_id,
                    "decision": "approve_plan" if not blockers else "block",
                    "blockers": blockers,
                }
            )
        return {
            "success": True,
            "status": "chaos_injection_governed",
            "decisions": decisions,
            "faults_injected": 0,
            "effect_service_required": True,
            "deterministic": True,
            "limitations": (
                "Approval is a policy decision only. A separately authorized "
                "chaos service must enforce environment controls and rollback."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1101ChaosInjectionGovernor(context).run(context)
