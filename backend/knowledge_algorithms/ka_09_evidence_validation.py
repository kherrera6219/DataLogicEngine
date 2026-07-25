"""KA-009: deterministic evidence credibility and relevance validation."""

import json
import logging
import os
from typing import Any

from pydantic import BaseModel, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)


class KA009Input(BaseModel):
    evidence: list[dict[str, Any]] = Field(default_factory=list, description="A list of evidence snippets to validate")
    query: str = Field("", description="The query to validate evidence against")

class KA009EvidenceValidation(KnowledgeAlgorithm):
    """
    KA-009: Scorer and validator for evidence snippets.
    """
    input_schema = KA009Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-009"
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_09_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError):
            return {}

    def _run_logic(self, input_data: KA009Input) -> dict[str, Any]:
        evidence_list = input_data.evidence
        query = input_data.query

        if not evidence_list:
            return {
                "success": False,
                "status": "insufficient_evidence",
                "results": [],
                "overall_validity": False,
            }
        
        self.log_execution_step("Validating Evidence", {"count": len(evidence_list)})
        
        results = []
        for item in evidence_list:
            final_score = self._calculate_local_score(item, query)
            
            results.append({
                "source": item.get("source"),
                "score": final_score,
                "is_valid": final_score >= self.config.get("min_evidence_score", 0.3),
                "sdk_feedback": None,
            })
            
        return {
            "success": True,
            "results": results,
            "overall_validity": all(r["is_valid"] for r in results) if results else True
        }

    def _calculate_local_score(self, item: dict[str, Any], query: str) -> float:
        content = item.get("content", "").lower()
        source_type = item.get("source_type", "unknown")
        source_scores = self.config.get("trusted_sources", {})
        credibility = source_scores.get(source_type, 0.4)
        
        query_words = set(query.lower().split())
        content_words = set(content.split())
        overlap = len(query_words.intersection(content_words)) / max(len(query_words), 1)
        relevance = min(1.0, overlap * 2.0)
        
        return (credibility * 0.6) + (relevance * 0.4)

def run(context: dict[str, Any]) -> dict[str, Any]:
    try:
        algo = KA009EvidenceValidation(context)
        result = algo.run(context)
        output = result.get("output") if isinstance(result.get("output"), dict) else {}
        if output.get("status"):
            result["status"] = output["status"]
        return result
    except Exception as e:  # noqa: BLE001 - KA boundary returns a stable failure
        logger.error(f"KA-009 Failed: {e}")
        return {"success": False, "error": str(e)}
