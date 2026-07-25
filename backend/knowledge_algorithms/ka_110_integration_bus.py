"""KA-110: governed integration-event routing proposal."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from backend.knowledge_algorithms.production_utils import (
    load_config,
    stable_identifier,
)
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA110BusInput(BaseModel):
    message: dict[str, Any]
    topic: str = Field(default="system_events", min_length=1, max_length=200)
    entity_id: str = Field(min_length=1, max_length=500)


class KA110IntegrationBus(KnowledgeAlgorithm):
    """Validate a durable outbox proposal without claiming publication."""

    input_schema = KA110BusInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-110"
        self.config = load_config(__file__, "ka_110_config.json")

    def _run_logic(self, input_data: KA110BusInput) -> dict[str, Any]:
        allowed_topics = {
            str(value)
            for value in self.config.get(
                "topics",
                ["knowledge_updates", "system_events", "audit_logs"],
            )
        }
        if input_data.topic not in allowed_topics:
            return {
                "success": False,
                "status": "integration_topic_not_allowed",
                "allowed_topics": sorted(allowed_topics),
            }
        serialized = json.dumps(
            input_data.message,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        max_bytes = int(self.config.get("max_message_size_bytes", 524_288))
        if len(serialized) > max_bytes:
            return {
                "success": False,
                "status": "integration_message_too_large",
                "payload_size_bytes": len(serialized),
                "max_message_size_bytes": max_bytes,
            }
        message_id = stable_identifier(
            "message",
            {
                "topic": input_data.topic,
                "entity_id": input_data.entity_id,
                "message": input_data.message,
            },
        )
        proposal = {
            "effect_id": message_id,
            "kind": "enqueue_cross_store_outbox_event",
            "status": "proposed",
            "service": "cross_store_outbox",
            "payload": {
                "topic": input_data.topic,
                "entity_id": input_data.entity_id,
                "message": input_data.message,
            },
        }
        return {
            "success": True,
            "message_id": message_id,
            "published": False,
            "published_to": None,
            "bus_type": "postgresql_outbox_with_redis_materialization",
            "delivery_guarantee": "durable_after_authoritative_receipt",
            "acknowledge_receipt": False,
            "routing_status": "proposed",
            "payload_size_bytes": len(serialized),
            "effect_proposal": proposal,
            "authoritative_receipt": None,
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA110IntegrationBus(context).run(context)
