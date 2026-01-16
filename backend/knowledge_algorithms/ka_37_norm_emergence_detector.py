"""
KA-037: Norm Emergence Detector
Purpose: Detect groupthink, unhealthy convergence, or forced consensus in multi-agent and persona outputs.
"""
import logging
import json
import os
import statistics
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

class KA037Input(BaseModel):
    persona_results: List[Dict[str, Any]] = Field(default_factory=list, description="A list of persona results to analyze for convergence")

class KA037NormEmergenceDetector(KnowledgeAlgorithm):
    """
    KA-037: Groupthink and unhealthy convergence detection engine.
    """
    input_schema = KA037Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-037"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_37_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA037Input) -> Dict[str, Any]:
        persona_results = input_data.persona_results
        self.log_execution_step("Analyzing Convergence", {"perspective_count": len(persona_results)})
        
        if len(persona_results) < self.config.get("min_perspectives", 3):
            return {"success": True, "msg": "Insufficient data for norm analysis"}
            
        confidences = [p.get("confidence", 0.0) for p in persona_results]
        variance = statistics.variance(confidences) if len(confidences) > 1 else 0.0
        avg_conf = statistics.mean(confidences)
        is_converged = avg_conf > self.config.get("convergence_threshold", 0.8) and variance < 0.01
        
        return {
            "success": True,
            "convergence_metrics": {
                "average_confidence": avg_conf,
                "confidence_variance": variance,
                "is_dangerously_converged": is_converged
            },
            "status": "DIVERSE" if not is_converged else "UNHEALTHY_CONVERGENCE"
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA037NormEmergenceDetector(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-037 Failed: {e}")
        return {"success": False, "error": str(e)}
