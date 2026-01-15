"""
L9-KA-003: Persona Agreement Auditor

Audits persona agreement matrix for:
- Silent dissent (experts who disagree but were overruled)
- Below-threshold satisfaction
- Unresolved concerns
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class PersonaAgreementAuditorKA:
    """KA for auditing persona agreement."""
    
    KA_ID = "L9-KA-003"
    NAME = "Persona Agreement Auditor"
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.default_threshold = self.config.get("default_threshold", 0.95)
    
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Audit persona agreement for silent dissent.
        
        Args:
            inputs: {"domain_confidences": List[Dict]}
            
        Returns:
            {"min_score": float, "flagged": List[Dict], "consensus": bool}
        """
        domain_confs = inputs.get("domain_confidences", [])
        threshold = inputs.get("threshold", self.default_threshold)
        
        min_score = 1.0
        flagged = []
        
        for dc in domain_confs:
            if isinstance(dc, dict):
                confidence = dc.get("confidence", 1.0)
                domain = dc.get("domain", "unknown")
                
                if confidence < min_score:
                    min_score = confidence
                
                if confidence < threshold:
                    flagged.append({
                        "persona": domain,
                        "score": confidence,
                        "gap": threshold - confidence,
                        "concern": f"Below threshold by {(threshold - confidence)*100:.1f}%"
                    })
        
        consensus = len(flagged) == 0
        
        logger.info(f"L9-KA-003: Min score {min_score:.3f}, {len(flagged)} flagged, consensus={consensus}")
        
        return {
            "min_score": min_score,
            "flagged": flagged,
            "consensus": consensus,
            "threshold_applied": threshold
        }
