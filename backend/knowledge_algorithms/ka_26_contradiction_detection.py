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

from pydantic import BaseModel, Field

class KA026Input(BaseModel):
    findings: List[Dict[str, Any]] = Field(default_factory=list, description="Findings to scan for contradictions")

class KA026ContradictionDetection(KnowledgeAlgorithm):
    """
    KA-026: Conflict and contradiction detection engine for multi-persona reasoning.
    """
    input_schema = KA026Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-026"
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

    def _run_logic(self, input_data: KA026Input) -> Dict[str, Any]:
        findings = input_data.findings
        self.log_execution_step("Scanning for Contradictions", {"finding_count": len(findings)})
        
        conflicts = []
        for i in range(len(findings)):
            for j in range(i + 1, len(findings)):
                conflict = self._detect_conflict(findings[i], findings[j])
                if conflict:
                    conflicts.append(conflict)
                    
        return {
            "success": True,
            "has_contradictions": len(conflicts) > 0,
            "conflicts": conflicts,
            "severity_score": sum(c.get("severity", 0) for c in conflicts) / max(len(conflicts), 1) if conflicts else 0.0
        }

    def _detect_conflict(self, f1: Dict[str, Any], f2: Dict[str, Any]) -> Dict[str, Any]:
        t1 = f1.get("content", "").lower()
        t2 = f2.get("content", "").lower()
        words1 = [w for w in re.split(r'\W+', t1) if w]
        if f"not {t1}" in t2 or f"no {t1}" in t2 or f"never {t1}" in t2 or (("not" in t2 or "no" in t2) and all(w in t2 for w in words1)):
             return {
                 "type": "DIRECT_NEGATION",
                 "f1_id": f1.get("id"),
                 "f2_id": f2.get("id"),
                 "severity": 1.0,
                 "description": f"Finding 2 negates Finding 1: {t2} vs {t1}"
             }
        if f1.get("persona") and f2.get("persona"):
            if f1.get("persona") != f2.get("persona") and f1.get("subject") == f2.get("subject"):
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
