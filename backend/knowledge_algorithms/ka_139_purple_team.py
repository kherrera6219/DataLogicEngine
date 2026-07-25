"""KA-139: deterministic purple-team control coverage analysis."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class PurpleScenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario_id: str = Field(min_length=1, max_length=200)
    technique_id: str = Field(min_length=1, max_length=200)
    severity: Literal["low", "medium", "high", "critical"]
    expected_detection_control_ids: list[str] = Field(
        default_factory=list, max_length=1_000
    )
    expected_response_control_ids: list[str] = Field(
        default_factory=list, max_length=1_000
    )


class KA139Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "scenarios": [
                        {
                            "scenario_id": "scenario-1",
                            "technique_id": "T1001",
                            "severity": "high",
                            "expected_detection_control_ids": ["detect-1"],
                            "expected_response_control_ids": ["respond-1"],
                        }
                    ],
                    "observed_control_ids": ["detect-1"],
                }
            ]
        },
    )

    scenarios: list[PurpleScenario] = Field(min_length=1, max_length=10_000)
    observed_control_ids: list[str] = Field(default_factory=list, max_length=100_000)

    @model_validator(mode="after")
    def validate_ids(self) -> KA139Input:
        identifiers = [item.scenario_id for item in self.scenarios]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("scenario IDs must be unique")
        return self


class KA139PurpleTeam(KnowledgeAlgorithm):
    """Compare expected red scenarios with observed blue-team controls."""

    input_schema = KA139Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-139"

    def _run_logic(self, input_data: KA139Input) -> dict[str, Any]:
        observed = set(input_data.observed_control_ids)
        assessments = []
        for item in sorted(input_data.scenarios, key=lambda row: row.scenario_id):
            expected = set(item.expected_detection_control_ids) | set(
                item.expected_response_control_ids
            )
            missing = sorted(expected - observed)
            coverage = len(expected & observed) / len(expected) if expected else 0.0
            assessments.append(
                {
                    "scenario_id": item.scenario_id,
                    "technique_id": item.technique_id,
                    "coverage_ratio": round(coverage, 8),
                    "missing_control_ids": missing,
                    "accepted": bool(expected) and not missing,
                }
            )
        return {
            "success": True,
            "status": "purple_team_coverage_assessed",
            "assessments": assessments,
            "adversarial_actions_executed": 0,
            "controls_changed": 0,
            "deterministic": True,
            "limitations": (
                "This compares declared scenarios and control evidence; it does "
                "not execute attacks or prove control effectiveness."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA139PurpleTeam(context).run(context)
