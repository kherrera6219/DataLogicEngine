"""
KA-017: Spatial/Jurisdiction Mapping
Purpose: Resolve and map geographies/jurisdictions to applicable regulations and constraints.
"""
import logging
import json
import os
from typing import Dict, Any
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA017Input(BaseModel):
    location: str = Field("GLOBAL", description="The geographical location to map")
    entity_scope: str = Field("GLOBAL", description="The scope of the entity")

class KA017SpatialMapping(KnowledgeAlgorithm):
    """
    KA-017: Spatial and Jurisdiction mapping engine.
    """
    input_schema = KA017Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-017"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_17_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA017Input) -> Dict[str, Any]:
        location_meta = input_data.location
        entity_scope = input_data.entity_scope
        
        self.log_execution_step("Jurisdiction Resolution", {"location": location_meta, "scope": entity_scope})
        
        jurisdictions_config = self.config.get("jurisdictions", {})
        primary = location_meta.upper()
        if primary not in jurisdictions_config:
            primary = "GLOBAL"
            
        details = jurisdictions_config.get(primary, {})
        
        return {
            "success": True,
            "resolved_jurisdiction": primary,
            "sub_jurisdictions": details.get("sub_jurisdictions", []),
            "applicable_regulations": details.get("primary_regulations", []),
            "metadata": {
                "input_location": location_meta,
                "input_scope": entity_scope
            }
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA017SpatialMapping(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-017 Failed: {e}")
        return {"success": False, "error": str(e)}
