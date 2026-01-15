"""
KA-042: Contradiction Propagation Analysis
Purpose: Trace the downstream impacts of detected contradictions through the dependency graph.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA042ContradictionPropagationAnalysis(KnowledgeAlgorithm):
    """
    KA-042: Contradiction impact and ripple effect analysis engine.
    """
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_42_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        conflicts = input_data.get("conflicts", [])
        dependencies = input_data.get("dependencies", {}) # Adjacency list
        
        self.log_execution_step("Tracing Contradiction Ripples", {"conflict_count": len(conflicts)})
        
        affected_nodes = {}
        propagation_depth = self.config.get("propagation_depth", 3)
        
        for c in conflicts:
            f1_id = c.get("f1_id")
            f2_id = c.get("f2_id")
            severity = c.get("severity", 1.0)
            
            # Start BFS from the conflicting nodes
            queue = [(f1_id, 0), (f2_id, 0)]
            visited = set()
            
            while queue:
                node_id, depth = queue.pop(0)
                if node_id in visited or depth >= propagation_depth:
                    continue
                visited.add(node_id)
                
                if node_id not in [f1_id, f2_id]:
                    # This node is affected by the contradiction downstream
                    affected_nodes[node_id] = affected_nodes.get(node_id, 0.0) + (severity / (depth + 1))
                
                # Add neighbors
                for neighbor in dependencies.get(node_id, []):
                    queue.append((neighbor, depth + 1))
                    
        return {
            "ka_id": "KA-042",
            "ka_name": "Contradiction Propagation Analysis",
            "success": True,
            "impacted_nodes": affected_nodes,
            "total_affected": len(affected_nodes),
            "priority_fixes": sorted(affected_nodes.keys(), key=lambda x: affected_nodes[x], reverse=True)[:5]
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA042ContradictionPropagationAnalysis(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-042 Failed: {e}")
        return {"success": False, "error": str(e)}
