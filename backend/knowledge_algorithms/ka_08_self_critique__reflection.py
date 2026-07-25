"""KA-008: deterministic, evidence-honest self-critique and reflection."""

from __future__ import annotations

import logging
import re
from typing import Any

from pydantic import BaseModel, Field

from backend.knowledge_algorithms.production_utils import (
    load_config,
    normalized_tokens,
    overlap_ratio,
)
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


class KA008Input(BaseModel):
    output_content: str = Field(min_length=1, max_length=100_000)
    query: str = Field(default="", max_length=20_000)
    required_points: list[str] = Field(default_factory=list, max_length=100)
    validation_results: list[dict[str, Any]] = Field(
        default_factory=list,
        max_length=500,
    )
    policy_violations: list[str] = Field(default_factory=list, max_length=100)


class KA008SelfCritique(KnowledgeAlgorithm):
    """Measure structural quality without inventing an accuracy score."""

    input_schema = KA008Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-008"
        self.config = load_config(__file__, "ka_08_config.json")

    def _run_logic(self, input_data: KA008Input) -> dict[str, Any]:
        content = input_data.output_content.strip()
        content_tokens = normalized_tokens(content)
        query_tokens = normalized_tokens(input_data.query)
        required = [
            point.strip()
            for point in input_data.required_points
            if point.strip()
        ]
        covered = [
            point
            for point in required
            if normalized_tokens(point) <= content_tokens
        ]
        validation_decisions = [
            row
            for row in input_data.validation_results
            if row.get("passed") is not None
        ]
        accuracy_score = (
            round(
                sum(bool(row["passed"]) for row in validation_decisions)
                / len(validation_decisions),
                6,
            )
            if validation_decisions
            else None
        )
        completeness = (
            round(len(covered) / len(required), 6)
            if required
            else overlap_ratio(query_tokens, content_tokens)
        )
        sentences = [
            value.strip()
            for value in SENTENCE_RE.split(content)
            if value.strip()
        ]
        average_sentence_words = (
            sum(len(value.split()) for value in sentences) / len(sentences)
            if sentences
            else len(content.split())
        )
        clarity = round(
            max(0.0, min(1.0, 1.0 - max(0.0, average_sentence_words - 24) / 48)),
            6,
        )
        compliance = 1.0 if not input_data.policy_violations else 0.0
        scores: dict[str, float | None] = {
            "accuracy": accuracy_score,
            "completeness": completeness,
            "clarity": clarity,
            "compliance": compliance,
        }
        measured = {
            name: score for name, score in scores.items() if score is not None
        }
        rubrics = self.config.get("rubrics", {})
        weights = {
            name: float(rubrics.get(name, {}).get("weight", 1.0))
            for name in measured
        }
        total_weight = sum(weights.values())
        overall_score = round(
            (
                sum(measured[name] * weights[name] for name in measured)
                / total_weight
            )
            if total_weight
            else 0.0,
            6,
        )
        suggestions = self._suggestions(scores)
        assessment_complete = accuracy_score is not None
        threshold = float(self.config.get("auto_regen_threshold", 0.5))
        regeneration = overall_score < threshold or not assessment_complete
        return {
            "success": True,
            "overall_score": overall_score,
            "rubric_scores": scores,
            "measured_rubrics": sorted(measured),
            "unmeasured_rubrics": [
                name for name, score in scores.items() if score is None
            ],
            "assessment_complete": assessment_complete,
            "covered_required_points": covered,
            "suggestions": suggestions,
            "regeneration_recommended": regeneration,
            "is_sufficient": not regeneration,
            "limitations": (
                "Accuracy is not measured unless explicit validator decisions "
                "are supplied."
            ),
        }

    def _suggestions(
        self,
        scores: dict[str, float | None],
    ) -> list[str]:
        suggestions: list[str] = []
        rubrics = self.config.get("rubrics", {})
        for name, score in scores.items():
            if score is None:
                suggestions.append(f"Measure {name} with an explicit validator.")
                continue
            minimum = float(rubrics.get(name, {}).get("min_score", 0.7))
            if score < minimum:
                suggestions.append(
                    f"Improve {name}: {score:.2f} is below {minimum:.2f}."
                )
        return suggestions or ["Measured quality thresholds are satisfied."]


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA008SelfCritique(context).run(context)
