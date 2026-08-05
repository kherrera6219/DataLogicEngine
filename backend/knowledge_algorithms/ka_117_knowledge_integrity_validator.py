"""KA-117: deterministic knowledge-graph integrity validation."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA117Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshot: dict[str, Any] = Field(default_factory=dict)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_dependency(self) -> KA117Input:
        if self.dependency_results and set(self.dependency_results) != {"KA-065"}:
            raise ValueError("KA-117 requires the exact KA-065 dependency result")
        return self


class KA117KnowledgeIntegrityValidator(KnowledgeAlgorithm):
    """Validate declared structure without quarantining or mutating knowledge."""

    input_schema = KA117Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-117"
        self.config = self._load_config()

    @staticmethod
    def _load_config() -> dict[str, Any]:
        try:
            config_path = os.path.join(
                os.path.dirname(__file__), "config", "ka_117_config.json"
            )
            if os.path.exists(config_path):
                with open(config_path) as stream:
                    return json.load(stream) or {}
        except Exception:
            return {}
        return {}

    def _run_logic(self, input_data: KA117Input) -> dict[str, Any]:
        nodes = input_data.snapshot.get("nodes", [])
        edges = input_data.snapshot.get("edges", [])
        nodes = nodes if isinstance(nodes, list) else []
        edges = edges if isinstance(edges, list) else []
        node_ids = [str(node.get("id")) for node in nodes if isinstance(node, dict) and node.get("id") is not None]
        issues = []
        if len(node_ids) != len(set(node_ids)):
                issues.append({"type": "DUPLICATE_NODE_ID"})
        known = set(node_ids)
        for index, edge in enumerate(edges):
            if not isinstance(edge, dict):
                issues.append({"type": "INVALID_EDGE", "edge_index": index})
                continue
            missing = sorted(
                value
                for value in (str(edge.get("source")), str(edge.get("target")))
                if value not in known
            )
            if missing:
                issues.append(
                    {"type": "DANGLING_EDGE", "edge_index": index, "missing_node_ids": missing}
                )
        minimum_confidence = float(self.config.get("min_node_confidence", 0.3))
        for node in nodes:
            if isinstance(node, dict) and float(node.get("confidence", 1.0)) < minimum_confidence:
                issues.append(
                    {"type": "LOW_CONFIDENCE_NODE", "node_id": str(node.get("id"))}
                )
        regression = input_data.dependency_results.get("KA-065", {})
        if regression and regression.get("status") != "regression_free":
            issues.append({"type": "REGRESSION_DEPENDENCY_FAILED"})
        valid = not issues
        status = "PASSED" if valid else "FAILED"
        if issues and self.config.get("quarantine_on_failure", True):
            status = "QUARANTINED"
        return {
            "success": True,
            "status": status,
            "is_valid": valid,
            "issues": issues,
            "issue_count": len(issues),
            "integrity_report": issues,
            "issues_count": len(issues),
            "dependency_consumed": "KA-065" if regression else None,
            "quarantine_applied": False,
            "knowledge_updated": False,
            "deterministic": True,
            "limitations": (
                "Validation is limited to the supplied snapshot and regression "
                "result; the owner decides whether any record is quarantined."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    try:
        return KA117KnowledgeIntegrityValidator(context).run(context)
    except Exception as exc:
        logging.getLogger(__name__).error("KA-117 failed: %s", exc)
        return {"success": False, "error": str(exc)}
