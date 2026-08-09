"""KA-102: explicit dependency-binding proposal."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.knowledge_algorithms.production_utils import stable_identifier
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class DependencyBinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service_key: str = Field(min_length=1, max_length=200)
    implementation_ref: str = Field(min_length=1, max_length=2_000)
    contract_ref: str = Field(min_length=1, max_length=2_000)
    implementation_approved: bool


class KA102InjectionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requesting_module: str = Field(min_length=1, max_length=500)
    bindings: list[DependencyBinding] = Field(min_length=1, max_length=1_000)
    rollback_plan_ref: str = Field(min_length=1, max_length=2_000)
    owner_approved: bool

    @model_validator(mode="after")
    def validate_binding_keys(self) -> KA102InjectionInput:
        keys = [item.service_key for item in self.bindings]
        if len(keys) != len(set(keys)):
            raise ValueError("dependency service keys must be unique")
        return self


class KA102DependencyInjection(KnowledgeAlgorithm):
    """Validate explicit bindings without instantiating or injecting services."""

    input_schema = KA102InjectionInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-102"

    def _run_logic(self, input_data: KA102InjectionInput) -> dict[str, Any]:
        blockers = []
        if not input_data.owner_approved:
            blockers.append("owner_approval_required")
        if any(not item.implementation_approved for item in input_data.bindings):
            blockers.append("implementation_not_approved")
        bindings = [
            {
                "service_key": item.service_key,
                "implementation_ref": item.implementation_ref,
                "contract_ref": item.contract_ref,
            }
            for item in sorted(input_data.bindings, key=lambda row: row.service_key)
        ]
        proposal_id = stable_identifier(
            "dependency-bindings",
            {"requesting_module": input_data.requesting_module, "bindings": bindings},
        )
        admitted = not blockers
        return {
            "success": True,
            "status": "dependency_bindings_evaluated",
            "decision": "admit" if admitted else "block",
            "blockers": blockers,
            "bindings": bindings,
            "injected_count": 0,
            "container_changed": False,
            "effect_proposal": (
                {
                    "effect_id": proposal_id,
                    "kind": "apply_dependency_bindings",
                    "status": "proposed",
                    "service": "operations_control_service",
                    "payload": {
                        "requesting_module": input_data.requesting_module,
                        "bindings": bindings,
                        "rollback_plan_ref": input_data.rollback_plan_ref,
                    },
                }
                if admitted
                else None
            ),
            "authoritative_receipt": None,
            "deterministic": True,
            "limitations": "No service is instantiated or injected by this KA.",
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA102DependencyInjection(context).run(context)
