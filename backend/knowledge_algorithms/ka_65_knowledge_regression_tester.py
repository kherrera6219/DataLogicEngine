"""KA-065: deterministic structural regression comparison."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA065Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshot: dict[str, Any] = Field(default_factory=dict)
    baseline: dict[str, Any] = Field(default_factory=dict)


class KA065KnowledgeRegressionTester(KnowledgeAlgorithm):
    """Compare supplied node records without returning their values."""

    input_schema = KA065Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-065"

    @staticmethod
    def _nodes(snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
        raw = snapshot.get("nodes", [])
        if isinstance(raw, dict):
            return {
                str(node_id): value if isinstance(value, dict) else {"value": value}
                for node_id, value in raw.items()
            }
        if isinstance(raw, list):
            return {
                str(item["id"]): item
                for item in raw
                if isinstance(item, dict) and item.get("id") is not None
            }
        return {}

    def _run_logic(self, input_data: KA065Input) -> dict[str, Any]:
        current = self._nodes(input_data.snapshot)
        baseline = self._nodes(input_data.baseline)
        regressions = []
        for node_id in sorted(baseline):
            if node_id not in current:
                regressions.append(
                    {"node_id": node_id, "type": "missing_node", "changed_fields": []}
                )
                continue
            changed = sorted(
                key
                for key in set(baseline[node_id]) | set(current[node_id])
                if key != "id" and baseline[node_id].get(key) != current[node_id].get(key)
            )
            if changed:
                regressions.append(
                    {"node_id": node_id, "type": "changed_node", "changed_fields": changed}
                )
        return {
            "success": True,
            "status": "regression_free" if not regressions else "regression_detected",
            "regression_count": len(regressions),
            "regressions": regressions,
            "baseline_node_count": len(baseline),
            "snapshot_node_count": len(current),
            "source_values_returned": False,
            "knowledge_updated": False,
            "deterministic": True,
            "limitations": (
                "This compares supplied structural snapshots only; field changes "
                "require owner review and are not independently classified as errors."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA065KnowledgeRegressionTester(context).run(context)
