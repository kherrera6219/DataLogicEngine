"""
KA-009: Evidence Validation
Purpose: Validate pieces of evidence based on source credibility, relevance, and SDK-level fact checking.
"""
import logging
import json
import os
from typing import Dict, Any, List
import importlib
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA009Input(BaseModel):
    evidence: List[Dict[str, Any]] = Field(default_factory=list, description="A list of evidence snippets to validate")
    query: str = Field("", description="The query to validate evidence against")

class KA009EvidenceValidation(KnowledgeAlgorithm):
    """
    KA-009: Scorer and validator for evidence snippets.
    """
    input_schema = KA009Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-009"
        self.config = self._load_config()
        self.sdk_module = "ukg_sdk.ka.handlers.ka_009"

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_09_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA009Input) -> Dict[str, Any]:
        evidence_list = input_data.evidence
        query = input_data.query
        
        self.log_execution_step("Validating Evidence", {"count": len(evidence_list)})
        
        results = []
        for item in evidence_list:
            local_score = self._calculate_local_score(item, query)
            sdk_res = self._delegate_to_sdk({"item": item, "query": query})
            final_score = (local_score + sdk_res.get("score", local_score)) / 2
            
            results.append({
                "source": item.get("source"),
                "score": final_score,
                "is_valid": final_score >= self.config.get("min_evidence_score", 0.3),
                "sdk_feedback": sdk_res.get("feedback")
            })
            
        return {
            "success": True,
            "results": results,
            "overall_validity": all(r["is_valid"] for r in results) if results else True
        }

    def _calculate_local_score(self, item: Dict[str, Any], query: str) -> float:
        content = item.get("content", "").lower()
        source_type = item.get("source_type", "unknown")
        source_scores = self.config.get("trusted_sources", {})
        credibility = source_scores.get(source_type, 0.4)
        
        query_words = set(query.lower().split())
        content_words = set(content.split())
        overlap = len(query_words.intersection(content_words)) / max(len(query_words), 1)
        relevance = min(1.0, overlap * 2.0)
        
        return (credibility * 0.6) + (relevance * 0.4)

    def _delegate_to_sdk(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            mod = importlib.import_module(self.sdk_module)
            if hasattr(mod, "run"):
                return mod.run(data)
            else:
                func = getattr(mod, "ka_009", None) or getattr(mod, "validate_evidence", None)
                if func:
                    return func(data)
                return {"score": 0.5}
        except Exception:
            return {"score": 0.5}

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA009EvidenceValidation(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-009 Failed: {e}")
        return {"success": False, "error": str(e)}
