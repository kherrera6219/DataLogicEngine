"""
KA-065: Knowledge Regression Tester
Purpose: Ensure that updates to the knowledge base do not break or contradict prior established high-confidence knowledge.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

class KA065RegressionInput(BaseModel):
    snapshot: Dict[str, Any] = Field(default_factory=dict, description="The current knowledge base snapshot to test")
    baseline: Dict[str, Any] = Field(default_factory=dict, description="Baseline established knowledge to compare against")

class KA065KnowledgeRegressionTester(KnowledgeAlgorithm):
    """
    KA-065: Knowledge regression and consistency testing engine to prevent stability violations.
    """
    input_schema = KA065RegressionInput

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-065"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_65_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA065RegressionInput) -> Dict[str, Any]:
        kb_snapshot = input_data.snapshot
        baseline_knowledge = input_data.baseline
        self.log_execution_step("Running Knowledge Regression Tests", {"baseline_size": len(baseline_knowledge)})
        
        failures = []
        for node_id, baseline_val in baseline_knowledge.items():
             current_val = kb_snapshot.get("nodes", {}).get(node_id)
             if current_val and current_val != baseline_val:
                  failures.append({
                      "node_id": node_id,
                      "baseline": baseline_val,
                      "current": current_val,
                      "type": "STABILITY_VIOLATION"
                  })
                  
        status = "PASSED" if not failures else "FAILED"
        return {
            "success": True,
            "status": status,
            "failure_count": len(failures),
            "regression_report": failures,
            "veto": status == "FAILED" and self.config.get("strict_mode", True)
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA065KnowledgeRegressionTester(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-065 Failed: {e}")
        return {"success": False, "error": str(e)}
