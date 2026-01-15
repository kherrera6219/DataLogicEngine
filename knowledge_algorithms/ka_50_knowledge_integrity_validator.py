"""
KA-050: Knowledge Integrity Validator
Purpose: Validate internal consistency, schema compliance, and structural integrity of the KB before persistence.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA050KnowledgeIntegrityValidator(KnowledgeAlgorithm):
    """
    KA-050: KB integrity and consistency validation engine.
    """
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_50_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        kb_snapshot = input_data.get("snapshot", {})
        nodes = kb_snapshot.get("nodes", [])
        edges = kb_snapshot.get("edges", [])
        
        self.log_execution_step("Validating KB Integrity", {"node_count": len(nodes), "edge_count": len(edges)})
        
        issues = []
        
        # 1. Check for dangling edges
        node_ids = set(n.get("id") for n in nodes)
        for edge in edges:
            src = edge.get("source")
            tgt = edge.get("target")
            if src not in node_ids or tgt not in node_ids:
                issues.append({
                    "type": "DANGLING_EDGE",
                    "edge": edge,
                    "description": f"Edge references missing node: {src} -> {tgt}"
                })
                
        # 2. Confidence Floor Validation
        min_conf = self.config.get("min_node_confidence", 0.3)
        for node in nodes:
            if node.get("confidence", 0.0) < min_conf:
                issues.append({
                    "type": "LOW_CONFIDENCE_NODE",
                    "node_id": node.get("id"),
                    "description": f"Node confidence below threshold: {node.get('confidence')}"
                })
                
        status = "PASSED" if not issues else "FAILED"
        if issues and self.config.get("quarantine_on_failure", True):
             status = "QUARANTINED"
             
        return {
            "ka_id": "KA-050",
            "ka_name": "Knowledge Integrity Validator",
            "success": True,
            "status": status,
            "issues_count": len(issues),
            "integrity_report": issues,
            "is_valid": len(issues) == 0
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA050KnowledgeIntegrityValidator(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-050 Failed: {e}")
        return {"success": False, "error": str(e)}
