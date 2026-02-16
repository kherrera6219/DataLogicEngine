"""
KA-058: Interactive Clarification & Learning
Purpose: Decide when the system has insufficient information or high ambiguity and must ask the user for clarification.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field

class KA058Input(BaseModel):
    ambiguity_metrics: Dict[str, Any] = Field(default_factory=dict, description="Ambiguity and entropy metrics for the current query")
    competing_intents: List[Dict[str, Any]] = Field(default_factory=list, description="A list of competing intent interpretations")

class KA058InteractiveClarificationLearning(KnowledgeAlgorithm):
    """
    KA-058: Ambiguity detection and follow-up generation engine for active learning.
    """
    input_schema = KA058Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-058"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_58_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA058Input) -> Dict[str, Any]:
        ambiguity_metrics = input_data.ambiguity_metrics
        competing_intents = input_data.competing_intents
        self.log_execution_step("Evaluating Need for Clarification", {"intent_count": len(competing_intents)})
        
        threshold = self.config.get("ambiguity_threshold", 0.6)
        should_clarify = False
        questions = []
        if len(competing_intents) > 1:
             score1 = competing_intents[0].get("score", 0.0)
             score2 = competing_intents[1].get("score", 0.0)
             if (score1 - score2) < (1 - threshold):
                  should_clarify = True
                  questions.append(f"I found two likely interpretations: '{competing_intents[0].get('name')}' and '{competing_intents[1].get('name')}'. Which one should I prioritize?")
        if ambiguity_metrics.get("overall_entropy", 0.0) > threshold:
             should_clarify = True
             if not questions:
                  questions.append("Your request has some ambiguity. Could you please provide more context regarding the target objective?")
                  
        return {
            "success": True,
            "clarification_required": should_clarify,
            "suggested_questions": questions[:self.config.get("max_clarifications_per_turn", 2)],
            "options_provided": self.config.get("suggest_options", True)
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA058InteractiveClarificationLearning(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-058 Failed: {e}")
        return {"success": False, "error": str(e)}
