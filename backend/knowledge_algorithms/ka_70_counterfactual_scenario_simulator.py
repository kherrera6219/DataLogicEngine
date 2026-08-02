"""
KA-070: Counterfactual Scenario Simulator
Purpose: Simulate what-if scenarios by perturbing knowledge nodes and observing downstream ripple effects.
"""
import json
import logging
import os
from typing import Any, Dict, List

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class KA070ScenarioInput(BaseModel):
    model_config = ConfigDict(extra="allow")
    hypotheticals: List[Dict[str, Any]] = Field(default_factory=list, description="Hypothetical changes to knowledge nodes")
    graph: Dict[str, Any] = Field(default_factory=dict)
    dependency_results: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class KA070CounterfactualScenarioSimulator(KnowledgeAlgorithm):
    """
    KA-070: What-if simulation and divergence analysis engine for downstream impact prediction.
    """
    input_schema = KA070ScenarioInput

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-070"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_70_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA070ScenarioInput) -> Dict[str, Any]:
        local_projection = dict(input_data.dependency_results.get("KA-042") or {})
        hypothetical_changes = list(input_data.hypotheticals)
        if not hypothetical_changes and local_projection:
            hypothetical_changes = [
                {
                    "node_id": impact.get("field"),
                    "new_value": impact.get("after"),
                }
                for impact in local_projection.get("impacts", [])
                if impact.get("changed") and impact.get("field")
            ]
        self.log_execution_step("Simulating Counterfactual Scenarios", {"change_count": len(hypothetical_changes)})

        graph = input_data.graph or {}
        depth = self._safe_int(self.config.get("simulation_depth", 3), 3)
        threshold = float(self.config.get("divergence_threshold", 0.4))
        outcomes = [self._simulate_change(change, graph, depth, threshold) for change in hypothetical_changes]
        graph_divergence = sum(item["aggregate_divergence"] for item in outcomes) / len(outcomes) if outcomes else 0.0
        local_divergence = float(local_projection.get("divergence_score") or 0)
        aggregate = max(graph_divergence, local_divergence)
        return {
            "success": True,
            "simulated_outcomes": outcomes,
            "divergence_threshold_applied": threshold,
            "aggregate_divergence": round(aggregate, 4),
            "risk_level": "high" if aggregate >= threshold else "medium" if aggregate >= threshold / 2 else "low",
            "local_projection_consumed": bool(local_projection),
            "local_projection_divergence": local_divergence,
        }

    def _simulate_change(self, change: Dict[str, Any], graph: Dict[str, Any], depth: int, threshold: float) -> Dict[str, Any]:
        node_id = str(change.get("node_id") or change.get("id") or change.get("field") or "unknown")
        new_value = change.get("new_value", change.get("value"))
        visited = {node_id}
        frontier = [(node_id, 1.0)]
        impacts = []
        for level in range(1, depth + 1):
            next_frontier = []
            for node, strength in frontier:
                for target, weight in self._neighbors(node, graph).items():
                    if target in visited:
                        continue
                    visited.add(target)
                    divergence = round(strength * weight, 4)
                    impacts.append({"node": target, "depth": level, "observed_divergence": divergence})
                    if divergence >= threshold / 2:
                        next_frontier.append((target, divergence))
            frontier = next_frontier
        aggregate = sum(item["observed_divergence"] for item in impacts)
        return {
            "changed_node": node_id,
            "hypothetical_value": new_value,
            "downstream_impacts": impacts,
            "aggregate_divergence": round(aggregate, 4),
            "stability_risk": "high" if aggregate >= threshold else "medium" if aggregate > 0 else "low",
        }

    @staticmethod
    def _neighbors(node_id: str, graph: Dict[str, Any]) -> Dict[str, float]:
        raw = graph.get(node_id, {}) if isinstance(graph, dict) else {}
        if isinstance(raw, dict):
            return {str(target): float(weight) for target, weight in raw.items() if isinstance(weight, (int, float))}
        if isinstance(raw, list):
            return {str(target): 0.5 for target in raw}
        return {}

    @staticmethod
    def _safe_int(value: Any, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA070CounterfactualScenarioSimulator(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-070 Failed: {e}")
        return {"success": False, "error": str(e)}
