"""
KA-013: Persona Weighting
Purpose: Weight persona outputs by relevance/authority.
"""
import logging
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA013PersonaWeighting(KnowledgeAlgorithm):
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate weights for persona outputs.
        """
        persona_results = input_data.get("persona_results", {})
        domain = input_data.get("domain", "general")
        
        self.log_execution_step("Weighting Personas", {"count": len(persona_results)})
        
        weighted_views = {}
        priority_map = {}
        
        for p_type, res in persona_results.items():
            base_weight = 1.0
            # Boost based on domain
            if domain == "legal" and p_type in ["regulatory", "compliance"]:
                base_weight = 1.5
            elif domain == "tech" and p_type in ["sector", "knowledge"]:
                base_weight = 1.2
                
            weighted_views[p_type] = {
                "weight": base_weight,
                "content": res.get("response", "")
            }
            priority_map[p_type] = base_weight
            
        return {
            "ka_id": "KA-013",
            "success": True,
            "weighted_views": weighted_views,
            "priority_map": priority_map
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA013PersonaWeighting(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-013 Failed: {e}")
        return {"success": False, "error": str(e)}
