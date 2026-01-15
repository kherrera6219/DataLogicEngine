"""
KA-026: Contradiction Detection
Purpose: Detect logical conflicts, semantic negations, and stance clashes across diverse findings.
"""
import logging
import json
import os
import re
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA026ContradictionDetection(KnowledgeAlgorithm):
    """
    KA-026: Conflict and contradiction detection engine.
    """
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_26_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        findings = input_data.get("findings", [])
        
        self.log_execution_step("Scanning for Contradictions", {"finding_count": len(findings)})
        
        conflicts = []
        
        # 1. Semantic Negation Detection (Rule-based stub)
        # Compare every finding against every other finding
        for i in range(len(findings)):
            for j in range(i + 1, len(findings)):
                f1 = findings[i]
                f2 = findings[j]
                
                conflict = self._detect_conflict(f1, f2)
                if conflict:
                    conflicts.append(conflict)
                    
        return {
            "ka_id": "KA-026",
            "ka_name": "Contradiction Detection",
            "success": True,
            "has_contradictions": len(conflicts) > 0,
            "conflicts": conflicts,
            "severity_score": sum(c.get("severity", 0) for c in conflicts) / max(len(conflicts), 1) if conflicts else 0.0
        }

    def _detect_conflict(self, f1: Dict[str, Any], f2: Dict[str, Any]) -> Dict[str, Any]:
        # Simple string-based negation check
        t1 = f1.get("content", "").lower()
        t2 = f2.get("content", "").lower()
        
        # Remove common words to find core subject
        # If t2 is basically 'not' + t1
        if f"not {t1}" in t2 or f"no {t1}" in t2 or f"never {t1}" in t2:
             return {
                 "type": "DIRECT_NEGATION",
                 "f1_id": f1.get("id"),
                 "f2_id": f2.get("id"),
                 "severity": 1.0,
                 "description": f"Finding 2 negates Finding 1: {t2} vs {t1}"
             }
             
        # Cross-persona stance clash (stub)
        if f1.get("persona") and f2.get("persona"):
            if f1.get("persona") != f2.get("persona") and f1.get("subject") == f2.get("subject"):
                 # Different personas saying different things about the same subject
                 if t1 != t2:
                      return {
                          "type": "STANCE_CLASH",
                          "f1_id": f1.get("id"),
                          "f2_id": f2.get("id"),
                          "severity": 0.5,
                          "description": "Stakeholder perspective clash detected."
                      }
                      
        return None

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA026ContradictionDetection(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-026 Failed: {e}")
        return {"success": False, "error": str(e)}
