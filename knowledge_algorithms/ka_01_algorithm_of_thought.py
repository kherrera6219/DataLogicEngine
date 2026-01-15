"""
KA-001: Algorithm of Thought (AoT)
Purpose: Decompose query into ordered tasks and dependencies.
"""
import logging
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA001AlgorithmOfThought(KnowledgeAlgorithm):
    """
    KA-001: Decomposes complex queries into a Directed Acyclic Graph (DAG) of tasks.
    """
    def __init__(self, context: Dict[str, Any]):
        # Initialize with context as config, managers None for now
        super().__init__(context, None, None, None)
        
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute AoT decomposition.
        """
        query = input_data.get("query", "")
        if not query:
            return {"error": "No query provided", "success": False}
            
        self.log_execution_step("Decomposing query", {"query": query})
        
        # Simple rule-based decomposition for now
        tasks = self._decompose(query)
        
        return {
            "ka_id": "KA-001",
            "ka_name": "Algorithm of Thought",
            "success": True,
            "tasks": tasks,
            "graph": self._build_dependency_graph(tasks)
        }

    def _decompose(self, query: str) -> List[Dict[str, Any]]:
        tasks = []
        # Always have a validate step
        tasks.append({"id": "t1", "name": "Validate Input", "ka": "KA-004"})
        
        # Analyze step
        tasks.append({"id": "t2", "name": "Analyze Query", "ka": "KA-005", "deps": ["t1"]})
        
        # If complex, add planning
        if len(query.split()) > 10 or "complex" in query.lower():
            tasks.append({"id": "t3", "name": "Deep Planning", "ka": "KA-006", "deps": ["t2"]})
            tasks.append({"id": "t4", "name": "Execute Plan", "type": "execution", "deps": ["t3"]})
        else:
             tasks.append({"id": "t3", "name": "Direct Execution", "type": "execution", "deps": ["t2"]})
             
        # Synthesis
        tasks.append({"id": "tn", "name": "Synthesize Response", "ka": "KA-019", "deps": [t["id"] for t in tasks if t["id"] != "tn"]})
        
        return tasks

    def _build_dependency_graph(self, tasks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        adj_list = {}
        for t in tasks:
            adj_list[t["id"]] = t.get("deps", [])
        return adj_list

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA001AlgorithmOfThought(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-001 Failed: {e}")
        return {"success": False, "error": str(e)}
