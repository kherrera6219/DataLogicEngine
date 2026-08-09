"""KA-101: bounded environment-configuration proposal."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.knowledge_algorithms.production_utils import stable_identifier
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA101EnvInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_environment: Literal["development", "test", "staging", "production"]
    configuration_ref: str = Field(min_length=1, max_length=2_000)
    configuration_sha256: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    setting_names: list[str] = Field(min_length=1, max_length=1_000)
    rollback_plan_ref: str = Field(min_length=1, max_length=2_000)
    owner_approved: bool


class KA101EnvironmentManagement(KnowledgeAlgorithm):
    """Propose an allowlisted configuration activation without reading secrets."""

    input_schema = KA101EnvInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-101"

    def _run_logic(self, input_data: KA101EnvInput) -> dict[str, Any]:
        setting_names = sorted(set(input_data.setting_names))
        blockers = [] if input_data.owner_approved else ["owner_approval_required"]
        proposal_id = stable_identifier(
            "environment-configuration",
            {
                "environment": input_data.target_environment,
                "configuration_ref": input_data.configuration_ref,
                "configuration_sha256": input_data.configuration_sha256.lower(),
                "setting_names": setting_names,
            },
        )
        admitted = not blockers
        return {
            "success": True,
            "status": "environment_configuration_evaluated",
            "decision": "admit" if admitted else "block",
            "blockers": blockers,
            "setting_names": setting_names,
            "configuration_values_returned": False,
            "environment_variables_read": False,
            "configuration_applied": False,
            "effect_proposal": (
                {
                    "effect_id": proposal_id,
                    "kind": "activate_environment_configuration",
                    "status": "proposed",
                    "service": "operations_control_service",
                    "payload": {
                        "target_environment": input_data.target_environment,
                        "configuration_ref": input_data.configuration_ref,
                        "configuration_sha256": input_data.configuration_sha256.lower(),
                        "setting_names": setting_names,
                        "rollback_plan_ref": input_data.rollback_plan_ref,
                    },
                }
                if admitted
                else None
            ),
            "authoritative_receipt": None,
            "deterministic": True,
            "limitations": (
                "The KA returns names and hashes only; it never reads process "
                "environment values or activates configuration."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA101EnvironmentManagement(context).run(context)
