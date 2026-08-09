"""KA-109: supplied-evidence system-health aggregation."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class ComponentHealth(BaseModel):
    model_config = ConfigDict(extra="forbid")

    component_id: str = Field(min_length=1, max_length=200)
    status: Literal["healthy", "degraded", "unavailable", "unknown"]
    required: bool = True
    liveness_passed: bool
    readiness_passed: bool
    evidence_ref: str = Field(min_length=1, max_length=2_000)


class KA109HealthInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    components: list[ComponentHealth] = Field(min_length=1, max_length=10_000)

    @model_validator(mode="after")
    def validate_ids(self) -> KA109HealthInput:
        identifiers = [item.component_id for item in self.components]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("component IDs must be unique")
        return self


class KA109SystemHealth(KnowledgeAlgorithm):
    """Aggregate authoritative component observations without polling services."""

    input_schema = KA109HealthInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-109"

    def _run_logic(self, input_data: KA109HealthInput) -> dict[str, Any]:
        components = [
            {
                "component_id": item.component_id,
                "status": item.status,
                "required": item.required,
                "liveness_passed": item.liveness_passed,
                "readiness_passed": item.readiness_passed,
                "evidence_ref": item.evidence_ref,
            }
            for item in sorted(input_data.components, key=lambda row: row.component_id)
        ]
        required = [item for item in components if item["required"]]
        liveness = all(item["liveness_passed"] for item in required)
        readiness = all(
            item["readiness_passed"] and item["status"] == "healthy"
            for item in required
        )
        return {
            "success": True,
            "status": "system_health_aggregated",
            "overall_status": "healthy" if readiness else "degraded",
            "component_health": components,
            "liveness_verified": liveness,
            "readiness_verified": readiness,
            "components_polled": 0,
            "measurement_status": "authoritative_observations_supplied",
            "deterministic": True,
            "limitations": (
                "The KA aggregates supplied health evidence and performs no network, "
                "filesystem, process, registry, uptime, or disk-space probe."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA109SystemHealth(context).run(context)
