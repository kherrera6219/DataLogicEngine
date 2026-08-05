"""KA-020: deterministic L10 loopback-decision proposal."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA020Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "pass_count": 1,
                    "max_passes": 3,
                    "final_confidence": 0.72,
                    "entropy_level": 0.6,
                    "gap_count": 1,
                }
            ]
        },
    )

    pass_count: int = Field(default=1, ge=1, le=100)
    max_passes: int = Field(default=3, ge=1, le=100)
    final_confidence: float = Field(default=1.0, ge=0, le=1)
    entropy_level: float = Field(default=0.0, ge=0, le=1)
    gap_count: int = Field(default=0, ge=0, le=1_000_000)
    minimum_confidence: float = Field(default=0.85, ge=0, le=1)
    maximum_entropy: float = Field(default=0.4, ge=0, le=1)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_dependencies(self) -> KA020Input:
        if self.dependency_results and set(self.dependency_results) != {
            "KA-014",
            "KA-1102",
        }:
            raise ValueError("dependency_results must contain KA-014 and KA-1102")
        return self


class KA020LoopbackTrigger(KnowledgeAlgorithm):
    """Propose another bounded reasoning pass without starting one."""

    input_schema = KA020Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-020"

    def _run_logic(self, input_data: KA020Input) -> dict[str, Any]:
        confidence = input_data.final_confidence
        entropy = input_data.entropy_level
        if input_data.dependency_results:
            confidence = float(
                input_data.dependency_results["KA-014"].get(
                    "confidence_index", confidence
                )
            )
            entropy = float(
                input_data.dependency_results["KA-1102"].get(
                    "normalized_entropy", entropy
                )
            )
        reasons = []
        budget_available = input_data.pass_count < input_data.max_passes
        if confidence < input_data.minimum_confidence:
            reasons.append("confidence_below_minimum")
        if entropy > input_data.maximum_entropy:
            reasons.append("entropy_above_maximum")
        if input_data.gap_count:
            reasons.append("unresolved_gaps")
        should_loop = budget_available and bool(reasons)
        if not budget_available:
            reasons.append("pass_budget_exhausted")
        return {
            "success": True,
            "status": "loopback_decision_proposed",
            "should_loopback": should_loop,
            "reason_codes": reasons,
            "measured_confidence": round(confidence, 8),
            "measured_entropy": round(entropy, 8),
            "next_pass": input_data.pass_count + 1 if should_loop else input_data.pass_count,
            "loopback_applied": False,
            "dependencies_consumed": sorted(input_data.dependency_results),
            "deterministic": True,
            "limitations": (
                "This proposes a bounded loop decision from supplied or committed "
                "measurements. GovernedExecutionService alone may schedule a pass."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA020LoopbackTrigger(context).run(context)
