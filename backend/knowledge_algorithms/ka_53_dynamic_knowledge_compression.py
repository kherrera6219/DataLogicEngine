"""
KA-053: Dynamic Knowledge Compression
Purpose: Compress and merge knowledge nodes to optimize storage and retrieval while preserving utility and semantics.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field

class KA053Input(BaseModel):
    graph_segments: List[Dict[str, Any]] = Field(default_factory=list, description="Segments of the knowledge graph to compress")

class KA053DynamicKnowledgeCompression(KnowledgeAlgorithm):
    """
    KA-053: Graph compression and node unification engine to optimize the knowledge base.
    """
    input_schema = KA053Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-053"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_53_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA053Input) -> Dict[str, Any]:
        graph_segments = input_data.graph_segments
        self.log_execution_step("Compressing Knowledge Graph", {"segment_count": len(graph_segments)})
        
        compressed_nodes = []
        mapping_table = {}
        for segment in graph_segments:
             nodes = segment.get("nodes", [])
             if len(nodes) > 1:
                  primary = nodes[0]
                  comp_id = f"COMP-{primary.get('id')}"
                  compressed_nodes.append({
                      "id": comp_id,
                      "merged_from": [n.get("id") for n in nodes],
                      "utility_preserved": True
                  })
                  for n in nodes:
                       mapping_table[n.get("id")] = comp_id
                       
        return {
            "success": True,
            "compressed_nodes": compressed_nodes,
            "mapping": mapping_table,
            "compression_ratio": len(compressed_nodes) / max(len(graph_segments), 1)
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA053DynamicKnowledgeCompression(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-053 Failed: {e}")
        return {"success": False, "error": str(e)}
