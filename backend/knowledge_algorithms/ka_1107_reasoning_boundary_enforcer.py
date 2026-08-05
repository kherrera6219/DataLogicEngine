"""KA-1107: deterministic reasoning-boundary enforcement."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class PlannedReasoningStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(min_length=1, max_length=200)
    capability_id: str = Field(min_length=1, max_length=200)
    layer: str = Field(pattern=r"^L(?:[1-9]|10)$")
    query_class: str = Field(min_length=1, max_length=200)


class KA1107Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "planned_steps": [
                        {
                            "step_id": "step-1",
                            "capability_id": "KA-001",
                            "layer": "L1",
                            "query_class": "analysis",
                        }
                    ],
                    "allowed_capability_ids": ["KA-001"],
                    "allowed_layers": ["L1"],
                    "allowed_query_classes": ["analysis"],
                }
            ]
        },
    )

    planned_steps: list[PlannedReasoningStep] = Field(
        default_factory=list, max_length=10_000
    )
    allowed_capability_ids: list[str] = Field(min_length=1, max_length=10_000)
    allowed_layers: list[str] = Field(min_length=1, max_length=10)
    allowed_query_classes: list[str] = Field(min_length=1, max_length=1_000)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)


class KA1107ReasoningBoundaryEnforcer(KnowledgeAlgorithm):
    """Veto plan steps that cross declared capability or layer boundaries."""

    input_schema = KA1107Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1107"

    def _run_logic(self, input_data: KA1107Input) -> dict[str, Any]:
        capabilities = set(input_data.allowed_capability_ids)
        layers = set(input_data.allowed_layers)
        query_classes = set(input_data.allowed_query_classes)
        planned_steps = list(input_data.planned_steps)
        selection = input_data.dependency_results.get("KA-031", {})
        if not planned_steps:
            planned_steps = [
                PlannedReasoningStep(
                    step_id=f"selected-{index}",
                    capability_id=str(capability_id),
                    layer="L1",
                    query_class="routing",
                )
                for index, capability_id in enumerate(
                    selection.get("selected_pipeline", []), start=1
                )
            ]
        if not planned_steps:
            raise ValueError("planned steps or a KA-031 selection result are required")
        decisions = []
        for item in planned_steps:
            blockers = []
            if item.capability_id not in capabilities:
                blockers.append("capability_not_allowed")
            if item.layer not in layers:
                blockers.append("layer_not_allowed")
            if item.query_class not in query_classes:
                blockers.append("query_class_not_allowed")
            decisions.append(
                {
                    "step_id": item.step_id,
                    "decision": "allow" if not blockers else "block",
                    "blockers": blockers,
                }
            )
        return {
            "success": True,
            "status": "reasoning_boundaries_enforced",
            "plan_allowed": all(row["decision"] == "allow" for row in decisions),
            "decisions": decisions,
            "dependency_consumed": "KA-031" if selection else None,
            "execution_started": False,
            "persistence_applied": False,
            "deterministic": True,
            "limitations": (
                "Enforcement covers the supplied plan and policy sets; the "
                "orchestrator must prevent execution of blocked steps."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1107ReasoningBoundaryEnforcer(context).run(context)
