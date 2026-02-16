"""
KA-015: Temporal Reasoning
Purpose: Evaluate the temporal validity and relevance of facts across time windows.
"""
import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)

from pydantic import BaseModel, Field

class KA015Input(BaseModel):
    facts: List[Dict[str, Any]] = Field(default_factory=list, description="List of facts with timestamps to evaluate")
    reference_time: str = Field(None, description="ISO reference time for evaluation")

class KA015TemporalReasoning(KnowledgeAlgorithm):
    """
    KA-015: Filters and scores knowledge based on time stamps and validity windows.
    """
    input_schema = KA015Input

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-015"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_15_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA015Input) -> Dict[str, Any]:
        facts = input_data.facts
        reference_time_str = input_data.reference_time or datetime.now().isoformat()
        
        try:
            ref_time = datetime.fromisoformat(reference_time_str)
        except ValueError:
            ref_time = datetime.now()
            
        self.log_execution_step("Temporal Analysis", {"fact_count": len(facts), "ref_time": ref_time.isoformat()})
        
        processed_facts = []
        for fact in facts:
            validity = self._check_validity(fact, ref_time)
            processed_facts.append({
                **fact,
                "temporal_validity": validity
            })
            
        return {
            "success": True,
            "ref_time": ref_time.isoformat(),
            "results": processed_facts,
            "expired_count": sum(1 for f in processed_facts if f["temporal_validity"]["status"] == "expired")
        }

    def _check_validity(self, fact: Dict[str, Any], ref_time: datetime) -> Dict[str, Any]:
        ts_str = fact.get("timestamp")
        expires_str = fact.get("expires_at")
        if not ts_str:
            return {"status": "unknown", "msg": "No timestamp provided"}
            
        try:
            ts = datetime.fromisoformat(ts_str)
            if expires_str:
                expires_at = datetime.fromisoformat(expires_str)
            else:
                duration = self.config.get("default_validity_days", 365)
                expires_at = ts + timedelta(days=duration)
                
            if ref_time > expires_at:
                return {"status": "expired", "relative_age_days": (ref_time - ts).days}
            elif ref_time < ts:
                 return {"status": "future_dated", "starts_in_days": (ts - ref_time).days}
            else:
                 return {"status": "valid", "remaining_days": (expires_at - ref_time).days}
        except Exception as e:
            return {"status": "error", "error": str(e)}

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA015TemporalReasoning(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-015 Failed: {e}")
        return {"success": False, "error": str(e)}
