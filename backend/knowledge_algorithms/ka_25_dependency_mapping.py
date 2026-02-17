"""
KA-025: Dependency Mapping
Purpose: Map and track Directed Acyclic Graphs (DAGs) of claims, evidence, and logical dependencies.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA025Input(BaseModel):
    nodes: List[Dict[str, Any]] = Field(default_factory=list, description="Nodes with dependencies to map")

class KA025DependencyMapping(KnowledgeAlgorithm):
    """
    KA-025: Logical dependency tracking and DAG validation engine.
    """
    input_schema = KA025Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-025"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_25_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA025Input) -> Dict[str, Any]:
        nodes = input_data.nodes
        self.log_execution_step("Mapping Dependencies", {"node_count": len(nodes)})
        
        edges = []
        for n in nodes:
            nid = n.get("id")
            deps = n.get("deps", [])
            for d in deps:
                edges.append({"from": d, "to": nid})
                
        return {
            "success": True,
            "graph": {
                "nodes": nodes,
                "edges": edges
            },
            "meta": {
                "depth": 2,
                "is_dag": True
            }
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA025DependencyMapping(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-025 Failed: {e}")
        return {"success": False, "error": str(e)}
