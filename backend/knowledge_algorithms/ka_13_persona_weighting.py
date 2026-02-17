"""
KA-013: Persona Weighting
Purpose: Weigh various persona perspectives based on query domain and persona authority.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA013Input(BaseModel):
    persona_results: List[Dict[str, Any]] = Field(default_factory=list, description="The results from persona simulations")
    domain: str = Field("GENERAL", description="The query domain for weighting")

class KA013PersonaWeighting(KnowledgeAlgorithm):
    """
    KA-013: Normalizes and weights persona findings based on domain authority.
    """
    input_schema = KA013Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-013"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_13_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA013Input) -> Dict[str, Any]:
        persona_results = input_data.persona_results
        domain = input_data.domain
        
        self.log_execution_step("Persona Weighting", {"domain": domain, "personasCount": len(persona_results)})
        
        weights = self.config.get("domain_weights", {}).get(domain, self.config.get("domain_weights", {}).get("GENERAL", {}))
        
        weighted_results = []
        total_weighted_confidence = 0.0
        active_weights_sum = 0.0
        
        for res in persona_results:
            p_type = res.get("persona_type")
            weight = weights.get(p_type, 0.25)
            w_conf = res.get("confidence", 0.8) * weight
            
            weighted_results.append({
                **res,
                "applied_weight": weight,
                "weighted_confidence": w_conf
            })
            total_weighted_confidence += w_conf
            active_weights_sum += weight
            
        final_confidence = total_weighted_confidence / active_weights_sum if active_weights_sum > 0 else 0.0
        
        return {
            "success": True,
            "domain": domain,
            "weighted_results": weighted_results,
            "final_consensus_confidence": final_confidence
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA013PersonaWeighting(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-013 Failed: {e}")
        return {"success": False, "error": str(e)}
