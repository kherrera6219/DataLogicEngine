"""
KA-010: Bias Detection
Purpose: Scan content for linguistic and conceptual bias, and suggest neutral alternatives.
"""
import logging
import json
import os
import re
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field

class KA010Input(BaseModel):
    content: str = Field(..., description="The content to scan for bias")

class KA010BiasDetection(KnowledgeAlgorithm):
    """
    KA-010: Detects biased patterns in text based on configurable keyword sets.
    """
    input_schema = KA010Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-010"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_10_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA010Input) -> Dict[str, Any]:
        content = input_data.content
        self.log_execution_step("Scanning for Bias", {"content_len": len(content)})
        
        findings = self._scan_for_bias(content)
        bias_score = self._calculate_bias_score(findings, content)
        
        return {
            "success": True,
            "bias_score": bias_score,
            "findings": findings,
            "is_biased": bias_score > self.config.get("severity_threshold", 0.2)
        }

    def _scan_for_bias(self, content: str) -> List[Dict[str, Any]]:
        findings = []
        categories = self.config.get("bias_categories", {})
        for cat_name, info in categories.items():
            keywords = info.get("keywords", [])
            suggestions = info.get("suggestions", {})
            for kw in keywords:
                matches = re.finditer(rf"\b{kw}\b", content, re.IGNORECASE)
                for match in matches:
                    findings.append({
                        "category": cat_name,
                        "term": kw,
                        "matched_text": match.group(),
                        "position": match.start(),
                        "suggestion": suggestions.get(kw.lower(), "Consider neutral phrasing")
                    })
        return findings

    def _calculate_bias_score(self, findings: List[Dict[str, Any]], content: str) -> float:
        if not content: return 0.0
        word_count = max(len(content.split()), 1)
        return min(1.0, len(findings) / (word_count / 10))

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA010BiasDetection(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-010 Failed: {e}")
        return {"success": False, "error": str(e)}
