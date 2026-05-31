"""
KA-031: Algorithm Selection Engine
Purpose: Select the optimal sequence of Knowledge Algorithms for a query class, complexity tier, and policy constraints.
"""
import json
import logging
import os
from typing import Any, Dict, List

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class KA031Input(BaseModel):
    model_config = ConfigDict(extra="allow")
    query_class: str = Field("GENERAL", description="The classification of the query")
    complexity_tier: str = Field("standard", description="The complexity tier")
    policy_flags: List[str] = Field(default_factory=list, description="Optional policy flags affecting selection")
    query: str = ""
    budget: Dict[str, Any] = Field(default_factory=dict)
    available_kas: List[str] = Field(default_factory=list)


class KA031AlgorithmSelectionEngine(KnowledgeAlgorithm):
    """
    KA-031: Optimal KA pipeline selection engine based on query class, budget, and safety policy.
    """
    input_schema = KA031Input

    QUERY_CLASS_KAS = {
        "GENERAL": ["KA-001", "KA-004", "KA-005"],
        "REASONING": ["KA-001", "KA-040", "KA-041", "KA-043"],
        "COUNTERFACTUAL": ["KA-042", "KA-070"],
        "DATA": ["KA-072", "KA-073", "KA-075", "KA-079"],
        "ML": ["KA-081", "KA-082", "KA-086"],
        "OPERATIONS": ["KA-080", "KA-095", "KA-106", "KA-109"],
        "SECURITY": ["KA-034", "KA-061", "KA-097", "KA-111"],
    }

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-031"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_31_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA031Input) -> Dict[str, Any]:
        query_class = self._infer_query_class(input_data)
        complexity_tier = input_data.complexity_tier or self.config.get("default_complexity_tier", "standard")
        policy_flags = {flag.lower() for flag in input_data.policy_flags}
        self.log_execution_step("Selecting KA Pipeline", {"query_class": query_class, "tier": complexity_tier})

        candidates = self._candidate_pipeline(query_class, complexity_tier, policy_flags)
        available = set(input_data.available_kas)
        if available:
            candidates = [ka_id for ka_id in candidates if ka_id in available]
        scored = [self._score_ka(ka_id, query_class, complexity_tier, policy_flags) for ka_id in candidates]
        scored.sort(key=lambda item: (-item["score"], item["ka_id"]))

        max_kas = self._budget_limit(input_data)
        selected = scored[:max_kas]
        return {
            "success": True,
            "selected_pipeline": [item["ka_id"] for item in selected],
            "ranked_candidates": scored,
            "metadata": {
                "query_class": query_class,
                "tier": complexity_tier,
                "policy_applied": sorted(policy_flags) or ["default"],
                "max_kas": max_kas,
            },
        }

    def _candidate_pipeline(self, query_class: str, complexity_tier: str, policy_flags: set[str]) -> List[str]:
        tier_mappings = self.config.get("tier_mappings", {})
        base = list(tier_mappings.get(complexity_tier, tier_mappings.get("standard", [])))
        domain = self.QUERY_CLASS_KAS.get(query_class, self.QUERY_CLASS_KAS["GENERAL"])
        if "safety_critical" in policy_flags or complexity_tier == "safety_critical":
            base.extend(tier_mappings.get("safety_critical", []))
            domain.extend(["KA-024", "KA-034", "KA-061"])
        if "local_first" in policy_flags:
            domain.extend(["KA-079", "KA-109"])
        return self._dedupe(base + domain)

    @classmethod
    def _infer_query_class(cls, input_data: KA031Input) -> str:
        explicit = str(input_data.query_class or "GENERAL").upper()
        if explicit != "GENERAL":
            return explicit
        text = f"{input_data.query} {' '.join(input_data.policy_flags)}".lower()
        keyword_map = {
            "COUNTERFACTUAL": ("what if", "counterfactual", "scenario"),
            "SECURITY": ("security", "adversarial", "attack", "auth"),
            "ML": ("model", "training", "evaluation", "hyperparameter"),
            "DATA": ("data", "retrieve", "clean", "schema", "archive"),
            "OPERATIONS": ("cache", "health", "fault", "deploy", "alert"),
            "REASONING": ("why", "hypothesis", "causal", "explain"),
        }
        for query_class, terms in keyword_map.items():
            if any(term in text for term in terms):
                return query_class
        return explicit

    @staticmethod
    def _score_ka(ka_id: str, query_class: str, complexity_tier: str, policy_flags: set[str]) -> Dict[str, Any]:
        score = 0.5
        if ka_id in KA031AlgorithmSelectionEngine.QUERY_CLASS_KAS.get(query_class, []):
            score += 0.3
        if complexity_tier in {"advanced", "deep", "safety_critical"}:
            score += 0.08
        if "safety_critical" in policy_flags and ka_id in {"KA-024", "KA-034", "KA-061", "KA-111"}:
            score += 0.25
        if "local_first" in policy_flags and ka_id in {"KA-079", "KA-109"}:
            score += 0.2
        return {"ka_id": ka_id, "score": round(min(1.0, score), 3), "reasons": {"query_class": query_class, "tier": complexity_tier}}

    def _budget_limit(self, input_data: KA031Input) -> int:
        configured = self.config.get("budget_constraints", {}).get("max_kas_per_pass", 10)
        requested = input_data.budget.get("max_kas") if isinstance(input_data.budget, dict) else None
        try:
            return max(1, min(25, int(requested or configured)))
        except (TypeError, ValueError):
            return int(configured)

    @staticmethod
    def _dedupe(items: List[str]) -> List[str]:
        seen = set()
        return [item for item in items if not (item in seen or seen.add(item))]


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA031AlgorithmSelectionEngine(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-031 Failed: {e}")
        return {"success": False, "error": str(e)}
