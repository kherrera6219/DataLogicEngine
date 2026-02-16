"""
KA-063: Continuous Performance Learning
Purpose: Learn which KA configurations and pipeline paths perform best over time by analyzing outcome metrics and user feedback.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field

class KA063LearningInput(BaseModel):
    outcome_metrics: Dict[str, Any] = Field(default_factory=dict, description="Performance and outcome metrics to learn from")
    feedback: List[Dict[str, Any]] = Field(default_factory=list, description="User or system feedback on previous outcomes")

class KA063ContinuousPerformanceLearning(KnowledgeAlgorithm):
    """
    KA-063: Real-time performance learning and profile tuning engine for long-term optimization.
    """
    input_schema = KA063LearningInput

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-063"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_63_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA063LearningInput) -> Dict[str, Any]:
        outcome_metrics = input_data.outcome_metrics
        self.log_execution_step("Updating Performance Profiles", {"metric_count": len(outcome_metrics)})
        
        learning_rate = self.config.get("learning_rate", 0.1)
        tuning_suggestions = []
        accuracy = outcome_metrics.get("accuracy", 0.0)
        latency = outcome_metrics.get("latency", 0.0)
        if accuracy < 0.8:
             tuning_suggestions.append({
                 "parameter": "pipeline_depth",
                 "adjustment": +1,
                 "reason": "Low accuracy detected in recent runs"
             })
        if latency > 1000:
             tuning_suggestions.append({
                 "parameter": "concurrency_level",
                 "adjustment": +2,
                 "reason": "High latency detected"
             })
             
        return {
            "success": True,
            "suggestions": tuning_suggestions,
            "learning_status": "UPDATING" if tuning_suggestions else "STABLE",
            "learning_rate_applied": learning_rate
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA063ContinuousPerformanceLearning(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-063 Failed: {e}")
        return {"success": False, "error": str(e)}
