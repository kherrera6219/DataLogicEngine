"""
KA-024: Trust Gate
Purpose: Act as a final hard-gate to approve or veto system outputs based on trust and risk metrics.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA024TrustGate(KnowledgeAlgorithm):
    """
    KA-024: Final policy enforcement gate.
    """
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_24_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        confidence = input_data.get("confidence", 0.0)
        risk_score = input_data.get("risk_score", 1.0) # Assume high risk if missing
        
        self.log_execution_step("Enforcing Trust Gate", {"conf": confidence, "risk": risk_score})
        
        trust_threshold = self.config.get("trust_threshold", 0.8)
        risk_tolerance = self.config.get("max_risk_tolerance", 0.5)
        
        reasons = []
        is_approved = True
        
        if confidence < trust_threshold:
            is_approved = False
            reasons.append(f"Confidence {confidence:.2f} below threshold {trust_threshold}")
            
        if risk_score > risk_tolerance:
            is_approved = False
            reasons.append(f"Risk score {risk_score:.2f} exceeds tolerance {risk_tolerance}")
            
        return {
            "ka_id": "KA-024",
            "ka_name": "Trust Gate",
            "success": True,
            "is_approved": is_approved,
            "blocking_reasons": reasons,
            "status": "APPROVED" if is_approved else "VETOED"
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA024TrustGate(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-024 Failed: {e}")
        return {"success": False, "error": str(e)}
