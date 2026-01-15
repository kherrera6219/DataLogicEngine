"""
KA-039: Ontology Drift Detection
Purpose: Monitor and detect semantic drift in ontology definitions over time by comparing snapshots.
"""
import logging
import json
import os
import hashlib
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA039OntologyDriftDetection(KnowledgeAlgorithm):
    """
    KA-039: Semantic and ontology drift detection engine.
    """
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_39_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        current_snapshot = input_data.get("snapshot", {})
        previous_snapshot = input_data.get("previous_snapshot", {})
        
        self.log_execution_step("Detecting Ontology Drift", {"nodes": len(current_snapshot.get("nodes", []))})
        
        # 1. Compare Snapshot Hashes
        curr_hash = hashlib.sha256(json.dumps(current_snapshot, sort_keys=True).encode()).hexdigest()
        prev_hash = hashlib.sha256(json.dumps(previous_snapshot, sort_keys=True).encode()).hexdigest()
        
        drift_detected = curr_hash != prev_hash
        drift_magnitude = 0.0
        
        # 2. Basic Delta Analysis
        if drift_detected:
            # Count added/removed nodes for magnitude (Stub logic)
            curr_nodes = set(n.get("id") for n in current_snapshot.get("nodes", []))
            prev_nodes = set(n.get("id") for n in previous_snapshot.get("nodes", []))
            
            changes = len(curr_nodes.symmetric_difference(prev_nodes))
            total = max(len(curr_nodes), 1)
            drift_magnitude = min(1.0, changes / total)
            
        return {
            "ka_id": "KA-039",
            "ka_name": "Ontology Drift Detection",
            "success": True,
            "drift_detected": drift_detected,
            "drift_magnitude": drift_magnitude,
            "is_significant": drift_magnitude > self.config.get("drift_threshold", 0.3),
            "alert_level": self.config.get("alert_severity", "medium")
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA039OntologyDriftDetection(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-039 Failed: {e}")
        return {"success": False, "error": str(e)}
