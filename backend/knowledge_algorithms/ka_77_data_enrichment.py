"""KA-077: bounded local-rule enrichment with no provider egress."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.knowledge_algorithms.ingestion_pipeline_utils import dependency_records
from backend.knowledge_algorithms.production_utils import load_config
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm


class KA077EnrichmentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    records: list[Any] = Field(default_factory=list, max_length=1_000)
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)


class KA077DataEnrichment(KnowledgeAlgorithm):
    input_schema = KA077EnrichmentInput

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-077"
        self.config = load_config(__file__, "ka_77_config.json")

    def _run_logic(self, input_data: KA077EnrichmentInput) -> dict[str, Any]:
        records = dependency_records(
            input_data.dependency_results,
            "KA-076",
            "resolved_records",
            input_data.records,
        )
        enriched_results: list[dict[str, Any]] = []
        for record in records:
            if not isinstance(record, dict):
                continue
            enriched = dict(record)
            enrichment_sources: list[str] = []
            if "company" in enriched or "organization" in enriched:
                enriched["industry"] = self._infer_industry(enriched)
                enrichment_sources.append("local_industry_rules")
            text = " ".join(str(value) for value in enriched.values())
            topics = self._infer_topics(text)
            if topics:
                enriched["entity_topics"] = topics
                enrichment_sources.append("local_topic_rules")
            enriched["enrichment_sources"] = enrichment_sources
            enriched_results.append(enriched)

        records_with_enrichment = sum(
            bool(record.get("enrichment_sources")) for record in enriched_results
        )
        self.log_execution_step(
            "Applied local enrichment rules",
            {"count": len(enriched_results), "enriched": records_with_enrichment},
        )
        return {
            "success": True,
            "records_enriched": len(enriched_results),
            "providers_used": [],
            "external_calls": 0,
            "enriched_records": enriched_results,
            "enrichment_summary": {
                "fields": ["industry", "entity_topics"],
                "inference_basis": "deterministic_local_rules",
                "local_only": True,
                "records_with_enrichment": records_with_enrichment,
                "coordinates_generated": 0,
            },
            "dependency_consumed": "KA-076" in input_data.dependency_results,
        }

    @staticmethod
    def _infer_industry(record: dict[str, Any]) -> str:
        text = " ".join(str(value).lower() for value in record.values())
        rules = {
            "healthcare": ("health", "hospital", "patient", "hipaa", "medical"),
            "finance": ("bank", "payment", "sox", "audit", "financial"),
            "defense": ("far", "dfars", "contract", "acquisition", "defense"),
            "technology": ("software", "cloud", "api", "data", "ai"),
        }
        for industry, terms in rules.items():
            if any(term in text for term in terms):
                return industry
        return "general"

    @staticmethod
    def _infer_topics(text: str) -> list[str]:
        lowered = text.lower()
        rules = {
            "compliance": ("compliance", "audit", "control", "regulation"),
            "privacy": ("privacy", "patient", "pii", "hipaa"),
            "security": ("security", "risk", "threat", "vulnerability"),
            "procurement": ("far", "dfars", "contract", "solicitation"),
        }
        return [
            topic
            for topic, terms in rules.items()
            if any(term in lowered for term in terms)
        ]


def run(context: dict[str, Any]) -> dict[str, Any]:
    return KA077DataEnrichment(context).run(context)
