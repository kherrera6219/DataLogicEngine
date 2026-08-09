"""KA-103: bounded service-communication policy proposal."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.knowledge_algorithms.production_utils import stable_identifier
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA103MeshInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_service: str = Field(min_length=1, max_length=200)
    policy_ref: str = Field(min_length=1, max_length=2_000)
    policy_sha256: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    mtls_required: bool = True
    maximum_retry_attempts: int = Field(ge=0, le=10)
    circuit_breaker_required: bool = True
    policy_approved: bool
    rollback_plan_ref: str = Field(min_length=1, max_length=2_000)


class KA103ServiceMesh(KnowledgeAlgorithm):
    """Propose an approved policy without asserting live mesh state."""

    input_schema = KA103MeshInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-103"

    def _run_logic(self, input_data: KA103MeshInput) -> dict[str, Any]:
        blockers = [] if input_data.policy_approved else ["policy_not_approved"]
        proposal_id = stable_identifier(
            "service-policy",
            {
                "target_service": input_data.target_service,
                "policy_ref": input_data.policy_ref,
                "policy_sha256": input_data.policy_sha256.lower(),
            },
        )
        admitted = not blockers
        return {
            "success": True,
            "status": "service_policy_evaluated",
            "decision": "admit" if admitted else "block",
            "blockers": blockers,
            "mesh_active": False,
            "mtls_verified": False,
            "policy_applied": False,
            "effect_proposal": (
                {
                    "effect_id": proposal_id,
                    "kind": "apply_service_communication_policy",
                    "status": "proposed",
                    "service": "operations_control_service",
                    "payload": {
                        "target_service": input_data.target_service,
                        "policy_ref": input_data.policy_ref,
                        "policy_sha256": input_data.policy_sha256.lower(),
                        "mtls_required": input_data.mtls_required,
                        "maximum_retry_attempts": input_data.maximum_retry_attempts,
                        "circuit_breaker_required": input_data.circuit_breaker_required,
                        "rollback_plan_ref": input_data.rollback_plan_ref,
                    },
                }
                if admitted
                else None
            ),
            "authoritative_receipt": None,
            "deterministic": True,
            "limitations": (
                "The KA does not configure a mesh, verify mTLS, inspect traffic, "
                "or change retry and circuit-breaker state."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA103ServiceMesh(context).run(context)
