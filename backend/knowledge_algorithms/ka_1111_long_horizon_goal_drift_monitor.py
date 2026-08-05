"""KA-1111: deterministic long-horizon goal-drift monitoring."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class GoalTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(min_length=1, max_length=200)
    sequence: int = Field(ge=0, le=1_000_000_000)
    declared_goal_ids: list[str] = Field(default_factory=list, max_length=1_000)
    observed_goal_ids: list[str] = Field(default_factory=list, max_length=1_000)
    evolution_action_ids: list[str] = Field(default_factory=list, max_length=1_000)


class KA1111Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "traces": [
                        {
                            "run_id": "run-1",
                            "sequence": 1,
                            "declared_goal_ids": ["owner-goal"],
                            "observed_goal_ids": ["owner-goal", "latent-goal"],
                        },
                        {
                            "run_id": "run-2",
                            "sequence": 2,
                            "declared_goal_ids": ["owner-goal"],
                            "observed_goal_ids": ["owner-goal", "latent-goal"],
                        },
                    ]
                }
            ]
        },
    )

    traces: list[GoalTrace] = Field(min_length=2, max_length=100_000)
    minimum_persistent_runs: int = Field(default=2, ge=2, le=100_000)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_runs(self) -> KA1111Input:
        identifiers = [item.run_id for item in self.traces]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("run IDs must be unique")
        if self.dependency_results and set(self.dependency_results) != {"KA-1112"}:
            raise ValueError("dependency_results must contain KA-1112")
        return self


class KA1111LongHorizonGoalDriftMonitor(KnowledgeAlgorithm):
    """Detect undeclared goal identifiers recurring across ordered runs."""

    input_schema = KA1111Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1111"

    def _run_logic(self, input_data: KA1111Input) -> dict[str, Any]:
        introspection_passed = input_data.dependency_results.get(
            "KA-1112", {}
        ).get("audit_passed", True) is True
        occurrences: dict[str, list[str]] = defaultdict(list)
        for trace in sorted(input_data.traces, key=lambda row: row.sequence):
            undeclared = set(trace.observed_goal_ids) - set(trace.declared_goal_ids)
            for goal_id in sorted(undeclared):
                occurrences[goal_id].append(trace.run_id)
        alerts = [
            {
                "goal_id": goal_id,
                "run_ids": run_ids,
                "persistent_run_count": len(run_ids),
                "proposed_constraint": "block_and_owner_review",
            }
            for goal_id, run_ids in sorted(occurrences.items())
            if len(run_ids) >= input_data.minimum_persistent_runs
        ]
        return {
            "success": True,
            "status": "long_horizon_goal_drift_assessed",
            "drift_detected": bool(alerts),
            "alerts": alerts,
            "constraints_applied": 0,
            "introspection_passed": introspection_passed,
            "owner_review_required": bool(alerts) or not introspection_passed,
            "dependencies_consumed": sorted(input_data.dependency_results),
            "deterministic": True,
            "limitations": (
                "Detection depends on stable caller-supplied goal identifiers and "
                "does not infer intent from natural-language traces."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1111LongHorizonGoalDriftMonitor(context).run(context)
