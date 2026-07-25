"""Compatibility loader backed by the canonical KA controller.

The former directory scanner guessed class names and maintained a private
runtime registry. This adapter preserves the historical API without a second
execution authority.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from backend.knowledge_algorithms.contracts import (
    KAExecutionContext,
    KAExecutionMode,
    KAExecutionRequest,
    KAExecutionResult,
)
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
            self.config.get("default_ka_confidence_threshold", 0.0)
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
        """Return the historical loader envelope for compatibility callers."""
        started_at = datetime.now(UTC)
        result = self.execute_typed(
            ka_id,
            input_data,
            session_id=session_id,
            pass_num=pass_num,
            layer_num=layer_num,
        )
        output = result.output
        measured_confidence = output.get("confidence")
        confidence = (
            float(measured_confidence)
            if isinstance(measured_confidence, (int, float))
            else 0.0
        )
        return {
            "status": "success" if result.success else "error",
            "ka_id": result.canonical_id,
            "ka_confidence": confidence,
            "findings": output,
            "error_message": result.error.message if result.error else None,
            "error_code": result.error.code.value if result.error else None,
            "execution_time": (
                datetime.now(UTC) - started_at
            ).total_seconds(),
            "trace_id": result.trace_id,
            "canonical_result": result.model_dump(
                mode="json",
                exclude_none=True,
            ),
        }

    def execute_typed(
        self,
        ka_id: int | str,
        input_data: dict[str, Any],
        *,
        session_id: str | None = None,
        pass_num: int | None = None,
        layer_num: int | None = None,
        production_workflow: bool = False,
    ) -> KAExecutionResult:
        """Execute and optionally persist one canonical typed KA result."""
        canonical_id = normalize_ka_id(str(ka_id))
        result = self.controller.execute(
            KAExecutionRequest(
                ka_id=canonical_id,
                input=input_data,
                context=KAExecutionContext(
                    session_id=session_id,
                    layer=str(layer_num) if layer_num is not None else None,
                ),
                mode=(
                    KAExecutionMode.PRODUCTION
                    if production_workflow
                    else KAExecutionMode.EVALUATION
                ),
            )
        )
        if session_id and self.smm is not None:
            self._record_memory(
                session_id=session_id,
                pass_num=pass_num,
                layer_num=layer_num,
                ka_id=result.canonical_id,
                input_data=input_data,
                result=result,
            )
        return result

    def _record_memory(
        self,
        *,
        session_id: str,
        pass_num: int | None,
        layer_num: int | None,
        ka_id: str,
        input_data: dict[str, Any],
        result: KAExecutionResult,
    ) -> None:
        try:
            output = result.output
            measured_confidence = output.get("confidence")
            confidence = (
                float(measured_confidence)
                if isinstance(measured_confidence, (int, float))
                else 0.0
            )
            self.smm.add_memory_entry(
                session_id=session_id,
                pass_num=pass_num if pass_num is not None else 0,
                layer_num=layer_num if layer_num is not None else 0,
                entry_type="ka_execution_log",
                content={
                    "ka_id": ka_id,
                    "input_data": input_data,
                    "result": result.model_dump(
                        mode="json",
                        exclude_none=True,
                    ),
                    "execution_time": result.duration_ms / 1000,
                },
                confidence=confidence,
            )
        except Exception as exc:  # noqa: BLE001 - optional legacy memory adapter
            logger.warning("Could not persist legacy KA memory record: %s", exc)

    def get_available_kas(self) -> list[str]:
        return sorted(self.ka_classes)
