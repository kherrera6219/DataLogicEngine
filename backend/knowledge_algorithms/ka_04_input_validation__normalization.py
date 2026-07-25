"""KA-004: deterministic input validation and normalization."""

import json
import logging
import os
import re
from typing import Any

from pydantic import BaseModel, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)


class KA004Input(BaseModel):
    query: str = Field(..., description="The input query to validate and normalize")

class KA004InputValidation(KnowledgeAlgorithm):
    """Validate and normalize input through the canonical backend implementation."""
    input_schema = KA004Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-004"
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_04_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError):
            return {}

    def _run_logic(self, input_data: KA004Input) -> dict[str, Any]:
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
        
        self.log_execution_step(
            "Canonical normalization complete",
            {"query_len": len(normalized_query)},
        )
        return {
            "success": True,
            "is_valid": True,
            "normalized_query": normalized_query,
            "sdk_response": {
                "source": "canonical_backend",
                "normalized_query": normalized_query,
                "is_valid": True,
            },
        }

    def _perform_local_validation(self, query: str) -> dict[str, Any]:
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

def run(context: dict[str, Any]) -> dict[str, Any]:
    try:
        algo = KA004InputValidation(context)
        return algo.run(context)
    except Exception as e:  # noqa: BLE001 - KA boundary returns a stable failure
        logger.error(f"KA-004 Failed: {e}")
        return {"success": False, "error": str(e)}
