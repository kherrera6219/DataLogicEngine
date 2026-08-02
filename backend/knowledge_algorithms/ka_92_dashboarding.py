"""KA-092: deterministic dashboard blueprint composition."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from backend.knowledge_algorithms.production_utils import (
    load_config,
    stable_identifier,
)
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class DashboardWidget(BaseModel):
    widget_id: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1, max_length=200)
    value: int | float | str | bool | None = None
    status: str = Field(default="measured", min_length=1, max_length=40)


class KA092DashboardInput(BaseModel):
    dashboard_id: str = Field(default="ops_main", min_length=1, max_length=100)
    widgets: list[DashboardWidget] = Field(default_factory=list, max_length=100)
    refresh_ms: int | None = Field(default=None, ge=1_000, le=3_600_000)

    @field_validator("widgets")
    @classmethod
    def unique_widgets(
        cls,
        value: list[DashboardWidget],
    ) -> list[DashboardWidget]:
        identifiers = [widget.widget_id for widget in value]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("dashboard widget_id values must be unique")
        return value


class KA092Dashboarding(KnowledgeAlgorithm):
    """Compose supplied measurements into a renderer-neutral blueprint."""

    input_schema = KA092DashboardInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-092"
        self.config = load_config(__file__, "ka_92_config.json")

    def _run_logic(self, input_data: KA092DashboardInput) -> dict[str, Any]:
        widgets = [widget.model_dump(mode="json") for widget in input_data.widgets]
        refresh_ms = input_data.refresh_ms or int(
            self.config.get("refresh_interval_ms", 5_000)
        )
        blueprint = {
            "dashboard_id": input_data.dashboard_id,
            "layout_type": self.config.get("layout", "grid"),
            "refresh_ms": refresh_ms,
            "composition": [
                {**widget, "position": position}
                for position, widget in enumerate(widgets)
            ],
        }
        return {
            "success": True,
            "blueprint_id": stable_identifier("dashboard", blueprint),
            "dashboard_blueprint": blueprint,
            "rendered": False,
            "persisted": False,
            "measurement_source": "caller_supplied_operational_snapshot",
            "limitations": (
                "KA-092 composes a dashboard blueprint; it does not render, "
                "persist, or stream dashboard data."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA092Dashboarding(context).run(context)
