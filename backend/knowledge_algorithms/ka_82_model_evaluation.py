"""KA-082: measured model evaluation from caller-supplied outcomes."""

from __future__ import annotations

import json
import logging
from typing import Any

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, ConfigDict, Field, model_validator

logger = logging.getLogger(__name__)


class KA082EvaluationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_id: str = Field(min_length=1, max_length=200)
    test_set: str = Field(min_length=1, max_length=200)
    predictions: list[Any] = Field(min_length=1, max_length=1_000_000)
    labels: list[Any] = Field(min_length=1, max_length=1_000_000)
    acceptance_accuracy: float = Field(default=0.8, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _validate_observations(self) -> "KA082EvaluationInput":
        if len(self.predictions) != len(self.labels):
            raise ValueError("predictions and labels must have equal length")
        for value in [*self.predictions, *self.labels]:
            if isinstance(value, (dict, list, set, tuple)):
                raise ValueError("predictions and labels must contain scalar values")
            try:
                json.dumps(value, allow_nan=False)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "predictions and labels must be finite JSON scalar values"
                ) from exc
        return self


class KA082ModelEvaluation(KnowledgeAlgorithm):
    """Calculate accuracy and macro classification metrics without baselines."""

    input_schema = KA082EvaluationInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-082"

    def _run_logic(self, input_data: KA082EvaluationInput) -> dict[str, Any]:
        self.log_execution_step(
            "Evaluating Measured Model Outcomes",
            {
                "model_id": input_data.model_id,
                "test_set": input_data.test_set,
                "sample_count": len(input_data.labels),
            },
        )
        metrics = self._classification_metrics(
            input_data.predictions,
            input_data.labels,
        )
        return {
            "success": True,
            "schema_version": "dle.model-evaluation.v1",
            "status": "MEASURED",
            "evaluated_model": input_data.model_id,
            "test_set_used": input_data.test_set,
            "sample_count": len(input_data.labels),
            "class_count": len(
                {self._label_key(value) for value in input_data.labels}
            ),
            "metrics": metrics,
            "metric_averaging": "macro",
            "acceptance_accuracy": input_data.acceptance_accuracy,
            "meets_acceptance_threshold": (
                metrics["accuracy"] >= input_data.acceptance_accuracy
            ),
            "predictions_generated": False,
            "evaluation_artifact_created": False,
        }

    @classmethod
    def _classification_metrics(
        cls,
        predictions: list[Any],
        labels: list[Any],
    ) -> dict[str, float]:
        label_keys = [cls._label_key(value) for value in labels]
        prediction_keys = [cls._label_key(value) for value in predictions]
        classes = sorted(set(label_keys) | set(prediction_keys))
        total = len(label_keys)
        accuracy = sum(
            prediction == label
            for prediction, label in zip(prediction_keys, label_keys, strict=True)
        ) / total

        precisions: list[float] = []
        recalls: list[float] = []
        f1_scores: list[float] = []
        for label_class in classes:
            true_positive = sum(
                prediction == label_class and label == label_class
                for prediction, label in zip(
                    prediction_keys,
                    label_keys,
                    strict=True,
                )
            )
            false_positive = sum(
                prediction == label_class and label != label_class
                for prediction, label in zip(
                    prediction_keys,
                    label_keys,
                    strict=True,
                )
            )
            false_negative = sum(
                prediction != label_class and label == label_class
                for prediction, label in zip(
                    prediction_keys,
                    label_keys,
                    strict=True,
                )
            )
            precision = true_positive / max(1, true_positive + false_positive)
            recall = true_positive / max(1, true_positive + false_negative)
            f1 = (
                0.0
                if precision + recall == 0.0
                else 2.0 * precision * recall / (precision + recall)
            )
            precisions.append(precision)
            recalls.append(recall)
            f1_scores.append(f1)

        return {
            "accuracy": round(accuracy, 4),
            "macro_precision": round(sum(precisions) / len(precisions), 4),
            "macro_recall": round(sum(recalls) / len(recalls), 4),
            "macro_f1": round(sum(f1_scores) / len(f1_scores), 4),
        }

    @staticmethod
    def _label_key(value: Any) -> str:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )


def run(context: dict[str, Any]) -> dict[str, Any]:
    try:
        return KA082ModelEvaluation(context).run(context)
    except Exception as exc:  # pragma: no cover - legacy adapter boundary
        logger.error("KA-082 failed: %s", exc)
        return {"success": False, "error": str(exc)}
