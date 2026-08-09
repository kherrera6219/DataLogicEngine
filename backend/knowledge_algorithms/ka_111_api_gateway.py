"""KA-111: authenticated gateway-routing admission."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.knowledge_algorithms.production_utils import stable_identifier
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA111Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1, max_length=2_000)
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] = "GET"
    principal_id: str = Field(min_length=1, max_length=200)
    authentication_verified: bool
    policy_approved: bool
    rate_limit_allowed: bool
    rate_limit_remaining: int = Field(ge=0)
    route_target: str = Field(min_length=1, max_length=200)


class KA111APIGateway(KnowledgeAlgorithm):
    """Consume authoritative gateway controls and propose one route."""

    input_schema = KA111Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-111"

    def _run_logic(self, input_data: KA111Input) -> dict[str, Any]:
        blockers = []
        if not input_data.authentication_verified:
            blockers.append("authentication_not_verified")
        if not input_data.policy_approved:
            blockers.append("policy_not_approved")
        if not input_data.rate_limit_allowed:
            blockers.append("rate_limit_exceeded")
        route_id = stable_identifier(
            "gateway-route",
            {
                "path": input_data.path,
                "method": input_data.method,
                "principal_id": input_data.principal_id,
                "route_target": input_data.route_target,
            },
        )
        admitted = not blockers
        return {
            "success": True,
            "status": "gateway_route_admitted" if admitted else "gateway_route_blocked",
            "decision": "admit" if admitted else "block",
            "blockers": blockers,
            "route_id": route_id,
            "principal_id": input_data.principal_id,
            "route_target": input_data.route_target if admitted else None,
            "method": input_data.method,
            "rate_limit_remaining": input_data.rate_limit_remaining,
            "forwarded": False,
            "provider_called": False,
            "effect_proposal": (
                {
                    "effect_id": route_id,
                    "kind": "forward_authenticated_gateway_request",
                    "status": "proposed",
                    "service": "provider_gateway_service",
                    "payload": {
                        "path": input_data.path,
                        "method": input_data.method,
                        "principal_id": input_data.principal_id,
                        "route_target": input_data.route_target,
                    },
                }
                if admitted
                else None
            ),
            "authoritative_receipt": None,
            "deterministic": True,
            "limitations": (
                "Authentication, policy, and rate-limit decisions are supplied by "
                "the gateway authority; this KA neither validates credentials nor forwards."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA111APIGateway(context).run(context)
