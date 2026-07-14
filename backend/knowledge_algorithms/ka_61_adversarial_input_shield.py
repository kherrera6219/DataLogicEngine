"""
KA-061: Adversarial Input Shield
Purpose: Detect and neutralize malicious or adversarial inputs early in the pipeline to protect the knowledge engine.
"""
import logging
import json
import os
import re
from typing import Dict, Any
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA061Input(BaseModel):
    query: str = Field(..., description="The user query or content to scan for adversarial patterns")

class KA061AdversarialInputShield(KnowledgeAlgorithm):
    """
    KA-061: Input sanitation and threat detection engine for neutralizing malicious queries.
    """
    input_schema = KA061Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-061"
        self.config = self._load_config()

    def _default_config(self) -> Dict[str, Any]:
        return {
            "block_patterns": [r"(?i)DROP\s+TABLE", r"(?i)DELETE\s+FROM", r"(?i)<script>"],
            "enable_veto_on_threat": True,
        }

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_61_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    loaded = json.load(f) or {}
                    defaults = self._default_config()
                    configured_patterns = loaded.get("block_patterns") or []
                    return {
                        **defaults,
                        **loaded,
                        "block_patterns": list(
                            dict.fromkeys(defaults["block_patterns"] + configured_patterns)
                        ),
                    }
            return self._default_config()
        except Exception:
            return self._default_config()

    def _run_logic(self, input_data: KA061Input) -> Dict[str, Any]:
        query = input_data.query
        self.log_execution_step("Scanning for Adversarial Patterns", {"query_len": len(query)})
        
        threats_detected = []
        block_patterns = self.config.get("block_patterns", [r"(?i)DROP\s+TABLE", r"(?i)DELETE\s+FROM", r"(?i)<script>"])
        for pattern in block_patterns:
             if re.search(pattern, query, re.IGNORECASE):
                  threats_detected.append({
                      "pattern": pattern,
                      "type": "MALICIOUS_SNIPPET"
                  })
                  
        is_blocked = len(threats_detected) > 0 and self.config.get("enable_veto_on_threat", True)
        return {
            "success": True,
            "blocked": is_blocked,
            "threats": threats_detected,
            "sanitized_query": query if not is_blocked else "[FILTERED]",
            "veto": is_blocked
        }

    def _fallback_logic(self, input_data: KA061Input, error: Exception) -> Dict[str, Any]:
        """Failsafe: Block the input if the scan fails."""
        self.logger.warning(f"Resilience Fallback for KA-061: {str(error)}")
        return {
            "success": False,
            "blocked": True,
            "threats": [{"type": "SCAN_FAILURE_VETO"}],
            "sanitized_query": "[FILTERED_BY_FAILSAFE]",
            "veto": True
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    # Base class .run() handles registry invocation and error wrapping
    algo = KA061AdversarialInputShield(context)
    return algo.run(context)
