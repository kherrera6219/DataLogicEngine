"""
KA-056: Narrative Explainability Engine
Purpose: Generate audience-safe, natural language explanations and rationale maps from complex execution traces and decision logs.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA056NarrativeExplainabilityEngine(KnowledgeAlgorithm):
    """
    KA-056: Explainability and rationale generation engine.
    """
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_56_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        trace_dag = input_data.get("trace_dag", {})
        decision_log = input_data.get("decision_log", [])
        
        self.log_execution_step("Generating Decision Rationale", {"decision_count": len(decision_log)})
        
        explanations = []
        # 1. Map decisions to human-readable rationales (Stub)
        for d in decision_log:
             explanations.append({
                 "step": d.get("step_id"),
                 "action": d.get("action"),
                 "rationale": f"Action taken because {d.get('reason_code', 'DEFAULT_LOGIC')} was triggered with confidence {d.get('confidence', 0.5)}.",
                 "pivot_point": d.get("is_pivot", False)
             })
             
        summary = f"Processed {len(decision_log)} decision nodes. High-level path: {trace_dag.get('summary_path', 'N/A')}"
        
        return {
            "ka_id": "KA-056",
            "ka_name": "Narrative Explainability Engine",
            "success": True,
            "narrative_summary": summary,
            "step_by_step_rationale": explanations,
            "audience_vibe": self.config.get("audience_vibe", "professional")
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA056NarrativeExplainabilityEngine(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-056 Failed: {e}")
        return {"success": False, "error": str(e)}
