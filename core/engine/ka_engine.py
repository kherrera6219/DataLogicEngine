"""Compatibility adapter to the canonical Knowledge Algorithm controller.

This module retains the historical ``KAEngine`` API for legacy core callers.
It no longer loads a private registry or imports guessed implementation paths.
"""

from __future__ import annotations

import logging
import uuid
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


class KAEngine:
    """Legacy API facade backed exclusively by the canonical KA controller."""

    def __init__(
        self,
        config: dict[str, Any] | None = None,
        graph_manager: Any = None,
        memory_manager: Any = None,
    ):
        self.config = config or {}
        self.graph_manager = graph_manager
        self.memory_manager = memory_manager
        self.controller: CanonicalKAController = get_ka_controller()
        self.execution_history: list[dict[str, Any]] = []
        self.stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
        }
        self.ka_registry = {
            definition.canonical_id: self._definition_info(definition)
            for definition in self.controller.list_definitions()
        }
        logger.info(
            "KAEngine compatibility adapter initialized with %d canonical KAs",
            len(self.ka_registry),
        )

    @staticmethod
    def _definition_info(definition) -> dict[str, Any]:
        return {
            "ka_id": definition.canonical_id,
            "name": definition.name,
            "description": definition.purpose,
            "version": definition.version,
            "parameters": {},
            "hard_dependencies": ",".join(definition.contract.dependencies),
            "implementation_status": definition.implementation.status,
            "production_enabled": definition.admission.production_enabled,
            "manifest_version": definition.contract.version,
        }

    def register_algorithm(
        self,
        ka_id: str,
        name: str,
        description: str,
        module_path: str,
        class_name: str,
        version: str = "1.0.0",
        parameters: dict[str, Any] | None = None,
        hard_dependencies: str | None = None,
    ) -> bool:
        """Reject private runtime registration.

        New capabilities must enter through the reviewed canonical manifest.
        The signature remains for callers that need an explicit migration
        failure instead of an ``AttributeError``.
        """

        del name, description, module_path, class_name, version, parameters
        del hard_dependencies
        normalized = normalize_ka_id(ka_id)
        logger.warning(
            "Private KA registration rejected for %s; update the canonical manifest",
            normalized,
        )
        return False

    def get_algorithm_info(self, ka_id: str) -> dict[str, Any] | None:
        try:
            canonical_id = self.controller.manifest.resolve_id(ka_id)
        except KeyError:
            return None
        return dict(self.ka_registry[canonical_id])

    def list_algorithms(self) -> list[dict[str, Any]]:
        return [dict(self.ka_registry[key]) for key in sorted(self.ka_registry)]

    def execute_algorithm(
        self,
        ka_id: str,
        params: dict[str, Any] | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Return the historical execution record for compatibility callers."""
        result = self.execute_typed(
            ka_id,
            params,
            session_id=session_id,
            production_workflow=bool(
                (params or {}).get("_production_workflow", False)
            ),
        )
        return self._legacy_execution_record(result, params, session_id)

    def execute_typed(
        self,
        ka_id: str,
        params: dict[str, Any] | None = None,
        *,
        session_id: str | None = None,
        production_workflow: bool = False,
    ) -> KAExecutionResult:
        """Execute through the canonical typed boundary for internal callers."""
        payload = dict(params or {})
        production_workflow = bool(
            production_workflow
            or payload.pop("_production_workflow", False)
        )
        return self.controller.execute(
            KAExecutionRequest(
                ka_id=ka_id,
                input=payload,
                context=KAExecutionContext(session_id=session_id),
                mode=(
                    KAExecutionMode.PRODUCTION
                    if production_workflow
                    else KAExecutionMode.EVALUATION
                ),
            )
        )

    def _legacy_execution_record(
        self,
        result: KAExecutionResult,
        params: dict[str, Any] | None,
        session_id: str | None,
    ) -> dict[str, Any]:
        execution_id = (
            f"EXEC_{result.canonical_id}_{str(uuid.uuid4())[:8]}_"
            f"{int(datetime.now(UTC).timestamp())}"
        )
        payload = dict(params or {})
        payload.pop("_production_workflow", None)
        record = {
            "execution_id": execution_id,
            "ka_id": result.canonical_id,
            "session_id": session_id,
            "params": payload,
            "status": "completed" if result.success else "failed",
            "start_time": result.started_at.isoformat(),
            "end_time": result.completed_at.isoformat(),
            "duration_ms": result.duration_ms,
            "results": result.output,
            "error": result.error.message if result.error else None,
            "error_code": result.error.code.value if result.error else None,
            "trace_id": result.trace_id,
            "canonical_result": result.model_dump(
                mode="json",
                exclude_none=True,
            ),
        }
        self.execution_history.append(record)
        self.stats["total_executions"] += 1
        self.stats[
            "successful_executions"
            if result.success
            else "failed_executions"
        ] += 1
        return record

    def execute_pipeline(
        self,
        pipeline: list[dict[str, Any]],
        session_id: str | None = None,
    ) -> dict[str, Any]:
        pipeline_id = (
            f"PIPE_{str(uuid.uuid4())[:8]}_{int(datetime.now(UTC).timestamp())}"
        )
        started_at = datetime.now(UTC)
        result = {
            "pipeline_id": pipeline_id,
            "session_id": session_id,
            "start_time": started_at.isoformat(),
            "end_time": None,
            "duration_ms": None,
            "steps": [],
            "overall_status": "started",
            "error": None,
        }
        for index, step in enumerate(pipeline):
            ka_id = step.get("ka_id")
            if not ka_id:
                result["overall_status"] = "failed"
                result["error"] = (
                    f"Pipeline step {index + 1} missing required 'ka_id'"
                )
                break
            execution_result = self.execute_typed(
                ka_id,
                step.get("params", {}),
                session_id=session_id,
            )
            execution = self._legacy_execution_record(
                execution_result,
                step.get("params", {}),
                session_id,
            )
            result["steps"].append(execution)
            if (
                execution["status"] == "failed"
                and not step.get("continue_on_failure", False)
            ):
                result["overall_status"] = "failed"
                result["error"] = (
                    f"Pipeline failed at step {index + 1}: "
                    f"{execution.get('error')}"
                )
                break
        if result["overall_status"] != "failed":
            result["overall_status"] = "completed"
        completed_at = datetime.now(UTC)
        result["end_time"] = completed_at.isoformat()
        result["duration_ms"] = (
            completed_at - started_at
        ).total_seconds() * 1000
        return result

    def get_execution_history(
        self,
        ka_id: str | None = None,
        session_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        rows = self.execution_history
        if ka_id:
            normalized = normalize_ka_id(ka_id)
            rows = [row for row in rows if row.get("ka_id") == normalized]
        if session_id:
            rows = [
                row for row in rows if row.get("session_id") == session_id
            ]
        return [dict(row) for row in rows[offset : offset + limit]]

    def clear_execution_history(self) -> bool:
        self.execution_history = []
        return True

    def get_algorithm_stats(
        self, ka_id: str | None = None
    ) -> dict[str, Any]:
        if not ka_id:
            return dict(self.stats)
        normalized = normalize_ka_id(ka_id)
        rows = [
            row
            for row in self.execution_history
            if row.get("ka_id") == normalized
        ]
        successful = sum(row.get("status") == "completed" for row in rows)
        failed = sum(row.get("status") == "failed" for row in rows)
        durations = [float(row.get("duration_ms") or 0) for row in rows]
        return {
            "ka_id": normalized,
            "total_executions": len(rows),
            "successful_executions": successful,
            "failed_executions": failed,
            "success_rate": (
                (successful / len(rows)) * 100 if rows else 0
            ),
            "avg_duration_ms": (
                sum(durations) / len(durations) if durations else 0
            ),
        }
