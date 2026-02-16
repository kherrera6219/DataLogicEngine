"""
KA-051: Self-Correcting Knowledge Distillation
Purpose: Distill high-confidence outcomes and validated traces into reusable rules and abstractions.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field

class KA051Input(BaseModel):
    traces: List[Dict[str, Any]] = Field(default_factory=list, description="Execution traces to distill into stable rules")

class KA051SelfCorrectingKnowledgeDistillation(KnowledgeAlgorithm):
    """
    KA-051: Learning engine that distills stable rules and abstractions from successful execution traces.
    """
    input_schema = KA051Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-051"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_51_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA051Input) -> Dict[str, Any]:
        traces = input_data.traces
        self.log_execution_step("Distilling Rules from Traces", {"trace_count": len(traces)})
        
        distilled_rules = []
        threshold = self.config.get("distillation_threshold", 0.9)
        for trace in traces:
            confidence = trace.get("confidence", 0.0)
            if confidence >= threshold:
                distilled_rules.append({
                    "rule_id": f"RULE-{trace.get('id', 'UNK')}",
                    "abstraction": f"Pattern: {trace.get('pattern_name')} -> Success",
                    "confidence": confidence,
                    "source_trace": trace.get("id")
                })
                
        max_rules = self.config.get("max_rules_per_session", 5)
        distilled_rules = distilled_rules[:max_rules]
        return {
            "success": True,
            "new_distilled_rules": distilled_rules,
            "count": len(distilled_rules)
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA051SelfCorrectingKnowledgeDistillation(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-051 Failed: {e}")
        return {"success": False, "error": str(e)}
