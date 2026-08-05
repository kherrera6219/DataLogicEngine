"""
KA-058: Interactive Clarification & Learning
Purpose: Decide when the system has insufficient information or high ambiguity and must ask the user for clarification.
"""

import json
import logging
import os
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)


class KA058Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ambiguity_metrics: dict[str, Any] = Field(default_factory=dict)
    competing_intents: list[dict[str, Any]] = Field(default_factory=list, max_length=20)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)


class KA058InteractiveClarificationLearning(KnowledgeAlgorithm):
    """
    KA-058: Ambiguity detection and follow-up generation engine for active learning.
    """

    input_schema = KA058Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-058"
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        try:
            config_path = os.path.join(
                os.path.dirname(__file__), "config", "ka_58_config.json"
            )
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError):
            return {}

    def _run_logic(self, input_data: KA058Input) -> dict[str, Any]:
        dependencies = input_data.dependency_results
        entropy = dependencies.get("KA-1102", {}).get("normalized_entropy")
        intent = dependencies.get("KA-1073", {})
        ambiguity_metrics = dict(input_data.ambiguity_metrics)
        if entropy is not None:
            ambiguity_metrics["overall_entropy"] = float(entropy)
        competing_intents = input_data.competing_intents
        self.log_execution_step(
            "Evaluating Need for Clarification",
            {"intent_count": len(competing_intents)},
        )

        threshold = self.config.get("ambiguity_threshold", 0.6)
        should_clarify = False
        questions = []
        if len(competing_intents) > 1:
            score1 = competing_intents[0].get("score", 0.0)
            score2 = competing_intents[1].get("score", 0.0)
            if (score1 - score2) < (1 - threshold):
                should_clarify = True
                questions.append(
                    f"I found two likely interpretations: '{competing_intents[0].get('name')}' and '{competing_intents[1].get('name')}'. Which one should I prioritize?"
                )
        if ambiguity_metrics.get("overall_entropy", 0.0) > threshold:
            should_clarify = True
            if not questions:
                questions.append(
                    "Your request has some ambiguity. Could you please provide more context regarding the target objective?"
                )

        return {
            "success": True,
            "clarification_required": should_clarify,
            "suggested_questions": questions[
                : self.config.get("max_clarifications_per_turn", 2)
            ],
            "options_provided": self.config.get("suggest_options", True),
            "resolved_intent": intent.get("resolved_intent"),
            "dependencies_consumed": sorted(dependencies),
            "clarification_dispatched": False,
            "learning_applied": False,
            "deterministic": True,
            "limitations": (
                "This returns a bounded clarification proposal only. The owning "
                "request service must decide whether to ask the user; no prompt "
                "is dispatched and no learning state is updated."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA058InteractiveClarificationLearning(context).run(context)
