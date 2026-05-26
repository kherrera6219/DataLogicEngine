"""
KA-023: Belief Decay
Purpose: Apply confidence decay to stale beliefs and knowledge entries based on their age.
"""
import logging
import json
import os
import math
from datetime import datetime, UTC
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA023Input(BaseModel):
    knowledge_items: List[Dict[str, Any]] = Field(default_factory=list, description="Knowledge entries with timestamps and confidence")
    reference_time: str = Field(None, description="ISO reference time for decay calculation")
    domain: str = Field("general", description="Domain-specific decay profile")

class KA023BeliefDecay(KnowledgeAlgorithm):
    """
    KA-023: Knowledge freshness and decay engine based on half-life configurations.
    """
    input_schema = KA023Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-023"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_23_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA023Input) -> Dict[str, Any]:
        knowledge_items = input_data.knowledge_items
        reference_time = input_data.reference_time or datetime.now(UTC).isoformat()
        
        try:
            ref_dt = datetime.fromisoformat(reference_time)
        except ValueError:
            ref_dt = datetime.now(UTC)
            
        self.log_execution_step("Applying Belief Decay", {"item_count": len(knowledge_items)})
        
        lambdas = self.config.get("domain_lambdas", {"healthcare": 0.05, "finance": 0.02, "general": 0.001})
        default_lambda = float(lambdas.get(input_data.domain, lambdas.get("general", 0.001)))
        floor = self.config.get("min_confidence_floor", 0.1)
        exclusions = self.config.get("categories_exclusion", [])
        
        updated_items = []
        for item in knowledge_items:
            if item.get("category") in exclusions:
                updated_items.append({**item, "decay_applied": False})
                continue
            ts_str = item.get("timestamp")
            if not ts_str:
                updated_items.append({**item, "decay_applied": False})
                continue
            try:
                ts_dt = datetime.fromisoformat(ts_str)
                if ts_dt.tzinfo is None and ref_dt.tzinfo is not None:
                    ts_dt = ts_dt.replace(tzinfo=ref_dt.tzinfo)
                age_days = max(0.0, (ref_dt - ts_dt).total_seconds() / (24 * 3600))
                c0 = item.get("confidence", 1.0)
                item_domain = str(item.get("domain") or input_data.domain or "general")
                decay_lambda = float(lambdas.get(item_domain, default_lambda))
                decayed_c = max(floor, c0 * math.exp(-decay_lambda * age_days))
                updated_items.append({
                    **item,
                    "original_confidence": c0,
                    "confidence": decayed_c,
                    "decay_applied": True,
                    "decay_lambda": decay_lambda,
                    "age_days": round(age_days, 1)
                })
            except Exception:
                updated_items.append({**item, "decay_applied": False, "error": "Invalid timestamp"})
                
        return {
            "success": True,
            "processed_items": updated_items,
            "decay_stats": {
                "average_loss": sum(i.get("original_confidence", 0) - i.get("confidence", 0) for i in updated_items if i.get("decay_applied")),
                "domain_lambdas": lambdas,
            }
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA023BeliefDecay(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-023 Failed: {e}")
        return {"success": False, "error": str(e)}
