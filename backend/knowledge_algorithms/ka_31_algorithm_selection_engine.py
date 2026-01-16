"""
KA-031: Algorithm Selection Engine
Purpose: Select the optimal sequence of Knowledge Algorithms (KA pipeline) given a query class, complexity tier, and policy constraints.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

class KA031Input(BaseModel):
    query_class: str = Field("GENERAL", description="The classification of the query")
    complexity_tier: str = Field("standard", description="The complexity tier (standard, deep, safety_critical)")
    policy_flags: List[str] = Field(default_factory=list, description="Optional policy flags affecting selection")

class KA031AlgorithmSelectionEngine(KnowledgeAlgorithm):
    """
    KA-031: Optimal KA pipeline selection engine based on query class and complexity.
    """
    input_schema = KA031Input

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
        query_class = input_data.query_class
        complexity_tier = input_data.complexity_tier
        policy_flags = input_data.policy_flags
        
        self.log_execution_step("Selecting KA Pipeline", {"query_class": query_class, "tier": complexity_tier})
        
        tier_mappings = self.config.get("tier_mappings", {})
        pipeline = tier_mappings.get(complexity_tier, tier_mappings.get("standard", []))
        if "safety_critical" in policy_flags:
            pipeline = tier_mappings.get("safety_critical", pipeline)
            
        max_kas = self.config.get("budget_constraints", {}).get("max_kas_per_pass", 10)
        final_pipeline = pipeline[:max_kas]
        
        return {
            "success": True,
            "selected_pipeline": final_pipeline,
            "metadata": {
                "tier": complexity_tier,
                "policy_applied": "high_safety" if "safety_critical" in policy_flags else "default"
            }
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA031AlgorithmSelectionEngine(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-031 Failed: {e}")
        return {"success": False, "error": str(e)}
