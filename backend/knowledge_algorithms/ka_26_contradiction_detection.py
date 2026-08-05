"""
KA-026: Contradiction Detection
Purpose: Detect logical conflicts, semantic negations, and stance clashes across diverse findings.
"""

import json
import logging
import os
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)


class KA026Input(BaseModel):
    model_config = ConfigDict(extra="forbid")

    findings: list[dict[str, Any]] = Field(default_factory=list, max_length=1_000)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)


class KA026ContradictionDetection(KnowledgeAlgorithm):
    """
    KA-026: Conflict and contradiction detection engine for multi-persona reasoning.
    """

    input_schema = KA026Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-026"
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        try:
            config_path = os.path.join(
                os.path.dirname(__file__), "config", "ka_26_config.json"
            )
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError):
            return {}

    def _run_logic(self, input_data: KA026Input) -> dict[str, Any]:
        findings = input_data.findings
        self.log_execution_step(
            "Scanning for Contradictions", {"finding_count": len(findings)}
        )

        conflicts = []
        for i in range(len(findings)):
            for j in range(i + 1, len(findings)):
                conflict = self._detect_conflict(findings[i], findings[j])
                if conflict:
                    conflicts.append(conflict)

        return {
            "success": True,
            "has_contradictions": len(conflicts) > 0,
            "conflicts": conflicts,
            "severity_score": sum(c.get("severity", 0) for c in conflicts)
            / max(len(conflicts), 1)
            if conflicts
            else 0.0,
            "dependencies_consumed": sorted(input_data.dependency_results),
            "corrections_applied": 0,
            "deterministic": True,
            "limitations": (
                "Detection uses explicit negation and declared persona/subject "
                "clashes. It does not prove either finding false or resolve it."
            ),
        }

    def _detect_conflict(
        self, f1: dict[str, Any], f2: dict[str, Any]
    ) -> dict[str, Any]:
        t1 = f1.get("content", "").lower()
        t2 = f2.get("content", "").lower()
        words1 = [w for w in re.split(r"\W+", t1) if w]
        if (
            f"not {t1}" in t2
            or f"no {t1}" in t2
            or f"never {t1}" in t2
            or (("not" in t2 or "no" in t2) and all(w in t2 for w in words1))
        ):
            return {
                "type": "DIRECT_NEGATION",
                "f1_id": f1.get("id"),
                "f2_id": f2.get("id"),
                "severity": 1.0,
                "description": "Finding 2 contains an explicit negation of Finding 1.",
            }
        if (
            f1.get("persona")
            and f2.get("persona")
            and f1.get("persona") != f2.get("persona")
            and f1.get("subject") == f2.get("subject")
            and t1 != t2
        ):
            return {
                "type": "STANCE_CLASH",
                "f1_id": f1.get("id"),
                "f2_id": f2.get("id"),
                "severity": 0.5,
                "description": "Stakeholder perspective clash detected.",
            }
        return None


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA026ContradictionDetection(context).run(context)
