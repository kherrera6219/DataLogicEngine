"""KA-1081: fail-closed simulation budget admission decision."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA1081Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        allow_inf_nan=False,
        json_schema_extra={
            "examples": [
                {
                    "estimated_duration_ms": 500,
                    "estimated_tokens": 1_000,
                    "estimated_cost_units": 0,
                    "estimated_peak_memory_mb": 256,
                    "recursion_depth": 2,
                    "concurrency": 1,
                    "maximum_duration_ms": 1_000,
                    "maximum_tokens": 2_000,
                    "maximum_cost_units": 1,
                    "maximum_peak_memory_mb": 512,
                    "maximum_recursion_depth": 3,
                    "maximum_concurrency": 2,
                }
            ]
        },
    )

    estimated_duration_ms: float = Field(ge=0, le=86_400_000)
    estimated_tokens: int = Field(ge=0, le=1_000_000_000)
    estimated_cost_units: float = Field(ge=0, le=1_000_000_000)
    estimated_peak_memory_mb: float = Field(ge=0, le=10_000_000)
    recursion_depth: int = Field(ge=0, le=10_000)
    concurrency: int = Field(ge=1, le=100_000)
    maximum_duration_ms: float = Field(gt=0, le=86_400_000)
    maximum_tokens: int = Field(ge=0, le=1_000_000_000)
    maximum_cost_units: float = Field(ge=0, le=1_000_000_000)
    maximum_peak_memory_mb: float = Field(gt=0, le=10_000_000)
    maximum_recursion_depth: int = Field(ge=0, le=10_000)
    maximum_concurrency: int = Field(ge=1, le=100_000)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)


class KA1081SimulationBudgetEnforcer(KnowledgeAlgorithm):
    """Return a deterministic admission decision without starting work."""

    input_schema = KA1081Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-1081"

    def _run_logic(self, input_data: KA1081Input) -> dict[str, Any]:
        dependency_estimate = dict(
            input_data.dependency_results.get("KA-1080", {}).get("estimate") or {}
        )
        estimated_duration_ms = float(
            dependency_estimate.get("duration_ms", input_data.estimated_duration_ms)
        )
        estimated_tokens = int(
            dependency_estimate.get("tokens", input_data.estimated_tokens)
        )
        estimated_cost_units = float(
            dependency_estimate.get("cost_units", input_data.estimated_cost_units)
        )
        estimated_peak_memory_mb = float(
            dependency_estimate.get(
                "peak_memory_mb",
                input_data.estimated_peak_memory_mb,
            )
        )
        checks = {
            "duration": (
                estimated_duration_ms,
                input_data.maximum_duration_ms,
            ),
            "tokens": (
                estimated_tokens,
                input_data.maximum_tokens,
            ),
            "cost": (
                estimated_cost_units,
                input_data.maximum_cost_units,
            ),
            "memory": (
                estimated_peak_memory_mb,
                input_data.maximum_peak_memory_mb,
            ),
            "recursion": (
                input_data.recursion_depth,
                input_data.maximum_recursion_depth,
            ),
            "concurrency": (
                input_data.concurrency,
                input_data.maximum_concurrency,
            ),
        }
        violations = [
            {
                "budget": name,
                "estimated": estimate,
                "maximum": maximum,
            }
            for name, (estimate, maximum) in checks.items()
            if estimate > maximum
        ]
        allowed = not violations
        return {
            "success": True,
            "status": "budget_allowed" if allowed else "budget_blocked",
            "allowed": allowed,
            "violations": violations,
            "execution_started": False,
            "deterministic": True,
            "estimate_source": (
                "KA-1080_dependency"
                if dependency_estimate
                else "direct_input"
            ),
            "limitations": (
                "Admission relies on supplied estimates. The simulation "
                "orchestrator must enforce live cancellation and resource "
                "limits during execution."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA1081SimulationBudgetEnforcer(context).run(context)
