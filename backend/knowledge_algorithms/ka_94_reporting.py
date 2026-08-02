"""KA-094: deterministic operational report plan."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from backend.knowledge_algorithms.production_utils import (
    load_config,
    stable_identifier,
)
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA094ReportingInput(BaseModel):
    report_name: str = Field(default="diagnostic_health", min_length=1, max_length=100)
    output_format: Literal["json", "html", "csv", "pdf"] = "json"
    sections: dict[str, Any] = Field(default_factory=dict)


class KA094Reporting(KnowledgeAlgorithm):
    """Plan a bounded report without claiming generation or distribution."""

    input_schema = KA094ReportingInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-094"
        self.config = load_config(__file__, "ka_94_config.json")

    def _run_logic(self, input_data: KA094ReportingInput) -> dict[str, Any]:
        allowed_formats = {
            str(value).lower()
            for value in self.config.get("formats", ["json", "html", "csv", "pdf"])
        }
        if input_data.output_format not in allowed_formats:
            return {
                "success": False,
                "status": "unsupported_report_format",
                "allowed_formats": sorted(allowed_formats),
            }
        section_names = sorted(str(name) for name in input_data.sections)
        plan = {
            "report_name": input_data.report_name,
            "output_format": input_data.output_format,
            "section_names": section_names,
            "section_count": len(section_names),
        }
        return {
            "success": True,
            "report_plan": {
                "report_id": stable_identifier("report", plan),
                **plan,
            },
            "artifact_created": False,
            "artifact": None,
            "distributed": False,
            "distribution_receipt": None,
            "limitations": (
                "KA-094 plans a report from caller-supplied section names; an "
                "authoritative reporting service must generate or distribute it."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA094Reporting(context).run(context)
