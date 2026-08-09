"""KA-107: bounded disaster-recovery admission proposal."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.knowledge_algorithms.production_utils import stable_identifier
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA107RecoveryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    failure_id: str = Field(min_length=1, max_length=200)
    failure_confirmed: bool
    recovery_plan_ref: str = Field(min_length=1, max_length=2_000)
    target_environment: Literal["local_recovery", "secondary_node"]
    latest_backup_verified: bool
    owner_approved: bool


class KA107DisasterRecovery(KnowledgeAlgorithm):
    """Admit an explicit recovery plan without initiating failover."""

    input_schema = KA107RecoveryInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-107"

    def _run_logic(self, input_data: KA107RecoveryInput) -> dict[str, Any]:
        blockers = []
        if not input_data.failure_confirmed:
            blockers.append("failure_not_confirmed")
        if not input_data.latest_backup_verified:
            blockers.append("backup_not_verified")
        if not input_data.owner_approved:
            blockers.append("owner_approval_required")
        proposal_id = stable_identifier(
            "disaster-recovery",
            {
                "failure_id": input_data.failure_id,
                "recovery_plan_ref": input_data.recovery_plan_ref,
                "target_environment": input_data.target_environment,
            },
        )
        admitted = not blockers
        return {
            "success": True,
            "status": "recovery_plan_evaluated",
            "decision": "admit" if admitted else "block",
            "blockers": blockers,
            "failure_id": input_data.failure_id,
            "recovery_started": False,
            "failover_applied": False,
            "rpo_attained": None,
            "rto_attained": None,
            "data_sync_verified": False,
            "effect_proposal": (
                {
                    "effect_id": proposal_id,
                    "kind": "execute_disaster_recovery",
                    "status": "proposed",
                    "service": "operations_control_service",
                    "payload": {
                        "failure_id": input_data.failure_id,
                        "recovery_plan_ref": input_data.recovery_plan_ref,
                        "target_environment": input_data.target_environment,
                    },
                }
                if admitted
                else None
            ),
            "authoritative_receipt": None,
            "deterministic": True,
            "limitations": (
                "OperationsControlService must execute and verify recovery; this KA "
                "does not measure RPO/RTO, synchronize data, or initiate failover."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA107DisasterRecovery(context).run(context)
