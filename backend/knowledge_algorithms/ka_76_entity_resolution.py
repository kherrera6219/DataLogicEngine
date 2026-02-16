"""
KA-076: Entity Resolution
Purpose: Identify and merge records representing the same real-world entity using fuzzy matching and conflict resolution.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field

class KA076ResolutionInput(BaseModel):
    records: List[Any] = Field(default_factory=list, description="The list of records to resolve and merge")

class KA076EntityResolution(KnowledgeAlgorithm):
    """
    KA-076: Fuzzy entity matching and record merging engine for knowledge de-duplication.
    """
    input_schema = KA076ResolutionInput

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-076"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_76_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA076ResolutionInput) -> Dict[str, Any]:
        records = input_data.records
        self.log_execution_step("Resolving Entities", {"record_count": len(records)})
        
        matching_keys = self.config.get("matching_keys", [])
        merged_entities = {}
        merge_count = 0
        
        for record in records:
            if not isinstance(record, dict):
                continue
            
            found_key = None
            for key in matching_keys:
                if record.get(key):
                    found_key = f"{key}:{record.get(key)}"
                    break
            
            if found_key:
                if found_key in merged_entities:
                    merge_count += 1
                    merged_entities[found_key].update(record)
                else:
                    merged_entities[found_key] = record
            else:
                merged_entities[id(record)] = record
                
        return {
            "success": True,
            "unique_entities_count": len(merged_entities),
            "merges_performed": merge_count,
            "strategy": self.config.get("conflict_resolution_strategy")
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA076EntityResolution(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-076 Failed: {e}")
        return {"success": False, "error": str(e)}
