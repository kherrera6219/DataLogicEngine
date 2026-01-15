"""
KA-019: Knowledge Synthesis
Purpose: Merge and unify multiple knowledge fragments and findings into a consistent state.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA019KnowledgeSynthesis(KnowledgeAlgorithm):
    """
    KA-019: Synthesis engine for diverse findings.
    """
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_19_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        findings = input_data.get("findings", [])
        
        self.log_execution_step("Synthesizing Results", {"findingsCount": len(findings)})
        
        # Unify findings by category
        unified_state = {cat: [] for cat in self.config.get("categories", ["FACT", "ASSUMPTION"])}
        
        for f in findings:
            cat = f.get("category", "FACT").upper()
            if cat in unified_state:
                unified_state[cat].append({
                    "content": f.get("content", ""),
                    "confidence": f.get("confidence", 0.5),
                    "source_ka": f.get("source_ka", "unknown")
                })
                
        # Resolve conflicts (highest confidence wins logic)
        for cat in unified_state:
            unified_state[cat] = self._resolve_conflicts(unified_state[cat])
            
        return {
            "ka_id": "KA-019",
            "ka_name": "Knowledge Synthesis",
            "success": True,
            "unified_knowledge": unified_state,
            "summary_points": self._generate_summary(unified_state)
        }

    def _resolve_conflicts(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # This is a stub for sophisticated conflict resolution.
        # Currently, it just keeps everything but sorts by confidence.
        return sorted(items, key=lambda x: x["confidence"], reverse=True)

    def _generate_summary(self, state: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        summary = []
        for cat, items in state.items():
            if items:
                summary.append(f"{cat}: {len(items)} items synthesized.")
        return summary

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA019KnowledgeSynthesis(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-019 Failed: {e}")
        return {"success": False, "error": str(e)}
