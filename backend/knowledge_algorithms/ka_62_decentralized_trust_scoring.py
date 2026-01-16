"""
KA-062: Decentralized Trust Scoring
Purpose: Compute a robust trust score for knowledge fragments based on their provenance hashes and source credibility.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

from core.knowledge_algorithm.exceptions import KAError, KAConfigError

class KA062Input(BaseModel):
    evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Evidence fragments to evaluate for trust and credibility")

class KA062DecentralizedTrustScoring(KnowledgeAlgorithm):
    """
    KA-062: Provenance-based trust calculation engine for knowledge fragments.
    """
    input_schema = KA062Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-062"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_62_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA062Input) -> Dict[str, Any]:
        evidence_nodes = input_data.evidence
        self.log_execution_step("Computing Trust Scores", {"evidence_count": len(evidence_nodes)})
        
        if not self.config:
            raise KAConfigError("Decentralized Trust configuration missing", details={"path": "config/ka_62_config.json"})

        provenance_weights = self.config.get("provenance_weights", {})
        trust_reports = []
        min_trust = self.config.get("min_trust_for_commitment", 0.7)
        
        for e in evidence_nodes:
             source = e.get("source", "unknown")
             weight = provenance_weights.get(source, 1.0)
             trust_score = weight * 0.8
             trust_reports.append({
                 "source": source,
                 "final_score": min(1.0, trust_score),
                 "status": "TRUSTED" if trust_score >= min_trust else "UNTRUSTED"
             })
             
        return {
            "success": True,
            "reports": trust_reports,
            "average_trust": sum(r["final_score"] for r in trust_reports) / max(1, len(trust_reports))
        }

    def _fallback_logic(self, input_data: KA062Input, error: Exception) -> Dict[str, Any]:
        """Failsafe: Return zero trust for all evidence if calculation fails."""
        self.logger.warning(f"Resilience Fallback for KA-062: {str(error)}")
        return {
            "success": False,
            "reports": [],
            "average_trust": 0.0,
            "fallback_engaged": True,
            "message": "Trust scoring failed. Defaulting to zero trust for all fragments."
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    algo = KA062DecentralizedTrustScoring(context)
    return algo.run(context)
