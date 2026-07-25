"""KA-112: durable background-job enqueue proposal."""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, Field

from backend.knowledge_algorithms.production_utils import (
    load_config,
    stable_identifier,
)
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA112Input(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)
    queue: Literal["high_priority", "background_tasks"] = "background_tasks"
    job_type: str = Field(min_length=1, max_length=200)
    entity_id: str = Field(min_length=1, max_length=500)


class KA112MessageBroker(KnowledgeAlgorithm):
    """Validate a durable job proposal without using a private broker."""

    input_schema = KA112Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-112"
        self.config = load_config(__file__, "ka_112_config.json")

    def _run_logic(self, input_data: KA112Input) -> dict[str, Any]:
        serialized = json.dumps(
            input_data.payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        max_bytes = int(self.config.get("max_message_size_bytes", 524_288))
        if len(serialized) > max_bytes:
            return {
                "success": False,
                "status": "job_payload_too_large",
                "payload_size_bytes": len(serialized),
                "max_message_size_bytes": max_bytes,
            }
        message_tag = stable_identifier(
            "job",
            {
                "queue": input_data.queue,
                "job_type": input_data.job_type,
                "entity_id": input_data.entity_id,
                "payload": input_data.payload,
            },
        )
        proposal = {
            "effect_id": message_tag,
            "kind": "enqueue_durable_job",
            "status": "proposed",
            "service": "postgresql_redis_job_coordinator",
            "payload": {
                "queue": input_data.queue,
                "job_type": input_data.job_type,
                "entity_id": input_data.entity_id,
                "payload": input_data.payload,
            },
        }
        return {
            "success": True,
            "message_tag": message_tag,
            "queue_active": None,
            "queued": False,
            "broker_type": "postgresql_authority_with_redis_notification",
            "ack_mode": "authoritative_receipt_required",
            "effect_proposal": proposal,
            "authoritative_receipt": None,
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA112MessageBroker(context).run(context)
