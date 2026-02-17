"""
KA-004: Input Validation & Normalization
Purpose: Sanitize, normalize, and validate query and metadata with local rules and SDK delegation.
"""
import logging
import json
import os
import re
from typing import Dict, Any
import importlib
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA004Input(BaseModel):
    query: str = Field(..., description="The input query to validate and normalize")

class KA004InputValidation(KnowledgeAlgorithm):
    """
    KA-004: Performs local pre-validation and normalization before delegating to SDK.
    """
    input_schema = KA004Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-004"
        self.config = self._load_config()
        self.sdk_module = "ukg_sdk.ka.handlers.ka_004"

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_04_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA004Input) -> Dict[str, Any]:
        query = input_data.query
        
        # 1. Local Validation
        local_validation = self._perform_local_validation(query)
        if not local_validation["is_valid"]:
            return {
                "success": True, 
                "is_valid": False,
                "reason": local_validation["reason"],
                "normalized_query": query
            }

        # 2. Local Normalization
        normalized_query = self._perform_local_normalization(query)
        
        # 3. SDK Delegation
        self.log_execution_step("Delegating to SDK for advanced validation", {"query_len": len(normalized_query)})
        sdk_result = self._delegate_to_sdk({"query": normalized_query})
        
        final_query = sdk_result.get("normalized_query", normalized_query)
        final_valid = sdk_result.get("is_valid", True)
        
        return {
            "success": True,
            "is_valid": final_valid,
            "normalized_query": final_query,
            "sdk_response": sdk_result
        }

    def _perform_local_validation(self, query: str) -> Dict[str, Any]:
        if not query:
            return {"is_valid": False, "reason": "Empty query"}
        
        max_len = self.config.get("max_query_length", 2000)
        min_len = self.config.get("min_query_length", 3)
        
        if len(query) > max_len:
            return {"is_valid": False, "reason": f"Query exceeds max length of {max_len}"}
        if len(query) < min_len:
            return {"is_valid": False, "reason": f"Query shorter than min length of {min_len}"}
            
        blacklist = self.config.get("blacklist_patterns", [])
        for pattern in blacklist:
            if pattern.lower() in query.lower():
                return {"is_valid": False, "reason": f"Query contains blacklisted pattern: {pattern}"}
        return {"is_valid": True, "reason": None}

    def _perform_local_normalization(self, query: str) -> str:
        rules = self.config.get("normalization_rules", {})
        processed = query
        if rules.get("strip_html"):
            processed = re.sub(r'<[^>]*>', '', processed)
        if rules.get("trim_whitespace"):
            processed = processed.strip()
        if rules.get("lowercase"):
            processed = processed.lower()
        return processed

    def _delegate_to_sdk(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            mod = importlib.import_module(self.sdk_module)
            if hasattr(mod, "run"):
                return mod.run(data)
            else:
                func = getattr(mod, "ka_004", None) or getattr(mod, "calculate_validation_result", None)
                if func:
                    return func(data)
                return {"is_valid": True, "normalized_query": data.get("query")}
        except Exception as e:
            logger.warning(f"KA-004 SDK fallback triggered: {e}")
            return {"is_valid": True, "normalized_query": data.get("query")}

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA004InputValidation(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-004 Failed: {e}")
        return {"success": False, "error": str(e)}
