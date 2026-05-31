"""
KA-095: Alerting
Purpose: Detect critical system states and trigger real-time alerts with escalation and deduplication logic.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA095AlertInput(BaseModel):
    event: str = Field(..., description="The system event identifier")
    level: str = Field("error", description="The alert level (e.g., info, warning, error, critical)")
    recent_events: List[str] = Field(default_factory=list, description="List of recently triggered alert events for deduplication")


class KA095Alerting(KnowledgeAlgorithm):
    """
    KA-095: System event alerting and multi-level escalation engine.
    """
    input_schema = KA095AlertInput

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-095"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_95_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA095AlertInput) -> Dict[str, Any]:
        event = input_data.event
        level = input_data.level
        self.log_execution_step("Evaluating Alert Event", {"event": event, "level": level})
        
        # Deduplication check
        is_deduplicated = event in input_data.recent_events
        
        # Determine escalation target based on level
        escalation_config = self.config.get("escalation_policy")
        if isinstance(escalation_config, dict):
            policy = escalation_config.get(level.lower(), "standard_ops")
        elif isinstance(escalation_config, str):
            policy = escalation_config
        else:
            default_map = {
                "info": "none",
                "warning": "slack",
                "error": "pagerduty",
                "critical": "executive_pager"
            }
            policy = default_map.get(level.lower(), "standard_ops")
        
        return {
            "success": True,
            "alert_triggered": not is_deduplicated,
            "active_alert_id": f"ALRT_{os.urandom(4).hex().upper()}",
            "escalation_policy": policy,
            "deduplicated": is_deduplicated,
            "alert_details": {
                "event": event,
                "level": level,
                "urgency": "HIGH" if level.lower() in ["error", "critical"] else "LOW"
            }
        }


def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA095Alerting(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-095 Failed: {e}")
        return {"success": False, "error": str(e)}
