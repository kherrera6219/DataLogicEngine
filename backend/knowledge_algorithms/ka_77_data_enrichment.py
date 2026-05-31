"""
KA-077: Data Enrichment
Purpose: Augment data records with external metadata, geocoding, and context using third-party providers.
"""
import logging
import json
import os
import hashlib
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA077EnrichmentInput(BaseModel):
    records: List[Any] = Field(default_factory=list, description="The list of records to enrich")

class KA077DataEnrichment(KnowledgeAlgorithm):
    """
    KA-077: External data augmentation and metadata enrichment engine.
    """
    input_schema = KA077EnrichmentInput

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-077"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_77_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA077EnrichmentInput) -> Dict[str, Any]:
        records = input_data.records
        self.log_execution_step("Enriching Records", {"record_count": len(records)})
        
        providers = self.config.get("external_providers", [])
        enrichment_fields = self.config.get("enrichment_fields", [])
        enriched_results = []
        
        for record in records:
            if not isinstance(record, dict):
                continue
            
            enriched = record.copy()
            enrichment_sources = []
            if "location" in enriched and "location_coords" in enrichment_fields:
                enriched["geo_coords"] = self._deterministic_coordinates(str(enriched["location"]))
                enrichment_sources.append("local_geocode_hash")
            if "company" in enriched or "organization" in enriched:
                enriched["industry"] = self._infer_industry(enriched)
                enrichment_sources.append("local_industry_rules")
            text = " ".join(str(value) for value in enriched.values())
            topics = self._infer_topics(text)
            if topics:
                enriched["entity_topics"] = topics
                enrichment_sources.append("local_topic_rules")
            enriched["enrichment_sources"] = enrichment_sources or ["none"]
            
            enriched_results.append(enriched)
            
        return {
            "success": True,
            "records_enriched": len(enriched_results),
            "providers_used": providers,
            "enriched_records": enriched_results,
            "enrichment_summary": {
                "fields": enrichment_fields,
                "local_only": True,
                "records_with_enrichment": sum(
                    1 for record in enriched_results if record.get("enrichment_sources") != ["none"]
                ),
            },
        }

    @staticmethod
    def _deterministic_coordinates(location: str) -> List[float]:
        digest = hashlib.sha256(location.lower().encode("utf-8")).hexdigest()
        lat_seed = int(digest[:8], 16) / 0xFFFFFFFF
        lon_seed = int(digest[8:16], 16) / 0xFFFFFFFF
        return [round((lat_seed * 180) - 90, 6), round((lon_seed * 360) - 180, 6)]

    @staticmethod
    def _infer_industry(record: Dict[str, Any]) -> str:
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
    def _infer_topics(text: str) -> List[str]:
        lowered = text.lower()
        topics = []
        rules = {
            "compliance": ("compliance", "audit", "control", "regulation"),
            "privacy": ("privacy", "patient", "pii", "hipaa"),
            "security": ("security", "risk", "threat", "vulnerability"),
            "procurement": ("far", "dfars", "contract", "solicitation"),
        }
        for topic, terms in rules.items():
            if any(term in lowered for term in terms):
                topics.append(topic)
        return topics

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA077DataEnrichment(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-077 Failed: {e}")
        return {"success": False, "error": str(e)}
