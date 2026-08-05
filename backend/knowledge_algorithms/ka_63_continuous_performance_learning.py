"""KA-063: deterministic performance-tuning proposal generation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA063LearningInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome_metrics: dict[str, Any] = Field(default_factory=dict)
    feedback: list[dict[str, Any]] = Field(default_factory=list, max_length=10_000)


class KA063ContinuousPerformanceLearning(KnowledgeAlgorithm):
    """Recommend bounded tuning review without updating a model or profile."""

    input_schema = KA063LearningInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-063"

    def _run_logic(self, input_data: KA063LearningInput) -> dict[str, Any]:
        suggestions = []
        accuracy = input_data.outcome_metrics.get("measured_accuracy")
        latency = input_data.outcome_metrics.get("p95_latency_ms")
        if (
            isinstance(accuracy, (int, float))
            and 0 <= float(accuracy) <= 1
            and float(accuracy) < 0.8
        ):
            suggestions.append(
                {
                    "parameter": "pipeline_depth",
                    "direction": "increase_review",
                    "basis": "measured_accuracy_below_0.8",
                }
            )
        if isinstance(latency, (int, float)) and float(latency) > 1_000:
            suggestions.append(
                {
                    "parameter": "concurrency_level",
                    "direction": "benchmark_higher_concurrency",
                    "basis": "measured_p95_latency_above_1000ms",
                }
            )
        return {
            "success": True,
            "status": "tuning_review_proposed" if suggestions else "no_change_proposed",
            "suggestions": suggestions,
            "feedback_record_count": len(input_data.feedback),
            "profile_update_applied": False,
            "model_training_started": False,
            "deterministic": True,
            "limitations": (
                "Recommendations use caller-supplied aggregate measurements. No "
                "online learning, configuration change, or model update occurs."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA063ContinuousPerformanceLearning(context).run(context)
