"""
KA-055: Adaptive Multi-Modal Integration
Purpose: Resolve conflicts and fuse evidence across different modalities (text, image, audio, etc.) using weighted trust models.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

class KA055Input(BaseModel):
    modal_evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Evidence from different modalities to integrate")

class KA055AdaptiveMultiModalIntegration(KnowledgeAlgorithm):
    """
    KA-055: Cross-modal conflict resolution and integration engine using weighted trust models.
    """
    input_schema = KA055Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-055"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_55_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA055Input) -> Dict[str, Any]:
        modal_evidence = input_data.modal_evidence
        self.log_execution_step("Integrating Multi-Modal Evidence", {"modality_count": len(modal_evidence)})
        
        trust_weights = self.config.get("trust_weights", {})
        fused_evidence = []
        disagreements = []
        for i in range(len(modal_evidence)):
            e = modal_evidence[i]
            modality = e.get("modality")
            weight = trust_weights.get(modality, 1.0)
            e_fused = e.copy()
            e_fused["weighted_confidence"] = e.get("confidence", 0.5) * weight
            fused_evidence.append(e_fused)
            for j in range(i+1, len(modal_evidence)):
                 other = modal_evidence[j]
                 if e.get("topic") == other.get("topic") and e.get("verdict") != other.get("verdict"):
                      disagreements.append({
                          "topic": e.get("topic"),
                          "modalities": [modality, other.get("modality")],
                          "clash": f"{e.get('verdict')} vs {other.get('verdict')}"
                      })
                      
        return {
            "success": True,
            "fused_results": fused_evidence,
            "disagreements": disagreements,
            "consensus_reached": len(disagreements) == 0
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA055AdaptiveMultiModalIntegration(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-055 Failed: {e}")
        return {"success": False, "error": str(e)}
