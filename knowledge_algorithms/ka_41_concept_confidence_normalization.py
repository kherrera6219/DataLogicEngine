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

from pydantic import BaseModel, Field
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

class KA041Input(BaseModel):
    findings: List[Dict[str, Any]] = Field(default_factory=list, description="Findings with raw confidence to normalize")

class KA041ConceptConfidenceNormalization(KnowledgeAlgorithm):
    """
    KA-041: Scale normalization and cross-domain confidence calibration engine.
    """
    input_schema = KA041Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-041"
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

    def _run_logic(self, input_data: KA041Input) -> Dict[str, Any]:
        findings = input_data.findings
        self.log_execution_step("Normalizing Confidence Scales", {"finding_count": len(findings)})
        
        domain_scaling = self.config.get("domain_scaling", {})
        bounds = self.config.get("global_bounds", [0.0, 1.0])
        clip_outputs = self.config.get("clip_outputs", True)
        
        normalized_findings = []
        for f in findings:
            raw_conf = f.get("confidence", 0.5)
            domain = f.get("domain", "general")
            scale = domain_scaling.get(domain, 1.0)
            calibrated_conf = raw_conf * scale
            if clip_outputs:
                calibrated_conf = max(bounds[0], min(bounds[1], calibrated_conf))
            
            f_copy = f.copy()
            f_copy["confidence"] = calibrated_conf
            f_copy["metadata"] = f_copy.get("metadata", {})
            f_copy["metadata"]["original_confidence"] = raw_conf
            normalized_findings.append(f_copy)
            
        return {
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
