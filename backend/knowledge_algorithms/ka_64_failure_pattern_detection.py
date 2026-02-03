"""
KA-064: Failure Pattern Detection
Purpose: Identify recurring failure signatures and error patterns in the execution logs to trigger proactive alerts or mitigation.
"""
import logging
import json
import os
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)


class KA064Input(BaseModel):
    class Config:
        extra = 'allow'
class KA064FailurePatternDetection(KnowledgeAlgorithm):
    input_schema = KA064Input
    """
    KA-064: Error signature matching and pattern analysis engine.
    """
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_64_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA064Input) -> Dict[str, Any]:
        input_dict = input_data.model_dump()
        error_logs = input_dict.get("error_logs", [])
        
        self.log_execution_step("Scanning for Failure Patterns", {"log_count": len(error_logs)})
        
        signatures = self.config.get("signature_db", [])
        detected_patterns = {}
        
        for log in error_logs:
             msg = log.get("message", "")
             for sig in signatures:
                  if re.search(sig["regex"], msg, re.IGNORECASE):
                       tag = sig["tag"]
                       detected_patterns[tag] = detected_patterns.get(tag, 0) + 1
                       
        # Filter by min occurrence
        threshold = self.config.get("min_occurrence_count", 3)
        significant_failures = {k: v for k, v in detected_patterns.items() if v >= threshold}
        
        return {
            "ka_id": "KA-064",
            "ka_name": "Failure Pattern Detection",
            "success": True,
            "detected_signatures": significant_failures,
            "alert_triggered": len(significant_failures) > 0
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA064FailurePatternDetection(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-064 Failed: {e}")
        return {"success": False, "error": str(e)}
