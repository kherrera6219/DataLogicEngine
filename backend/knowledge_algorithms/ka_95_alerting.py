"""KA-095: deterministic alert decision and effect proposal."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from backend.knowledge_algorithms.production_utils import (
    load_config,
    stable_identifier,
)
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA095AlertInput(BaseModel):
    event: str = Field(min_length=1, max_length=2_000)
    level: Literal["info", "warning", "error", "critical"] = "error"
    source: str = Field(default="datalogicengine", min_length=1, max_length=200)
    recent_deduplication_keys: list[str] = Field(
        default_factory=list,
        max_length=10_000,
    )


class KA095Alerting(KnowledgeAlgorithm):
    """Decide whether an alert should be sent without claiming delivery."""

    input_schema = KA095AlertInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-095"
        self.config = load_config(__file__, "ka_95_config.json")

    def _run_logic(self, input_data: KA095AlertInput) -> dict[str, Any]:
        deduplication_key = stable_identifier(
            "alert",
            {
                "source": input_data.source,
                "event": input_data.event,
                "level": input_data.level,
            },
        )
        deduplicated = deduplication_key in set(
            input_data.recent_deduplication_keys
        )
        should_alert = input_data.level != "info" and not deduplicated
        policy = self.config.get("escalation_policy", "ops_on_call")
        proposal = (
            {
                "effect_id": deduplication_key,
                "kind": "operator_alert",
                "status": "proposed",
                "service": "app_observability_alert_service",
                "payload": {
                    "event": input_data.event,
                    "level": input_data.level,
                    "source": input_data.source,
                    "escalation_policy": policy,
                },
            }
            if should_alert
            else None
        )
        return {
            "success": True,
            "alert_triggered": False,
            "alert_recommended": should_alert,
            "active_alert_id": None,
            "deduplication_key": deduplication_key,
            "escalation_policy": policy,
            "deduplicated": deduplicated,
            "effect_proposal": proposal,
            "delivery_receipt": None,
            "limitations": (
                "An alert is not delivered until the canonical orchestrator "
                "applies this proposal through the alert service."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA095Alerting(context).run(context)
