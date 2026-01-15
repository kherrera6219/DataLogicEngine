"""
KA-023: Belief Decay
Purpose: Apply confidence decay to stale beliefs and knowledge entries based on their age.
"""
import logging
import json
import os
import math
from datetime import datetime
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

class KA023BeliefDecay(KnowledgeAlgorithm):
    """
    KA-023: Knowledge freshness and decay engine.
    """
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
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

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        knowledge_items = input_data.get("knowledge_items", [])
        reference_time = input_data.get("reference_time", datetime.now().isoformat())
        
        try:
            ref_dt = datetime.fromisoformat(reference_time)
        except ValueError:
            ref_dt = datetime.now()
            
        self.log_execution_step("Applying Belief Decay", {"item_count": len(knowledge_items)})
        
        half_life = self.config.get("decay_half_life_days", 180)
        floor = self.config.get("min_confidence_floor", 0.1)
        exclusions = self.config.get("categories_exclusion", [])
        
        updated_items = []
        for item in knowledge_items:
            # 1. Skip exclusions
            if item.get("category") in exclusions:
                updated_items.append({**item, "decay_applied": False})
                continue
                
            # 2. Compute age
            ts_str = item.get("timestamp")
            if not ts_str:
                updated_items.append({**item, "decay_applied": False})
                continue
                
            try:
                ts_dt = datetime.fromisoformat(ts_str)
                age_days = (ref_dt - ts_dt).total_seconds() / (24 * 3600)
                
                # 3. Calculate Decay (Exponential: C = C0 * 0.5 ^ (age / half_life))
                c0 = item.get("confidence", 1.0)
                decayed_c = max(floor, c0 * (0.5 ** (age_days / half_life)))
                
                updated_items.append({
                    **item,
                    "original_confidence": c0,
                    "confidence": decayed_c,
                    "decay_applied": True,
                    "age_days": round(age_days, 1)
                })
            except Exception:
                updated_items.append({**item, "decay_applied": False, "error": "Invalid timestamp"})
                
        return {
            "ka_id": "KA-023",
            "ka_name": "Belief Decay",
            "success": True,
            "processed_items": updated_items,
            "decay_stats": {
                "average_decay": sum(i.get("original_confidence", 0) - i.get("confidence", 0) for i in updated_items if i.get("decay_applied"))
            }
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA023BeliefDecay(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-023 Failed: {e}")
        return {"success": False, "error": str(e)}
