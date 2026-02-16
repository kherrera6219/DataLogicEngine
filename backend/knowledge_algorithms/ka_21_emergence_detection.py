"""
KA-021: Emergence Detection
Purpose: Detect novel patterns, unexpected insights, or emergent behaviors in reasoning traces.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field

class KA021Input(BaseModel):
    findings: List[Dict[str, Any]] = Field(default_factory=list, description="Reasoning findings to scan for emergence")
    entropy: float = Field(0.0, ge=0.0, description="Current system entropy level")

class KA021EmergenceDetection(KnowledgeAlgorithm):
    """
    KA-021: Scans for novelty and emergence signals in reasoning traces.
    """
    input_schema = KA021Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-021"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_21_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA021Input) -> Dict[str, Any]:
        findings = input_data.findings
        entropy = input_data.entropy
        
        self.log_execution_step("Detecting Emergence", {"finding_count": len(findings), "entropy": entropy})
        
        novelty_score = 0.0
        signals = []
        
        if entropy > self.config.get("novelty_threshold", 0.7):
            novelty_score += 0.4
            signals.append("High Entropy Spike")
            
        if len(findings) > 10:
            novelty_score += 0.3
            signals.append("Fact Proliferation")
            
        keywords = ["breakthrough", "paradigm", "unexpected", "novel", "emergent"]
        content_str = str(findings).lower()
        if any(kw in content_str for kw in keywords):
            novelty_score += 0.2
            signals.append("Linguistic Novelty Detected")
            
        return {
            "success": True,
            "novelty_score": min(1.0, novelty_score),
            "emergence_signals": signals,
            "is_emergent": novelty_score >= self.config.get("novelty_threshold", 0.7)
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA021EmergenceDetection(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-021 Failed: {e}")
        return {"success": False, "error": str(e)}
