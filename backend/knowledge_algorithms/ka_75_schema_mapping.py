"""
KA-075: Schema Mapping
Purpose: Align source-specific record structures into canonical enterprise schemas.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA075MappingInput(BaseModel):
    records: List[Any] = Field(default_factory=list, description="The list of records to map")
    target_schema: str = Field("user_profile", description="The name of the target canonical schema")

class KA075SchemaMapping(KnowledgeAlgorithm):
    """
    KA-075: Cross-system schema alignment and canonical mapping engine.
    """
    input_schema = KA075MappingInput

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-075"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_75_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA075MappingInput) -> Dict[str, Any]:
        records = input_data.records
        target_schema_name = input_data.target_schema
        self.log_execution_step("Mapping to Canonical Schema", {"target": target_schema_name, "count": len(records)})
        
        canonical_fields = self.config.get("canonical_schemas", {}).get(target_schema_name, [])
        mapped_records = []
        
        for record in records:
            if not isinstance(record, dict):
                continue
            
            mapped = {}
            for field in canonical_fields:
                mapped[field] = record.get(field) or record.get(f"src_{field}")
            
            mapped_records.append(mapped)
            
        return {
            "success": True,
            "records_mapped": len(mapped_records),
            "target_schema": target_schema_name,
            "fields_aligned": canonical_fields
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA075SchemaMapping(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-075 Failed: {e}")
        return {"success": False, "error": str(e)}
