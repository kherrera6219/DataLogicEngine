"""
KA-041: Concept Confidence Normalization
Purpose: Normalize confidence scales across different domains and sources to ensure comparability.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA041ConceptConfidenceNormalization(KnowledgeAlgorithm):
    """
    KA-041: Scale normalization and cross-domain confidence calibration.
    """
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_41_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        findings = input_data.get("findings", [])
        
        self.log_execution_step("Normalizing Confidence Scales", {"finding_count": len(findings)})
        
        domain_scaling = self.config.get("domain_scaling", {})
        bounds = self.config.get("global_bounds", [0.0, 1.0])
        
        normalized_findings = []
        for f in findings:
            raw_conf = f.get("confidence", 0.5)
            domain = f.get("domain", "general")
            
            # Apply domain-specific scaling/calibration
            scale = domain_scaling.get(domain, 1.0)
            calibrated_conf = raw_conf * scale
            
            # Clip to global bounds
            if self.config.get("clip_outputs", True):
                calibrated_conf = max(bounds[0], min(bounds[1], calibrated_conf))
                
            f_copy = f.copy()
            f_copy["confidence"] = calibrated_conf
            f_copy["metadata"] = f_copy.get("metadata", {})
            f_copy["metadata"]["original_confidence"] = raw_conf
            normalized_findings.append(f_copy)
            
        return {
            "ka_id": "KA-041",
            "ka_name": "Concept Confidence Normalization",
            "success": True,
            "normalized_findings": normalized_findings,
            "count": len(normalized_findings)
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA041ConceptConfidenceNormalization(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-041 Failed: {e}")
        return {"success": False, "error": str(e)}
