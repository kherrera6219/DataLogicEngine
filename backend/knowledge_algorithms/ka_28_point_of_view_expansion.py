"""
KA-028: Point-of-View Expansion
Purpose: Generate alternate stakeholder perspectives to identify blind spots and objections.
"""
import logging
import json
import os
import random
from typing import Dict, Any
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA028Input(BaseModel):
    query: str = Field(..., description="The query to expand perspectives for")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context for expansion")

class KA028POVExpansion(KnowledgeAlgorithm):
    """
    KA-028: Expand analysis with additional stakeholder POVs to identify blind spots.
    """
    input_schema = KA028Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-028"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_28_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA028Input) -> Dict[str, Any]:
        query = input_data.query
        self.log_execution_step("Expanding Perspectives", {"query": query})
        
        extra_personas = self.config.get("extra_personas", {})
        limit = self.config.get("expansion_limit", 2)
        selected_keys = random.sample(list(extra_personas.keys()), min(len(extra_personas), limit))
        
        additional_findings = []
        for key in selected_keys:
            p_info = extra_personas[key]
            finding = self._generate_pov_finding(key, p_info, query)
            additional_findings.append(finding)
            
        return {
            "success": True,
            "additional_perspectives": additional_findings,
            "count": len(additional_findings)
        }

    def _generate_pov_finding(self, key: str, info: Dict[str, Any], query: str) -> Dict[str, Any]:
        focus = info.get("focus")
        tone = info.get("tone")
        response = f"[{key.upper()} Perspective]: Analyzing '{query}' with a focus on {focus}. " \
                   f"The primary concern from this standpoint is ensuring that we optimize for {tone} outcomes."
        return {
            "persona": key,
            "focus": focus,
            "content": response,
            "confidence": 0.8
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA028POVExpansion(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-028 Failed: {e}")
        return {"success": False, "error": str(e)}
