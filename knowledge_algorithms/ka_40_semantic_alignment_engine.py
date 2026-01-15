"""
KA-040: Semantic Alignment Engine
Purpose: Align overlapping concepts, synonyms, and prevent ontological fragmentation by suggesting merges.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA040SemanticAlignmentEngine(KnowledgeAlgorithm):
    """
    KA-040: Concept alignment and synonym resolution engine.
    """
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_40_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        concepts = input_data.get("concepts", []) # e.g. ["User Profile", "Member Account"]
        
        self.log_execution_step("Aligning Concepts", {"concept_count": len(concepts)})
        
        alignments = []
        # 1. Simple Keyword Jaccard/Overlap analysis (Stub logic)
        for i in range(len(concepts)):
            for j in range(i + 1, len(concepts)):
                c1 = concepts[i]
                c2 = concepts[j]
                
                # If they share words, suggest alignment
                words1 = set(c1.lower().split())
                words2 = set(c2.lower().split())
                intersection = words1.intersection(words2)
                
                if intersection:
                    score = len(intersection) / max(len(words1), len(words2))
                    if score >= self.config.get("alignment_threshold", 0.6):
                        alignments.append({
                            "source": c1,
                            "target": c2,
                            "match_score": score,
                            "reason": f"Shared keywords: {list(intersection)}"
                        })
                        
        return {
            "ka_id": "KA-040",
            "ka_name": "Semantic Alignment Engine",
            "success": True,
            "alignment_suggestions": alignments,
            "auto_merged": False # Based on config
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA040SemanticAlignmentEngine(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-040 Failed: {e}")
        return {"success": False, "error": str(e)}
