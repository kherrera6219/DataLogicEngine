"""
KA-042: Counterfactual Simulator
Purpose: Simulate "what if" scenarios.
"""
import logging
from typing import Any, Dict

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class KA042Input(BaseModel):
    model_config = ConfigDict(extra="allow")
    scenario: str = ""
    change: Any = ""
    baseline: Dict[str, Any] = Field(default_factory=dict)
    relationships: Dict[str, Any] = Field(default_factory=dict)


class KA042CounterfactualSimulator(KnowledgeAlgorithm):
    input_schema = KA042Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-042"

    def _run_logic(self, input_data: KA042Input) -> Dict[str, Any]:
        self.log_execution_step("Simulating Counterfactual", {"scenario": input_data.scenario, "change": str(input_data.change)})

        baseline = dict(input_data.baseline)
        perturbations = self._normalize_change(input_data.change)
        projected = dict(baseline)
        impacts = []
        for key, new_value in perturbations.items():
            old_value = projected.get(key)
            projected[key] = new_value
            impacts.append(self._impact_record(key, old_value, new_value))
            for target, weight in self._dependent_targets(key, input_data.relationships).items():
                before = projected.get(target, 0)
                projected[target] = self._apply_dependency(before, old_value, new_value, weight)
                impacts.append(self._impact_record(target, before, projected[target], driver=key))

        divergence = self._divergence(baseline, projected)
        return {
            "ka_id": self.ka_id,
            "success": True,
            "outcome": f"Projected {len(impacts)} local state change(s) for scenario '{input_data.scenario}'.",
            "baseline": baseline,
            "projected_state": projected,
            "impacts": impacts,
            "divergence_score": divergence,
            "risk_level": "high" if divergence >= 0.6 else "medium" if divergence >= 0.25 else "low",
        }

    @staticmethod
    def _normalize_change(change: Any) -> Dict[str, Any]:
        if isinstance(change, dict):
            return dict(change)
        if isinstance(change, list):
            return {str(item.get("field", item.get("key", index))): item.get("value") for index, item in enumerate(change) if isinstance(item, dict)}
        return {"change": change}

    @staticmethod
    def _dependent_targets(key: str, relationships: Dict[str, Any]) -> Dict[str, float]:
        raw = relationships.get(key, {}) if isinstance(relationships, dict) else {}
        if isinstance(raw, dict):
            return {str(target): float(weight) for target, weight in raw.items() if isinstance(weight, (int, float))}
        return {}

    @staticmethod
    def _apply_dependency(before: Any, old_value: Any, new_value: Any, weight: float) -> Any:
        if all(isinstance(value, (int, float)) for value in (before, old_value, new_value)):
            return round(float(before) + (float(new_value) - float(old_value)) * weight, 4)
        return f"affected_by_{new_value}"

    @staticmethod
    def _impact_record(key: str, old_value: Any, new_value: Any, driver: str | None = None) -> Dict[str, Any]:
        changed = old_value != new_value
        magnitude = abs(float(new_value) - float(old_value)) if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)) else (1.0 if changed else 0.0)
        return {"field": key, "driver": driver or key, "before": old_value, "after": new_value, "changed": changed, "magnitude": round(magnitude, 4)}

    @staticmethod
    def _divergence(baseline: Dict[str, Any], projected: Dict[str, Any]) -> float:
        keys = set(baseline) | set(projected)
        if not keys:
            return 0.0
        changed = sum(1 for key in keys if baseline.get(key) != projected.get(key))
        return round(changed / len(keys), 4)


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA042CounterfactualSimulator(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-042 Failed: {e}")
        return {"success": False, "error": str(e)}
