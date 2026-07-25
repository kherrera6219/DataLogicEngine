"""KA-1036: bounded deterministic multi-objective Pareto optimization."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class ParetoObjective(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    direction: Literal["maximize", "minimize"]
    weight: float = Field(default=1.0, gt=0, le=100)


class ParetoOption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    option_id: str = Field(min_length=1, max_length=200)
    metrics: dict[str, float] = Field(min_length=1, max_length=20)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParetoConstraint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objective: str = Field(min_length=1, max_length=100)
    minimum: float | None = None
    maximum: float | None = None

    @model_validator(mode="after")
    def validate_bounds(self) -> ParetoConstraint:
        if self.minimum is None and self.maximum is None:
            raise ValueError("constraint requires minimum or maximum")
        if (
            self.minimum is not None
            and self.maximum is not None
            and self.minimum > self.maximum
        ):
            raise ValueError("constraint minimum exceeds maximum")
        return self


class KA1036Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        allow_inf_nan=False,
        json_schema_extra={
            "examples": [
                {
                    "objectives": [
                        {
                            "name": "quality",
                            "direction": "maximize",
                            "weight": 1,
                        }
                    ],
                    "options": [
                        {
                            "option_id": "candidate-a",
                            "metrics": {"quality": 0.8},
                        }
                    ],
                }
            ]
        },
    )

    objectives: list[ParetoObjective] = Field(
        min_length=1,
        max_length=20,
    )
    options: list[ParetoOption] = Field(min_length=1, max_length=500)
    constraints: list[ParetoConstraint] = Field(
        default_factory=list,
        max_length=40,
    )
    recommendation_limit: int = Field(default=10, ge=1, le=50)

    @model_validator(mode="after")
    def validate_references(self) -> KA1036Input:
        objective_names = [item.name for item in self.objectives]
        if len(objective_names) != len(set(objective_names)):
            raise ValueError("objective names must be unique")
        option_ids = [item.option_id for item in self.options]
        if len(option_ids) != len(set(option_ids)):
            raise ValueError("option IDs must be unique")
        expected = set(objective_names)
        for option in self.options:
            if set(option.metrics) != expected:
                raise ValueError(
                    f"{option.option_id} metrics must match all objectives"
                )
        if any(item.objective not in expected for item in self.constraints):
            raise ValueError("constraint references an unknown objective")
        return self


class KA1036ParetoOptimizationEngine(KnowledgeAlgorithm):
    """Return the non-dominated feasible set and a transparent ranking."""

    input_schema = KA1036Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1036"

    @staticmethod
    def _dominates(
        left: ParetoOption,
        right: ParetoOption,
        objectives: list[ParetoObjective],
    ) -> bool:
        no_worse = True
        strictly_better = False
        for objective in objectives:
            left_value = left.metrics[objective.name]
            right_value = right.metrics[objective.name]
            if objective.direction == "maximize":
                no_worse = no_worse and left_value >= right_value
                strictly_better = strictly_better or left_value > right_value
            else:
                no_worse = no_worse and left_value <= right_value
                strictly_better = strictly_better or left_value < right_value
        return no_worse and strictly_better

    @staticmethod
    def _constraint_violations(
        option: ParetoOption,
        constraints: list[ParetoConstraint],
    ) -> list[str]:
        violations: list[str] = []
        for constraint in constraints:
            value = option.metrics[constraint.objective]
            if constraint.minimum is not None and value < constraint.minimum:
                violations.append(f"{constraint.objective}:below_minimum")
            if constraint.maximum is not None and value > constraint.maximum:
                violations.append(f"{constraint.objective}:above_maximum")
        return violations

    @staticmethod
    def _weighted_score(
        option: ParetoOption,
        feasible: list[ParetoOption],
        objectives: list[ParetoObjective],
    ) -> float:
        weighted = 0.0
        total_weight = sum(item.weight for item in objectives)
        for objective in objectives:
            values = [item.metrics[objective.name] for item in feasible]
            low = min(values)
            high = max(values)
            if high == low:
                normalized = 1.0
            elif objective.direction == "maximize":
                normalized = (option.metrics[objective.name] - low) / (high - low)
            else:
                normalized = (high - option.metrics[objective.name]) / (high - low)
            weighted += normalized * objective.weight
        return round(weighted / total_weight, 8)

    def _run_logic(self, input_data: KA1036Input) -> dict[str, Any]:
        violations = {
            option.option_id: self._constraint_violations(
                option,
                input_data.constraints,
            )
            for option in input_data.options
        }
        feasible = sorted(
            (
                option
                for option in input_data.options
                if not violations[option.option_id]
            ),
            key=lambda item: item.option_id,
        )
        if not feasible:
            return {
                "success": False,
                "status": "no_feasible_options",
                "constraint_violations": violations,
                "limitations": (
                    "No recommendation is possible until at least one option "
                    "satisfies every supplied constraint."
                ),
            }

        front = [
            option
            for option in feasible
            if not any(
                self._dominates(other, option, input_data.objectives)
                for other in feasible
                if other.option_id != option.option_id
            )
        ]
        ranked = sorted(
            (
                {
                    "option_id": option.option_id,
                    "weighted_score": self._weighted_score(
                        option,
                        feasible,
                        input_data.objectives,
                    ),
                    "metrics": option.metrics,
                }
                for option in front
            ),
            key=lambda item: (-item["weighted_score"], item["option_id"]),
        )
        return {
            "success": True,
            "status": "pareto_front_computed",
            "pareto_front": [item["option_id"] for item in ranked],
            "recommended_set": ranked[: input_data.recommendation_limit],
            "feasible_option_count": len(feasible),
            "infeasible_options": {
                option_id: reasons
                for option_id, reasons in sorted(violations.items())
                if reasons
            },
            "deterministic": True,
            "limitations": (
                "The recommendation is conditional on caller-supplied metrics, "
                "constraints, directions, and weights; it is not a factual "
                "validation of those inputs."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1036ParetoOptimizationEngine(context).run(context)
