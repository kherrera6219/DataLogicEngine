"""
KA-005: Query Classification
Purpose: Identify query intent and domain using local rules and SDK delegation.
"""
import logging
import json
import os
from typing import Dict, Any, List, Tuple
import importlib
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA005QueryClassification(KnowledgeAlgorithm):
    """
    KA-005: Classifies queries into logical categories.
    """
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.config = self._load_config()
        self.sdk_module = "ukg_sdk.ka.handlers.ka_005"

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_05_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load KA-05 config: {e}")
            return {}

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        query = input_data.get("query", "")
        
        # 1. Local Rule-based Classification
        local_category, local_conf = self._perform_local_classification(query)
        
        # 2. SDK Delegation (for refined classification)
        self.log_execution_step("Delegating to SDK for refined classification", {"query": query})
        sdk_result = self._delegate_to_sdk(input_data)
        
        # 3. Conflict Resolution / Merging
        # Prefer SDK if it has higher confidence or is more specific
        final_category = sdk_result.get("category", local_category)
        final_conf = sdk_result.get("confidence", local_conf)
        
        # Ensure final result follows enterprise structure
        return {
            "ka_id": "KA-005",
            "ka_name": "Query Classification",
            "success": True,
            "category": final_category,
            "confidence": final_conf,
            "metadata": {
                "local_guess": local_category,
                "sdk_response": sdk_result
            }
        }

    def _perform_local_classification(self, query: str) -> Tuple[str, float]:
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

    def _delegate_to_sdk(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            mod = importlib.import_module(self.sdk_module)
            if hasattr(mod, "run"):
                return mod.run(data)
            else:
                func = getattr(mod, "ka_005", None) or getattr(mod, "classify", None)
                if func:
                    return func(data)
                return {}
        except Exception as e:
            logger.warning(f"KA-005 SDK fallback: {e}")
            return {}

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA005QueryClassification(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-005 Failed: {e}")
        return {"success": False, "error": str(e)}
