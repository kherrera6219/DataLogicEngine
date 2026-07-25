"""KA-091: deterministic visualization specification builder."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from backend.knowledge_algorithms.production_utils import (
    load_config,
    stable_identifier,
)
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA091VisualizationInput(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)
    viz_type: str = Field(default="graph", min_length=1, max_length=40)
    title: str | None = Field(default=None, max_length=200)

    @field_validator("viz_type")
    @classmethod
    def normalize_type(cls, value: str) -> str:
        return value.strip().lower()


class KA091Visualization(KnowledgeAlgorithm):
    """Create a stable renderer-neutral chart specification, not a fake asset."""

    input_schema = KA091VisualizationInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-091"
        self.config = load_config(__file__, "ka_91_config.json")

    def _run_logic(
        self,
        input_data: KA091VisualizationInput,
    ) -> dict[str, Any]:
        allowed = {
            str(value).lower()
            for value in self.config.get(
                "chart_types",
                ["line", "bar", "radar", "sankey", "graph"],
            )
        }
        if input_data.viz_type not in allowed:
            return {
                "success": False,
                "status": "unsupported_visualization_type",
                "allowed_types": sorted(allowed),
            }
        node_count = len(input_data.data.get("nodes", []))
        max_nodes = int(self.config.get("max_nodes_to_render", 500))
        if node_count > max_nodes:
            return {
                "success": False,
                "status": "visualization_budget_exceeded",
                "node_count": node_count,
                "max_nodes": max_nodes,
            }
        spec = {
            "type": input_data.viz_type,
            "title": input_data.title,
            "theme": self.config.get("theme", "standard"),
            "data": input_data.data,
            "interaction_enabled": bool(
                self.config.get("interaction_enabled", True)
            ),
        }
        return {
            "success": True,
            "visualization": {
                "chart_id": stable_identifier("viz", spec),
                **spec,
            },
            "rendered": False,
            "export_options": self.config.get("export_formats", ["png", "svg"]),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA091Visualization(context).run(context)
