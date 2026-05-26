import logging
import json
import os
from typing import Dict, Any
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class KA116Input(BaseModel):
    content: str = ""
    claims: list = []

class KA116EntropyDetection(KnowledgeAlgorithm):
    """
    KA-116: System decay and knowledge entropy detection engine.
    """
    input_schema = KA116Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-116"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_116_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA116Input) -> Dict[str, Any]:
        self.log_execution_step("Measuring System Entropy", {})

        from backend.knowledge_algorithms.l10.l10_ka_001_entropy_scorer import run as entropy_run

        payload = input_data.model_dump()
        if not payload.get("content") and payload.get("claims"):
            payload["content"] = " ".join(str(claim) for claim in payload["claims"])
        entropy_result = entropy_run(payload)
        entropy_score = entropy_result.get("entropy_score", 0.0)
        threshold = self.config.get("entropy_threshold", 0.5)
        
        return {
            "success": True,
            "entropy_score": entropy_score,
            "state": "STABLE" if entropy_score < threshold else "CRITICAL",
            "reconciliation_triggered": entropy_score >= threshold and self.config.get("trigger_reconciliation", False)
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA116EntropyDetection(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-116 Failed: {e}")
        return {"success": False, "error": str(e)}
