"""KA-097: canonical audit-record construction and persistence proposal."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel, Field

from backend.knowledge_algorithms.production_utils import (
    load_config,
    stable_identifier,
)
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA097AuditInput(BaseModel):
    event_data: dict[str, Any]
    actor_id: str = Field(default="system", min_length=1, max_length=200)
    occurred_at: str | None = Field(default=None, max_length=100)
    previous_hash: str | None = Field(default=None, max_length=128)


class KA097Auditing(KnowledgeAlgorithm):
    """Construct hash-chain input without claiming persistence or signing."""

    input_schema = KA097AuditInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-097"
        self.config = load_config(__file__, "ka_97_config.json")

    def _run_logic(self, input_data: KA097AuditInput) -> dict[str, Any]:
        record = {
            "event": input_data.event_data,
            "actor_id": input_data.actor_id,
            "occurred_at": input_data.occurred_at,
            "previous_hash": input_data.previous_hash,
            "generator": self.ka_id,
        }
        canonical = json.dumps(
            record,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        content_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        audit_id = stable_identifier("audit", record)
        effect_proposal = {
            "effect_id": audit_id,
            "kind": "append_audit_record",
            "status": "proposed",
            "service": "app_audit_service",
            "payload": {
                "record": record,
                "content_sha256": content_hash,
            },
        }
        return {
            "success": True,
            "audit_id": audit_id,
            "content_sha256": content_hash,
            "signed": False,
            "persisted": False,
            "immutable": False,
            "blockchain_anchored": False,
            "backend_target": self.config.get(
                "audit_backend",
                "postgresql_immutable",
            ),
            "prov_metadata": {
                "prov:wasGeneratedBy": f"activity:DataLogicEngine:{self.ka_id}",
                "prov:used": (
                    f"entity:{input_data.event_data.get('type', 'generic')}"
                ),
                "prov:agent": f"agent:{input_data.actor_id}",
            },
            "effect_proposal": effect_proposal,
            "authoritative_receipt": None,
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA097Auditing(context).run(context)
