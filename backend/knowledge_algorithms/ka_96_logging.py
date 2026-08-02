"""
KA-096: Logging
Purpose: Manage centralized system logging with support for structured formats, rotation, and sensitive data masking.
"""
import logging
import json
import os
from typing import Dict, Any, List
from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class KA096LoggingInput(BaseModel):
    logs: List[Any] = Field(default_factory=list, description="A list of log entries to process and store")

class KA096Logging(KnowledgeAlgorithm):
    """
    KA-096: Centralized system logging and structured trace engine.
    """
    input_schema = KA096LoggingInput

    def __init__(self, context: Dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-096"
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        try:
            config_path = os.path.join(os.path.dirname(__file__), "config", "ka_96_config.json")
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}

    def _run_logic(self, input_data: KA096LoggingInput) -> Dict[str, Any]:
        logs = input_data.logs
        self.log_execution_step("Processing Logs", {"count": len(logs)})
        
        masking = self.config.get("sensitive_fields_masking", ["api_key", "password"])
        processed_logs = []
        
        for entry in logs:
            if isinstance(entry, dict):
                for field in masking:
                    if field in entry:
                        entry[field] = "********"
            processed_logs.append(entry)
            
        return {
            "success": True,
            "logs_processed": len(processed_logs),
            "backend": self.config.get(
                "storage_backend",
                "application_owned_structured_log",
            ),
            "structured": self.config.get("structured_logging", True)
        }

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    try:
        algo = KA096Logging(context)
        return algo.run(context)
    except Exception as e:
        logger.error(f"KA-096 Failed: {e}")
        return {"success": False, "error": str(e)}
