"""
KA-061: Adversarial Input Shield
Purpose: Detect and neutralize malicious or adversarial inputs early in the pipeline to protect the knowledge engine.
"""
import json
import logging
import os
import re
from typing import Any

from pydantic import BaseModel, Field

from core.knowledge_algorithm.ka_base import KnowledgeAlgorithm

logger = logging.getLogger(__name__)


class KA061Input(BaseModel):
    query: str = Field(
        ...,
        description="The user query or content to scan for adversarial patterns",
    )
    dependency_results: dict[str, dict[str, Any]] = Field(default_factory=dict)


class KA061AdversarialInputShield(KnowledgeAlgorithm):
    """
    KA-061: Input sanitation and threat detection engine for neutralizing malicious queries.
    """
    input_schema = KA061Input

    def __init__(self, context: dict[str, Any]):
        super().__init__(context, None, None, None)
        self.ka_id = "KA-061"
        self.config = self._load_config()

    def _default_config(self) -> dict[str, Any]:
        return {
            "block_patterns": [r"(?i)DROP\s+TABLE", r"(?i)DELETE\s+FROM", r"(?i)<script>"],
            "enable_veto_on_threat": True,
        }

    def _load_config(self) -> dict[str, Any]:
        try:
            config_path = os.path.join(
                os.path.dirname(__file__),
                "config",
                "ka_61_config.json",
            )
            if os.path.exists(config_path):
                with open(config_path, encoding="utf-8") as f:
                    loaded = json.load(f) or {}
                    defaults = self._default_config()
                    configured_patterns = loaded.get("block_patterns") or []
                    return {
                        **defaults,
                        **loaded,
                        "block_patterns": list(
                            dict.fromkeys(defaults["block_patterns"] + configured_patterns)
                        ),
                    }
            return self._default_config()
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError):
            return self._default_config()

    def _run_logic(self, input_data: KA061Input) -> dict[str, Any]:
        validation = input_data.dependency_results.get("KA-004", {})
        query = str(validation.get("normalized_query") or input_data.query)
        self.log_execution_step(
            "Scanning for Adversarial Patterns",
            {"query_len": len(query)},
        )

        threats_detected = []
        block_patterns = self.config.get(
            "block_patterns",
            [r"(?i)DROP\s+TABLE", r"(?i)DELETE\s+FROM", r"(?i)<script>"],
        )
        for pattern in block_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                threats_detected.append(
                    {
                        "pattern": pattern,
                        "type": "MALICIOUS_SNIPPET",
                    }
                )

        is_blocked = len(threats_detected) > 0 and self.config.get(
            "enable_veto_on_threat",
            True,
        )
        return {
            "success": True,
            "blocked": is_blocked,
            "threats": threats_detected,
            "sanitized_query": query if not is_blocked else "[FILTERED]",
            "veto": is_blocked,
        }

    def _fallback_logic(
        self,
        input_data: KA061Input,
        error: Exception,
    ) -> dict[str, Any]:
        """Failsafe: Block the input if the scan fails."""
        self.logger.warning(f"Resilience Fallback for KA-061: {error!s}")
        return {
            "success": False,
            "blocked": True,
            "threats": [{"type": "SCAN_FAILURE_VETO"}],
            "sanitized_query": "[FILTERED_BY_FAILSAFE]",
            "veto": True,
        }


def run(context: dict[str, Any]) -> dict[str, Any]:
    # Base class .run() handles registry invocation and error wrapping
    algo = KA061AdversarialInputShield(context)
    return algo.run(context)
