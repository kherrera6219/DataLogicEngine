"""KA-005: deterministic local query intent and domain classification."""
import json
import logging
import os
from typing import Any

from pydantic import BaseModel, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)


class KA005Input(BaseModel):
    query: str = Field(..., description="The query to classify")

class KA005QueryClassification(KnowledgeAlgorithm):
    """
    KA-005: Classifies queries into logical categories.
    """
    input_schema = KA005Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-005"
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_05_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError):
            return {}

    def _run_logic(self, input_data: KA005Input) -> dict[str, Any]:
        query = input_data.query
        
        # 1. Local Rule-based Classification
        local_category, local_conf = self._perform_local_classification(query)
        
        # Provider calls from inside a KA would recursively enter the governed
        # pipeline and make the call budget untraceable. Phase 5 keeps this KA
        # deterministic; a future validator may request an explicitly budgeted
        # refinement at the canonical orchestrator boundary.
        sdk_result: dict[str, Any] = {}
        
        final_category = sdk_result.get("category", local_category)
        final_conf = sdk_result.get("confidence", local_conf)
        suggested_tier = self._tier_for_category(final_category)

        return {
            "success": True,
            "category": final_category,
            "confidence": final_conf,
            # Workflow tier derived from the classification category. Consumed by
            # TruthCore.determine_tier (which reads `suggested_tier`); previously
            # this KA only returned a category, so that branch always fell through
            # to the heuristic. Config-overridable via "category_tier_map".
            "suggested_tier": suggested_tier,
            "tier": suggested_tier,
            "metadata": {
                "local_guess": local_category,
                "sdk_response": sdk_result
            }
        }

    def _tier_for_category(self, category: str) -> str:
        """Map a classification category to a TruthCore workflow tier."""
        default_map = {
            "REGULATORY": "high_stakes",
            "TECHNICAL": "moderate",
            "RESEARCH": "moderate",
            "GENERAL": "trivial",
        }
        tier_map = {k.upper(): v for k, v in self.config.get("category_tier_map", default_map).items()}
        return tier_map.get(str(category).upper(), "moderate")

    def _perform_local_classification(self, query: str) -> tuple[str, float]:
        if not query:
            return "GENERAL", 0.0
            
        categories = self.config.get("categories", {})
        query_lower = query.lower()
        
        best_cat = self.config.get("fallback_category", "GENERAL")
        best_conf = categories.get(best_cat, {}).get("default_confidence", 0.5)
        
        for cat_name, info in categories.items():
            keywords = info.get("keywords", [])
            for kw in keywords:
                if kw in query_lower:
                    return cat_name, info.get("default_confidence", 0.8)
        return best_cat, best_conf

    async def _delegate_to_sdk_async(self, data: dict[str, Any]) -> dict[str, Any]:
        """Compatibility shim; recursive provider delegation is disabled."""
        return {}

    def _delegate_to_sdk(self, data: dict[str, Any]) -> dict[str, Any]:
        """Compatibility shim; classification is intentionally local."""
        return {}

def run(context: dict[str, Any]) -> dict[str, Any]:
    try:
        algo = KA005QueryClassification(context)
        return algo.run(context)
    except Exception as e:  # noqa: BLE001 - KA boundary returns a stable failure
        logger.error(f"KA-005 Failed: {e}")
        return {"success": False, "error": str(e)}
