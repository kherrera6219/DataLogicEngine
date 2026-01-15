"""
KA-049: Knowledge Redundancy Detector
Purpose: Detect duplicate or near-duplicate knowledge nodes and fragments across the system.
"""
import logging
import json
import os
import hashlib
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

class KA049Input(BaseModel):
    nodes: List[Dict[str, Any]] = Field(default_factory=list, description="A list of knowledge nodes to analyze for redundancy")

class KA049KnowledgeRedundancyDetector(KnowledgeAlgorithm):
    """
    KA-049: Deduplication and redundancy analysis engine for KB fragments.
    """
    input_schema = KA049Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-049"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_49_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA049Input) -> Dict[str, Any]:
        nodes = input_data.nodes
        self.log_execution_step("Detecting Knowledge Redundancy", {"node_count": len(nodes)})
        
        duplicates = []
        hashes = {}
        for node in nodes:
             content = node.get("content", "")
             h = hashlib.md5(content.encode()).hexdigest()
             if h in hashes:
                  duplicates.append({
                      "node_id": node.get("id"),
                      "duplicate_of": hashes[h],
                      "type": "EXACT_DUPLICATE"
                  })
             else:
                  hashes[h] = node.get("id")
                  
        return {
            "success": True,
            "redundancy_count": len(duplicates),
            "duplicate_groups": duplicates,
            "deduplication_recommended": len(duplicates) > 0
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA049KnowledgeRedundancyDetector(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-049 Failed: {e}")
        return {"success": False, "error": str(e)}
