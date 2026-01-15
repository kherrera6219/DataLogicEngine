"""
KA-016: Regulatory Mapping
Purpose: Map queries and scenarios to specific regulatory frameworks and obligations.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

class KA016Input(BaseModel):
    query: str = Field(..., description="The query to map to regulations")
    frameworks: List[str] = Field(default_factory=list, description="Optional specific frameworks to check")

class KA016RegulatoryMapping(KnowledgeAlgorithm):
    """
    KA-016: Compliance and Regulatory mapping engine.
    """
    input_schema = KA016Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-016"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_16_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA016Input) -> Dict[str, Any]:
        query = input_data.query.lower()
        requested_frameworks = input_data.frameworks
        
        self.log_execution_step("Regulatory Mapping", {"query": query, "frameworks": requested_frameworks})
        
        frameworks_config = self.config.get("compliance_frameworks", {})
        
        if not requested_frameworks:
            for fw, info in frameworks_config.items():
                if fw.lower() in query:
                    requested_frameworks.append(fw)
                    
        if not requested_frameworks:
            requested_frameworks = [self.config.get("default_framework", "INTERNAL")]
            
        mappings = []
        for fw in requested_frameworks:
            info = frameworks_config.get(fw)
            if info:
                mappings.append({
                    "framework": fw,
                    "obligations": info.get("obligations", []),
                    "risk_assessment": info.get("risk_score", 0.5)
                })
                
        return {
            "success": True,
            "mappings": mappings,
            "highest_risk": max([m["risk_assessment"] for m in mappings]) if mappings else 0.0
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA016RegulatoryMapping(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-016 Failed: {e}")
        return {"success": False, "error": str(e)}
