"""
KA-052: Temporal Knowledge Evolution
Purpose: Maintain time-versioned knowledge, handle fact retirement, and track the evolution of the knowledge base.
"""
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA052Input(BaseModel):
    kb_nodes: List[Dict[str, Any]] = Field(default_factory=list, description="Knowledge nodes to evaluate for temporal evolution")

class KA052TemporalKnowledgeEvolution(KnowledgeAlgorithm):
    """
    KA-052: Fact versioning and temporal lifecycle management engine.
    """
    input_schema = KA052Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-052"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_52_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA052Input) -> Dict[str, Any]:
        kb_nodes = input_data.kb_nodes
        current_time = datetime.now()
        self.log_execution_step("Managing Temporal Evolution", {"node_count": len(kb_nodes)})
        
        expired_nodes = []
        updated_nodes = []
        expiry_days = self.config.get("expiry_days", 30)
        automatic_retirement = self.config.get("automatic_retirement", True)
        version_limit = self.config.get("version_limit", 10)
        
        for node in kb_nodes:
            ts_str = node.get("timestamp")
            if ts_str:
                ts = datetime.fromisoformat(ts_str)
                if automatic_retirement and (current_time - ts) > timedelta(days=expiry_days):
                    expired_nodes.append(node.get("id"))
                    continue
            v = node.get("version", 1)
            if v < version_limit:
                 updated_nodes.append({
                     "id": node.get("id"),
                     "new_version": v + 1,
                     "evolution_status": "MONITORED"
                 })
                 
        return {
            "success": True,
            "expired_nodes": expired_nodes,
            "evolution_map": updated_nodes,
            "retirement_count": len(expired_nodes)
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA052TemporalKnowledgeEvolution(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-052 Failed: {e}")
        return {"success": False, "error": str(e)}
