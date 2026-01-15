"""
KA-047: Meta-Algorithm Selection
Purpose: Select or tune the Knowledge Algorithm pipeline dynamically based on performance signatures and history.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

class KA047Input(BaseModel):
    performance_history: List[Dict[str, Any]] = Field(default_factory=list, description="Performance metrics history for the pipeline")
    pipeline: List[str] = Field(default_factory=list, description="The current active pipeline of KA IDs")

class KA047MetaAlgorithmSelection(KnowledgeAlgorithm):
    """
    KA-047: Dynamic pipeline meta-selection and tuning engine.
    """
    input_schema = KA047Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-047"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_47_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA047Input) -> Dict[str, Any]:
        performance_history = input_data.performance_history
        current_pipeline = input_data.pipeline
        self.log_execution_step("Tuning Pipeline Meta-Parameters", {"history_len": len(performance_history)})
        
        avg_accuracy = sum(h.get("accuracy", 0.0) for h in performance_history) / max(len(performance_history), 1)
        suggested_pipeline = current_pipeline.copy()
        optimization_applied = False
        if avg_accuracy < self.config.get("min_accuracy_threshold", 0.8):
            if "KA-014" not in suggested_pipeline:
                 suggested_pipeline.append("KA-014")
                 optimization_applied = True
                 
        return {
            "success": True,
            "original_pipeline": current_pipeline,
            "optimized_pipeline": suggested_pipeline,
            "modifications_made": optimization_applied,
            "meta_status": "TUNED" if optimization_applied else "STABLE"
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA047MetaAlgorithmSelection(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-047 Failed: {e}")
        return {"success": False, "error": str(e)}
