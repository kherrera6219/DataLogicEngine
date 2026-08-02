import logging
import json
import os
import re
from typing import Dict, Any
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Signal vocabularies for the weighted complexity heuristic. Kept module-level
# so they are easy to extend; the per-signal weights live in ka_13... config.
_AMBIGUITY_TERMS = (
    "maybe", "might", "unclear", "ambiguous", "approximately", "possibly",
    "versus", " vs ", "compare", "trade-off", "tradeoff", "pros and cons",
    "or should", "either", "depends",
)
_DOMAIN_TERMS = (
    "regulation", "regulatory", "compliance", "statute", "clause", "hipaa",
    "sox", "gdpr", "clinical", "patient", "diagnosis", "financial", "audit",
    "sql", "api", "algorithm", "encryption", "kubernetes", "architecture",
    "liability", "jurisdiction", "actuarial",
)


class KA113Input(BaseModel):
    query: str = ""
    dependency_results: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

class KA113ComplexityRouter(KnowledgeAlgorithm):
    """
    KA-113: Query complexity analysis and pipeline routing engine.
    """
    input_schema = KA113Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-113"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_113_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA113Input) -> Dict[str, Any]:
        dependency_results = input_data.dependency_results
        validation = dependency_results.get("KA-004", {})
        classification = dependency_results.get("KA-005", {})
        query = str(
            validation.get("normalized_query")
            if validation.get("is_valid") is True
            else input_data.query
        )
        signals = self._complexity_signals(query)
        self.log_execution_step("Analyzing Query Complexity", {"len": len(query), "signals": signals})

        # Weighted blend of the three signals the config declares. Falls back to
        # the documented defaults; weights are normalized so the score stays 0–1.
        weights = self.config.get("heuristic_weights", {
            "query_length": 0.2, "semantic_ambiguity": 0.5, "domain_specificity": 0.3,
        })
        total_weight = sum(float(w) for w in weights.values()) or 1.0
        complexity_score = round(min(1.0, max(0.0, (
            weights.get("query_length", 0.2) * signals["query_length"]
            + weights.get("semantic_ambiguity", 0.5) * signals["semantic_ambiguity"]
            + weights.get("domain_specificity", 0.3) * signals["domain_specificity"]
        ) / total_weight)), 4)

        thresholds = self.config.get("complexity_thresholds", {"low": 0.3, "medium": 0.7})
        if complexity_score < thresholds.get("low", 0.3):
            tier = "low"
        elif complexity_score < thresholds.get("medium", 0.7):
            tier = "medium"
        else:
            tier = "high"

        dependency_tier = {
            "trivial": "low",
            "moderate": "medium",
            "high_stakes": "high",
            "extreme": "high",
            "autonomous": "high",
        }.get(str(classification.get("suggested_tier") or "").lower())
        tier_order = {"low": 1, "medium": 2, "high": 3}
        if dependency_tier and tier_order[dependency_tier] > tier_order[tier]:
            tier = dependency_tier

        return {
            "success": True,
            "complexity_score": complexity_score,
            "complexity_tier": tier,
            "signals": signals,
            "target_pipeline": self.config.get("routing_map", {}).get(tier, "default"),
            "dependency_routing": {
                "normalized_query_consumed": validation.get("is_valid") is True,
                "classification_tier": classification.get("suggested_tier"),
            },
        }

    @staticmethod
    def _complexity_signals(query: str) -> Dict[str, float]:
        """Three normalized 0–1 signals: length, semantic ambiguity, domain specificity."""
        q = query.lower()
        # Length: saturates around 200 chars.
        length_sig = min(1.0, len(query) / 200.0)
        # Ambiguity: multi-question / comparison / vague-term density.
        ambiguity_hits = sum(1 for term in _AMBIGUITY_TERMS if term in q)
        ambiguity_hits += max(0, query.count("?") - 1)  # multiple questions
        ambiguity_hits += len(re.findall(r"\b(and|but|however|whereas)\b", q)) // 2
        ambiguity_sig = min(1.0, ambiguity_hits / 4.0)
        # Domain specificity: regulated/technical vocabulary density.
        domain_hits = sum(1 for term in _DOMAIN_TERMS if term in q)
        domain_sig = min(1.0, domain_hits / 3.0)
        return {
            "query_length": round(length_sig, 4),
            "semantic_ambiguity": round(ambiguity_sig, 4),
            "domain_specificity": round(domain_sig, 4),
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA113ComplexityRouter(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-113 Failed: {e}")
        return {"success": False, "error": str(e)}
