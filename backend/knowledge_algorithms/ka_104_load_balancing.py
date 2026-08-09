"""KA-104: deterministic load-routing recommendation."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class ActiveNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(min_length=1, max_length=200)
    active_connections: int = Field(ge=0, le=1_000_000_000)
    capacity: int = Field(gt=0, le=1_000_000_000)
    healthy: bool


class KA104LBInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    batch_size: int = Field(ge=1, le=1_000_000_000)
    algorithm: Literal["least_connections", "capacity_ratio"]
    active_nodes: list[ActiveNode] = Field(min_length=1, max_length=10_000)

    @model_validator(mode="after")
    def validate_nodes(self) -> KA104LBInput:
        identifiers = [item.node_id for item in self.active_nodes]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("node IDs must be unique")
        return self


class KA104LoadBalancing(KnowledgeAlgorithm):
    """Choose one healthy node from supplied measurements without routing work."""

    input_schema = KA104LBInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-104"

    def _run_logic(self, input_data: KA104LBInput) -> dict[str, Any]:
        eligible = [item for item in input_data.active_nodes if item.healthy]
        if not eligible:
            return {
                "success": True,
                "status": "load_route_blocked",
                "decision": "block",
                "blockers": ["no_healthy_nodes"],
                "target_node_id": None,
                "routing_applied": False,
                "deterministic": True,
            }
        if input_data.algorithm == "least_connections":
            selected = min(
                eligible, key=lambda row: (row.active_connections, row.node_id)
            )
        else:
            selected = min(
                eligible,
                key=lambda row: (
                    row.active_connections / row.capacity,
                    row.node_id,
                ),
            )
        return {
            "success": True,
            "status": "load_route_recommended",
            "decision": "recommend",
            "blockers": [],
            "target_node_id": selected.node_id,
            "batch_size": input_data.batch_size,
            "algorithm": input_data.algorithm,
            "eligible_node_count": len(eligible),
            "routing_applied": False,
            "measurement_status": "caller_supplied",
            "deterministic": True,
            "limitations": "The owner routes work; this KA only recommends a node.",
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA104LoadBalancing(context).run(context)
