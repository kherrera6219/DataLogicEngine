"""
KA-041: Abductive Reasoning
Purpose: Infer the most likely explanation for an observation.
"""

import logging
import re
from typing import Any, Dict, List

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class KA041Input(BaseModel):
    model_config = ConfigDict(extra="allow")
    query: str = ""
    observation: str = ""
    rules: List[Any] = Field(default_factory=list)
    explanations: List[Any] = Field(default_factory=list)
    evidence: List[Any] = Field(default_factory=list)


class KA041AbductiveReasoning(KnowledgeAlgorithm):
    """
    KA-041: Perform abductive inference to find best-fit hypotheses.
    """

    input_schema = KA041Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-041"

    def _run_logic(self, input_data: KA041Input) -> Dict[str, Any]:
        observation = input_data.observation or input_data.query
        self.log_execution_step("Abductive Inference", {"obs": observation[:80]})

        candidates = input_data.explanations or self._explanations_from_rules(
            input_data.rules, observation
        )

        ranked = [
            self._score_explanation(
                item, observation, input_data.evidence, input_data.rules
            )
            for item in candidates
        ]
        ranked.sort(key=lambda item: (-item["likelihood"], item["hypothesis"]))
        best = (
            ranked[0]
            if ranked
            else {
                "hypothesis": "Unknown",
                "likelihood": 0.0,
                "rationale": "No explanations supplied.",
            }
        )

        return {
            "success": True,
            "ka_id": self.ka_id,
            "best_explanation": best,
            "hypotheses": ranked,
            "confidence": best["likelihood"],
            "method": "abductive_evidence_fit",
            "hypotheses_validated": False,
            "candidate_only": True,
            "deterministic": True,
            "limitations": (
                "Likelihood is a deterministic evidence-fit score, not a calibrated "
                "probability; the KA never invents an explanation when none is supplied."
            ),
        }

    @classmethod
    def _score_explanation(
        cls, item: Any, observation: str, evidence: List[Any], rules: List[Any]
    ) -> Dict[str, Any]:
        explanation = cls._normalize_explanation(item)
        hypothesis = explanation["hypothesis"]
        hyp_terms = cls._tokens(hypothesis + " " + explanation.get("rationale", ""))
        obs_terms = cls._tokens(observation)
        evidence_text = " ".join(cls._text(value) for value in evidence)
        evidence_terms = cls._tokens(evidence_text)
        rule_support = cls._rule_support(hypothesis, rules)
        overlap = len(hyp_terms & (obs_terms | evidence_terms)) / max(1, len(hyp_terms))
        evidence_mentions = 1.0 if hypothesis.lower() in evidence_text.lower() else 0.0
        prior = float(
            explanation.get("prior", explanation.get("likelihood", 0.45)) or 0.45
        )
        likelihood = round(
            min(
                0.95,
                max(
                    0.05,
                    prior * 0.25
                    + overlap * 0.35
                    + rule_support * 0.25
                    + evidence_mentions * 0.15,
                ),
            ),
            3,
        )
        return {
            "hypothesis": hypothesis,
            "likelihood": likelihood,
            "rationale": explanation.get("rationale")
            or "Ranked by local evidence fit.",
            "signals": {
                "prior": round(prior, 3),
                "term_overlap": round(overlap, 3),
                "rule_support": round(rule_support, 3),
                "evidence_mentions": evidence_mentions,
            },
        }

    @classmethod
    def _explanations_from_rules(
        cls, rules: List[Any], observation: str
    ) -> List[Dict[str, Any]]:
        explanations = []
        obs_terms = cls._tokens(observation)
        for rule in rules:
            text = cls._text(rule)
            if not text:
                continue
            lhs, _, rhs = text.partition("->")
            hypothesis = lhs.strip() if rhs and cls._tokens(rhs) & obs_terms else text
            explanations.append(
                {
                    "hypothesis": hypothesis,
                    "rationale": f"Derived from rule: {text}",
                    "prior": 0.55,
                }
            )
        return explanations

    @classmethod
    def _rule_support(cls, hypothesis: str, rules: List[Any]) -> float:
        if not rules:
            return 0.0
        hyp_terms = cls._tokens(hypothesis)
        supporting = sum(
            1 for rule in rules if hyp_terms & cls._tokens(cls._text(rule))
        )
        return supporting / len(rules)

    @staticmethod
    def _normalize_explanation(item: Any) -> Dict[str, Any]:
        if isinstance(item, dict):
            return {
                **item,
                "hypothesis": str(
                    item.get("hypothesis")
                    or item.get("name")
                    or item.get("cause")
                    or item
                ),
            }
        return {"hypothesis": str(item), "rationale": "Provided explanation candidate"}

    @staticmethod
    def _text(value: Any) -> str:
        if isinstance(value, dict):
            return " ".join(str(item) for item in value.values())
        return str(value)

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {
            token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2
        }


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA041AbductiveReasoning(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-041 Fatal Error: {e}")
        return {"success": False, "error": str(e)}
