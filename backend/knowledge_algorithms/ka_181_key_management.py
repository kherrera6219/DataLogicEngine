"""KA-181: deterministic cryptographic-key lifecycle governance."""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KeyRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key_ref: str = Field(min_length=1, max_length=2_000)
    status: Literal["active", "disabled", "compromised", "retired"]
    created_on: date
    rotate_by: date
    protected_storage_verified: bool
    usage_count: int = Field(ge=0, le=1_000_000_000)


class KA181Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "evaluation_date": "2026-07-25",
                    "keys": [
                        {
                            "key_ref": "key-1",
                            "status": "active",
                            "created_on": "2026-01-01",
                            "rotate_by": "2026-07-01",
                            "protected_storage_verified": True,
                            "usage_count": 100,
                        }
                    ],
                }
            ]
        },
    )

    evaluation_date: date
    keys: list[KeyRecord] = Field(min_length=1, max_length=100_000)


class KA181KeyManagement(KnowledgeAlgorithm):
    """Propose key lifecycle actions without exposing or changing keys."""

    input_schema = KA181Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-181"

    def _run_logic(self, input_data: KA181Input) -> dict[str, Any]:
        actions = []
        for item in sorted(input_data.keys, key=lambda row: row.key_ref):
            reasons = []
            action = "retain"
            if item.status == "compromised":
                action, reasons = "revoke_and_rotate", ["key_compromised"]
            elif not item.protected_storage_verified:
                action, reasons = "disable_and_reprotect", ["storage_not_verified"]
            elif item.status == "active" and item.rotate_by <= input_data.evaluation_date:
                action, reasons = "rotate", ["rotation_due"]
            actions.append(
                {"key_ref": item.key_ref, "proposed_action": action, "reasons": reasons}
            )
        return {
            "success": True,
            "status": "key_lifecycle_evaluated",
            "actions": actions,
            "key_material_returned": False,
            "actions_applied": 0,
            "deterministic": True,
            "limitations": (
                "The KA evaluates key metadata only; an OS-backed key service "
                "must generate, protect, rotate, revoke, and attest keys."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA181KeyManagement(context).run(context)
