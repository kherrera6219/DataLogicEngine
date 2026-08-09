"""KA-093: bounded notification-routing proposal."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.knowledge_algorithms.production_utils import load_config, stable_identifier
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA093NotificationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=100_000)
    severity: Literal["info", "warning", "critical"] = "info"
    allowed_channels: list[Literal["email", "slack", "webhook", "sms"]] = Field(
        default_factory=lambda: ["email", "webhook"], max_length=4
    )
    recipient_refs: list[str] = Field(min_length=1, max_length=1_000)


class KA093Notification(KnowledgeAlgorithm):
    """Select permitted notification routes without claiming delivery."""

    input_schema = KA093NotificationInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-093"
        self.config = load_config(__file__, "ka_93_config.json")

    def _run_logic(self, input_data: KA093NotificationInput) -> dict[str, Any]:
        configured = self.config.get("priority_rules", {}).get(
            input_data.severity, ["email"]
        )
        allowed = set(input_data.allowed_channels)
        channels = sorted(
            {str(channel) for channel in configured if channel in allowed}
        )
        proposal_id = stable_identifier(
            "notification",
            {
                "message": input_data.message,
                "severity": input_data.severity,
                "channels": channels,
                "recipient_refs": sorted(set(input_data.recipient_refs)),
            },
        )
        return {
            "success": True,
            "proposal_id": proposal_id,
            "severity_level": input_data.severity,
            "proposed_channels": channels,
            "recipient_refs": sorted(set(input_data.recipient_refs)),
            "routing_report": [
                {"channel": channel, "status": "proposed"} for channel in channels
            ],
            "dispatched_to": [],
            "delivered": False,
            "effect_proposal": (
                {
                    "effect_id": proposal_id,
                    "kind": "enqueue_notification",
                    "status": "proposed",
                    "service": "operations_control_service",
                    "payload": {
                        "message": input_data.message,
                        "severity": input_data.severity,
                        "channels": channels,
                        "recipient_refs": sorted(set(input_data.recipient_refs)),
                    },
                }
                if channels
                else None
            ),
            "authoritative_receipt": None,
            "deterministic": True,
            "limitations": (
                "The KA selects caller-permitted routes. OperationsControlService "
                "must durably enqueue and receipt any delivery."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA093Notification(context).run(context)
