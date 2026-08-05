"""KA-016: deterministic mapping of explicit regulatory framework IDs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA016Input(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "query": "Assess the declared privacy controls.",
                    "frameworks": ["GDPR"],
                }
            ]
        },
    )

    query: str = Field(default="", max_length=100_000)
    frameworks: list[str] = Field(default_factory=list, max_length=100)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_dependencies(self) -> KA016Input:
        if self.dependency_results and set(self.dependency_results) != {
            "KA-017",
            "KA-018",
        }:
            raise ValueError("dependency_results must contain KA-017 and KA-018")
        return self


class KA016RegulatoryMapping(KnowledgeAlgorithm):
    """Look up explicitly requested framework IDs in the governed local catalog."""

    input_schema = KA016Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-016"
        self.catalog = self._load_catalog()

    @staticmethod
    def _load_catalog() -> dict[str, dict[str, Any]]:
        path = Path(__file__).with_name("config") / "ka_16_config.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return {}
        frameworks = payload.get("compliance_frameworks")
        return frameworks if isinstance(frameworks, dict) else {}

    def _run_logic(self, input_data: KA016Input) -> dict[str, Any]:
        requested = sorted({item.strip() for item in input_data.frameworks if item.strip()})
        mappings = []
        for framework_id in requested:
            catalog_key = next(
                (
                    key
                    for key in self.catalog
                    if key.casefold() == framework_id.casefold()
                ),
                None,
            )
            definition = self.catalog.get(catalog_key, {}) if catalog_key else {}
            known = bool(catalog_key)
            mappings.append(
                {
                    "framework": catalog_key or framework_id,
                    "status": "mapped" if known else "unknown_framework",
                    "obligations": sorted(
                        {
                            str(item)
                            for item in definition.get("obligations", [])
                            if str(item).strip()
                        }
                    ),
                    "risk_assessment": (
                        float(definition.get("risk_score", 1.0)) if known else 1.0
                    ),
                }
            )
        jurisdiction = input_data.dependency_results.get("KA-017", {})
        provenance = input_data.dependency_results.get("KA-018", {})
        dependency_context_ready = not input_data.dependency_results or (
            bool(jurisdiction.get("matches"))
            and provenance.get("status") == "provenance_measured"
        )
        complete = bool(mappings) and all(
            row["status"] == "mapped" for row in mappings
        ) and dependency_context_ready
        return {
            "success": True,
            "status": (
                "regulatory_frameworks_mapped"
                if complete
                else "regulatory_evidence_required"
            ),
            "mappings": mappings,
            "highest_risk": max(
                (row["risk_assessment"] for row in mappings), default=1.0
            ),
            "dependency_context_ready": dependency_context_ready,
            "dependencies_consumed": sorted(input_data.dependency_results),
            "query_content_inspected": False,
            "legal_applicability_established": False,
            "external_lookup_performed": False,
            "deterministic": True,
            "limitations": (
                "Framework IDs must be explicit and exist in the governed local "
                "catalog. Mapping does not establish legal applicability or advice."
            ),
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA016RegulatoryMapping(context).run(context)
