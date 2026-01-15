"""
KA-038: Cross-Modal Synthesis
Purpose: Fuse evidence from multiple modalities (text, tables, image metadata, code) into a unified representation.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA038CrossModalSynthesis(KnowledgeAlgorithm):
    """
    KA-038: Multi-modal evidence fusion engine.
    """
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_38_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        evidence_list = input_data.get("evidence", [])
        
        self.log_execution_step("Fusing Multi-Modal Evidence", {"evidence_count": len(evidence_list)})
        
        fused_content = []
        modalities_present = set()
        
        for item in evidence_list:
             modality = item.get("modality", "text")
             modalities_present.add(modality)
             
             content = item.get("content", "")
             # Simple concatenation-based fusion logic
             fused_content.append(f"[{modality.upper()}]: {content}")
             
        unified_representation = "\n---\n".join(fused_content)
        
        return {
            "ka_id": "KA-038",
            "ka_name": "Cross-Modal Synthesis",
            "success": True,
            "fused_evidence": unified_representation,
            "modalities_processed": list(modalities_present),
            "total_size": len(unified_representation)
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA038CrossModalSynthesis(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-038 Failed: {e}")
        return {"success": False, "error": str(e)}
