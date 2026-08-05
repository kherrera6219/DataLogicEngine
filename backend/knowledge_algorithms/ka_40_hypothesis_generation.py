"""
KA-040: Hypothesis Generation
Purpose: Generate testable hypotheses for unknown phenomena.
"""

import logging
import re
from typing import Any, Dict, List

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class KA040Input(BaseModel):
    model_config = ConfigDict(extra="allow")
    observation: str = ""
    context: Dict[str, Any] = Field(default_factory=dict)
    variables: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    max_hypotheses: int = 5


class KA040HypothesisGeneration(KnowledgeAlgorithm):
    input_schema = KA040Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-040"

    def _run_logic(self, input_data: KA040Input) -> Dict[str, Any]:
        observation = input_data.observation or str(
            input_data.model_dump().get("query", "")
        )
        variables = input_data.variables or self._infer_variables(
            observation, input_data.context
        )
        max_hypotheses = max(1, min(10, self._safe_int(input_data.max_hypotheses, 5)))

        self.log_execution_step(
            "Generating Hypotheses",
            {"obs": observation[:80], "variables": len(variables)},
        )

        hypotheses = self._build_hypotheses(
            observation, variables, input_data.constraints, max_hypotheses
        )
        return {
            "ka_id": self.ka_id,
            "success": True,
            "status": "hypothesis_candidates_proposed",
            "hypotheses": hypotheses,
            "hypothesis_count": len(hypotheses),
            "method": "variable_signal_hypothesis_generation",
            "calibrated_probability": False,
            "hypotheses_validated": False,
            "external_effect_applied": False,
            "deterministic": True,
            "limitations": (
                "Candidates are template-based test proposals from supplied terms; "
                "they are not causal findings or calibrated probabilities."
            ),
        }

    @classmethod
    def _build_hypotheses(
        cls,
        observation: str,
        variables: List[str],
        constraints: List[str],
        max_hypotheses: int,
    ) -> List[Dict[str, Any]]:
        templates = [
            (
                "causal",
                "{variable} is a direct driver of the observed change.",
                "Test whether changes in {variable} precede the observation.",
            ),
            (
                "interaction",
                "{variable} interacts with another system factor to amplify the observation.",
                "Segment records by {variable} and compare effect size.",
            ),
            (
                "threshold",
                "{variable} crossed a threshold that changed system behavior.",
                "Find breakpoints in {variable} around the observation window.",
            ),
            (
                "measurement",
                "The observation is partly explained by a change in how {variable} is measured.",
                "Compare collection rules and missingness before and after the observation.",
            ),
            (
                "confounder",
                "{variable} is correlated with an unobserved confounder.",
                "Control for adjacent variables and check whether the signal remains.",
            ),
        ]
        if not variables:
            variables = sorted(cls._tokens(observation))[:3] or ["primary factor"]

        hypotheses: List[Dict[str, Any]] = []
        for index, variable in enumerate(variables[:max_hypotheses]):
            kind, statement, test = templates[index % len(templates)]
            priority_score = round(
                1.0 / (index + 1) + min(len(constraints), 3) * 0.01,
                3,
            )
            hypotheses.append(
                {
                    "id": f"H{index + 1}",
                    "type": kind,
                    "statement": statement.format(variable=variable),
                    "rationale": f"Generated from observation terms and candidate variable '{variable}'.",
                    "test": test.format(variable=variable),
                    "constraints_considered": constraints,
                    "priority_score": max(0.0, min(1.0, priority_score)),
                    "evidence_status": "untested",
                }
            )
        return hypotheses

    @classmethod
    def _infer_variables(cls, observation: str, context: Dict[str, Any]) -> List[str]:
        variables = []
        for key, value in context.items():
            if isinstance(value, (int, float, str, bool)):
                variables.append(str(key))
        variables.extend(sorted(cls._tokens(observation))[:5])
        seen = set()
        return [item for item in variables if not (item in seen or seen.add(item))]

    @staticmethod
    def _tokens(text: str) -> set[str]:
        stopwords = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "is",
            "are",
            "was",
            "were",
            "of",
            "to",
            "in",
            "for",
        }
        return {
            token
            for token in re.findall(r"[a-z0-9]+", text.lower())
            if len(token) > 3 and token not in stopwords
        }

    @staticmethod
    def _safe_int(value: Any, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA040HypothesisGeneration(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-040 Failed: {e}")
        return {"success": False, "error": str(e)}
