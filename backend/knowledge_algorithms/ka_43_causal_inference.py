"""
KA-043: Causal Inference
Purpose: Infer cause-effect relationships.
"""

import logging
import re
from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)


class KA043Input(BaseModel):
    model_config = ConfigDict(extra="allow")
    effect: str = ""
    candidates: List[Any] = Field(default_factory=list)
    evidence: List[Any] = Field(default_factory=list)


class KA043CausalInference(KnowledgeAlgorithm):
    input_schema = KA043Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-043"

    def _run_logic(self, input_data: KA043Input) -> Dict[str, Any]:
        effect = input_data.effect
        candidates = input_data.candidates

        self.log_execution_step("Inferring Cause", {"effect": effect})

        scored = [
            self._score_candidate(candidate, effect, input_data.evidence, index)
            for index, candidate in enumerate(candidates)
        ]
        scored.sort(key=lambda item: (-item["score"], item["rank"]))
        best = (
            scored[0]
            if scored
            else {
                "candidate": "Unknown",
                "score": 0.0,
                "confidence": 0.0,
                "signals": {},
                "explanation": "No candidate causes were supplied.",
            }
        )

        return {
            "ka_id": "KA-043",
            "success": True,
            "likely_cause": best["candidate"],
            "confidence": best["confidence"],
            "ranked_causes": [
                {
                    "candidate": item["candidate"],
                    "score": item["score"],
                    "confidence": item["confidence"],
                    "signals": item["signals"],
                    "explanation": item["explanation"],
                }
                for item in scored
            ],
            "effect": effect,
            "causal_claim_established": False,
            "candidate_only": True,
            "deterministic": True,
            "limitations": (
                "Confidence is an uncalibrated supplied-evidence support score; "
                "ranking does not establish intervention-level causality."
            ),
        }

    @classmethod
    def _score_candidate(
        cls, candidate: Any, effect: str, evidence: List[Any], rank: int
    ) -> Dict[str, Any]:
        normalized = cls._normalize_candidate(candidate)
        candidate_text = normalized["name"]
        effect_terms = cls._tokens(effect)
        candidate_terms = cls._tokens(candidate_text)
        evidence_terms = cls._tokens(
            " ".join(cls._evidence_text(item) for item in evidence)
        )
        explicit_score = float(
            normalized.get("score", normalized.get("correlation", 0.0)) or 0.0
        )
        temporal = cls._temporal_signal(normalized, evidence)
        mechanism = cls._mechanism_signal(normalized, effect_terms)
        overlap = len(
            (candidate_terms | set(normalized.get("keywords", [])))
            & (effect_terms | evidence_terms)
        )
        evidence_mentions = sum(
            1
            for item in evidence
            if candidate_text.lower() in cls._evidence_text(item).lower()
        )

        signals = {
            "explicit_score": min(1.0, max(0.0, explicit_score)),
            "temporal_precedence": temporal,
            "mechanism_match": mechanism,
            "term_overlap": min(1.0, overlap / max(1, len(effect_terms))),
            "evidence_mentions": min(1.0, evidence_mentions / max(1, len(evidence))),
        }
        weights = {
            "explicit_score": 0.25,
            "temporal_precedence": 0.2,
            "mechanism_match": 0.2,
            "term_overlap": 0.2,
            "evidence_mentions": 0.15,
        }
        score = sum(signals[name] * weight for name, weight in weights.items())
        confidence = round(min(1.0, max(0.0, score)), 3)
        return {
            "candidate": candidate_text,
            "score": round(score, 4),
            "confidence": confidence,
            "signals": signals,
            "rank": rank,
            "explanation": cls._explain(signals),
        }

    @staticmethod
    def _normalize_candidate(candidate: Any) -> Dict[str, Any]:
        if isinstance(candidate, dict):
            name = str(
                candidate.get("name")
                or candidate.get("cause")
                or candidate.get("id")
                or candidate
            )
            return {**candidate, "name": name}
        return {"name": str(candidate)}

    @staticmethod
    def _tokens(text: str) -> set[str]:
        stopwords = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "of",
            "to",
            "and",
            "in",
            "on",
            "for",
            "with",
        }
        return {
            token
            for token in re.findall(r"[a-z0-9]+", text.lower())
            if token not in stopwords
        }

    @staticmethod
    def _evidence_text(item: Any) -> str:
        if isinstance(item, dict):
            return " ".join(str(value) for value in item.values())
        return str(item)

    @staticmethod
    def _temporal_signal(candidate: Dict[str, Any], evidence: List[Any]) -> float:
        if candidate.get("precedes_effect") is True:
            return 1.0
        if candidate.get("precedes_effect") is False:
            return 0.0
        if candidate.get("timestamp") and any(
            isinstance(item, dict) and item.get("effect_timestamp") for item in evidence
        ):
            return 0.75
        return 0.4 if evidence else 0.2

    @staticmethod
    def _mechanism_signal(candidate: Dict[str, Any], effect_terms: set[str]) -> float:
        mechanism = str(candidate.get("mechanism", ""))
        if not mechanism:
            return 0.2
        mechanism_terms = KA043CausalInference._tokens(mechanism)
        return 0.85 if mechanism_terms & effect_terms else 0.55

    @staticmethod
    def _explain(signals: Dict[str, float]) -> str:
        strongest = max(signals, key=signals.get)
        labels = {
            "explicit_score": "provided statistical score",
            "temporal_precedence": "temporal precedence",
            "mechanism_match": "mechanism match",
            "term_overlap": "effect/evidence term overlap",
            "evidence_mentions": "supporting evidence mentions",
        }
        return f"Ranked by {labels[strongest]} with local deterministic scoring."


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA043CausalInference(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-043 Failed: {e}")
        return {"success": False, "error": str(e)}
