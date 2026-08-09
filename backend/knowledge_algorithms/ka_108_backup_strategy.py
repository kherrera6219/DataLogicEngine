"""KA-108: coordinated-backup plan and effect proposal."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from backend.knowledge_algorithms.production_utils import (
    load_config,
    stable_identifier,
)
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

SUPPORTED_COMPONENTS = (
    "postgresql",
    "redis",
    "neo4j",
    "chroma",
    "object_store",
    "retained_files",
)


class KA108BackupInput(BaseModel):
    target: Literal["all", "data_plane", "retained_files"] = "all"
    components: list[str] = Field(default_factory=list, max_length=20)


class KA108BackupStrategy(KnowledgeAlgorithm):
    """Plan a managed backup without claiming creation or verification."""

    input_schema = KA108BackupInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-108"
        self.config = load_config(__file__, "ka_108_config.json")

    def _run_logic(self, input_data: KA108BackupInput) -> dict[str, Any]:
        selected = input_data.components or list(SUPPORTED_COMPONENTS)
        invalid = sorted(set(selected) - set(SUPPORTED_COMPONENTS))
        if invalid:
            return {
                "success": False,
                "status": "unsupported_backup_component",
                "unsupported_components": invalid,
                "supported_components": list(SUPPORTED_COMPONENTS),
            }
        selected = [
            component for component in SUPPORTED_COMPONENTS if component in selected
        ]
        proposal_id = stable_identifier(
            "backup",
            {"target": input_data.target, "components": selected},
        )
        proposal = {
            "effect_id": proposal_id,
            "kind": "coordinated_backup",
            "status": "proposed",
            "service": "operations_control_service",
            "payload": {
                "target": input_data.target,
                "components": selected,
                "verification_required": True,
                "encryption_required": True,
            },
        }
        return {
            "success": True,
            "backup_id": None,
            "backup_created": False,
            "targets_covered": selected,
            "encryption_required": True,
            "verification_status": "not_run",
            "storage_tier": "app_owned_object_store",
            "effect_proposal": proposal,
            "authoritative_receipt": None,
            "deterministic": True,
            "limitations": (
                "This produces a coordinated backup proposal only. The owning "
                "operations service must create, encrypt, verify, retain, and receipt "
                "the backup."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA108BackupStrategy(context).run(context)
