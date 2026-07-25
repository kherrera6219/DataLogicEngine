"""Compatibility loader backed by the canonical KA controller.

The former directory scanner guessed class names and maintained a private
runtime registry. This adapter preserves the historical API without a second
execution authority.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from backend.knowledge_algorithms.controller import (
    CanonicalKAController,
    get_ka_controller,
)
from backend.knowledge_algorithms.manifest import normalize_ka_id

logger = logging.getLogger(__name__)


class KALoader:
    """Legacy ``execute_ka`` facade over the canonical controller."""

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        graph_manager: Any = None,
        memory_manager: Any = None,
        united_system_manager: Any = None,
    ):
        self.config = config or {}
        self.gm = graph_manager
        self.smm = memory_manager
        self.usm = united_system_manager
        self.default_ka_confidence_threshold = float(
            self.config.get("default_ka_confidence_threshold", 0.7)
        )
        self.controller: CanonicalKAController = get_ka_controller()
        self.ka_classes = {
            definition.canonical_id: definition.implementation.entrypoint
            for definition in self.controller.list_definitions()
            if definition.implementation.entrypoint is not None
        }
        logger.info(
            "KALoader compatibility adapter initialized with %d implementations",
            len(self.ka_classes),
        )

    def execute_ka(
        self,
        ka_id: int | str,
        input_data: dict[str, Any],
        session_id: str | None = None,
        pass_num: int | None = None,
        layer_num: int | None = None,
    ) -> dict[str, Any]:
        canonical_id = normalize_ka_id(str(ka_id))
        started_at = datetime.now(UTC)
        result = self.controller.execute_legacy(canonical_id, input_data)
        success = bool(result.get("success"))
        output = result.get("output", {})
        response = {
            "status": "success" if success else "error",
            "ka_id": result.get("ka_id", canonical_id),
            "ka_confidence": float(
                output.get("confidence", self.default_ka_confidence_threshold)
                if isinstance(output, dict)
                else self.default_ka_confidence_threshold
            ),
            "findings": output if isinstance(output, dict) else {},
            "error_message": result.get("error"),
            "error_code": result.get("error_code"),
            "execution_time": (
                datetime.now(UTC) - started_at
            ).total_seconds(),
            "trace_id": result.get("trace_id"),
            "canonical_result": result.get("canonical_result"),
        }
        if session_id and self.smm is not None:
            self._record_memory(
                session_id=session_id,
                pass_num=pass_num,
                layer_num=layer_num,
                ka_id=response["ka_id"],
                input_data=input_data,
                result=response,
            )
        return response

    def _record_memory(
        self,
        *,
        session_id: str,
        pass_num: int | None,
        layer_num: int | None,
        ka_id: str,
        input_data: dict[str, Any],
        result: dict[str, Any],
    ) -> None:
        try:
            self.smm.add_memory_entry(
                session_id=session_id,
                pass_num=pass_num if pass_num is not None else 0,
                layer_num=layer_num if layer_num is not None else 0,
                entry_type="ka_execution_log",
                content={
                    "ka_id": ka_id,
                    "input_data": input_data,
                    "result": result,
                    "execution_time": result["execution_time"],
                },
                confidence=result["ka_confidence"],
            )
        except Exception as exc:  # noqa: BLE001 - optional legacy memory adapter
            logger.warning("Could not persist legacy KA memory record: %s", exc)

    def get_available_kas(self) -> list[str]:
        return sorted(self.ka_classes)
