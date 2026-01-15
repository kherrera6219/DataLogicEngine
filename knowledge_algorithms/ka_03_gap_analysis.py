"""
KA-003: Gap Analysis
Purpose: Identify discrepancies between current and desired states.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA003GapAnalysis(KnowledgeAlgorithm):
    """
    KA-003: Performs structured Gap Analysis.
    """
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_03_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Gap Analysis.
        Expects 'current_state' (dict) and 'desired_state' (dict).
        """
        current = input_data.get("current_state", {})
        desired = input_data.get("desired_state", {})
        
        self.log_execution_step("Gap Analysis", {"current_keys": list(current.keys())})
        
        gaps = self._find_gaps(current, desired)
        
        # Calculate impact
        impact_score = sum(g["impact"] for g in gaps)
        
        return {
            "ka_id": "KA-003",
            "ka_name": "Gap Analysis",
            "success": True,
            "gaps": gaps,
            "total_impact": impact_score,
            "gap_count": len(gaps)
        }

    def _find_gaps(self, current: Dict[str, Any], desired: Dict[str, Any]) -> List[Dict[str, Any]]:
        gaps = []
        severity = self.config.get("severity_levels", {"high": 0.5})
        
        for key, desired_val in desired.items():
            if key not in current:
                gaps.append({
                    "type": "missing_field",
                    "field": key,
                    "expected": desired_val,
                    "impact": severity.get("high", 0.5)
                })
            elif current[key] != desired_val:
                # Simple equality check, could be enhanced for types
                gaps.append({
                    "type": "value_mismatch",
                    "field": key,
                    "actual": current[key],
                    "expected": desired_val,
                    "impact": severity.get("low", 0.1)
                })
                
        return gaps

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA003GapAnalysis(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-003 Failed: {e}")
        return {"success": False, "error": str(e)}
