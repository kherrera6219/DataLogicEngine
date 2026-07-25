"""One governed execution controller for all canonical Knowledge Algorithms."""

from __future__ import annotations

import importlib
import json
import time
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any
from uuid import uuid4

from pydantic import ValidationError

from backend.knowledge_algorithms.contracts import (
    KAExecutionError,
    KAExecutionMode,
    KAExecutionRequest,
    KAExecutionResult,
    KAExecutionState,
    KAFailureCode,
    KAOutcomeType,
)
from backend.knowledge_algorithms.manifest import (
    KADefinition,
    KAManifest,
    load_manifest,
)


class CanonicalKAController:
    """Resolve, admit, execute, and normalize every KA through one contract."""

    def __init__(self, manifest: KAManifest | None = None):
        self.manifest = manifest or load_manifest()

    def list_definitions(self) -> list[KADefinition]:
        return list(self.manifest.entries.values())

    def get_definition(
        self, ka_id: str, *, allow_scoped_alias: bool = False
    ) -> KADefinition:
        return self.manifest.get(
            ka_id, allow_scoped_alias=allow_scoped_alias
        )

    def execute(
        self,
        request: KAExecutionRequest | dict[str, Any],
        *,
        allow_scoped_alias: bool = False,
    ) -> KAExecutionResult:
        if not isinstance(request, KAExecutionRequest):
            try:
                request = KAExecutionRequest.model_validate(request)
            except ValidationError as exc:
                return self._request_error(exc)

        started_at = datetime.now(UTC)
        started = time.perf_counter()
        trace_id = str(uuid4())
        try:
            definition = self.get_definition(
                request.ka_id, allow_scoped_alias=allow_scoped_alias
            )
        except KeyError:
            return self._failure(
                request=request,
                canonical_id=request.ka_id,
                version="unknown",
                started_at=started_at,
                started=started,
                trace_id=trace_id,
                state=KAExecutionState.INVALID,
                outcome=KAOutcomeType.INVALID_INPUT,
                code=KAFailureCode.NOT_FOUND,
                message="Knowledge Algorithm was not found.",
            )

        if request.context.cancellation_requested:
            return self._failure(
                request=request,
                definition=definition,
                started_at=started_at,
                started=started,
                trace_id=trace_id,
                state=KAExecutionState.CANCELLED,
                outcome=KAOutcomeType.CANCELLED,
                code=KAFailureCode.CANCELLED,
                message="Knowledge Algorithm execution was cancelled.",
            )
        if (
            request.context.deadline_at is not None
            and request.context.deadline_at <= datetime.now(UTC)
        ):
            return self._failure(
                request=request,
                definition=definition,
                started_at=started_at,
                started=started,
                trace_id=trace_id,
                state=KAExecutionState.TIMED_OUT,
                outcome=KAOutcomeType.TIMEOUT,
                code=KAFailureCode.DEADLINE_EXCEEDED,
                message="Knowledge Algorithm execution deadline was exceeded.",
            )
        if (
            request.mode == KAExecutionMode.PRODUCTION
            and not definition.admission.production_enabled
        ):
            return self._failure(
                request=request,
                definition=definition,
                started_at=started_at,
                started=started,
                trace_id=trace_id,
                state=KAExecutionState.BLOCKED,
                outcome=KAOutcomeType.BLOCKED_POLICY,
                code=KAFailureCode.NOT_PRODUCTION_QUALIFIED,
                message="Knowledge Algorithm is not qualified for production.",
            )
        if definition.implementation.entrypoint is None:
            return self._failure(
                request=request,
                definition=definition,
                started_at=started_at,
                started=started,
                trace_id=trace_id,
                state=KAExecutionState.UNAVAILABLE,
                outcome=KAOutcomeType.UNAVAILABLE_PREREQUISITE,
                code=KAFailureCode.IMPLEMENTATION_UNAVAILABLE,
                message="Knowledge Algorithm implementation is unavailable.",
            )
        if request.mode == KAExecutionMode.DRY_RUN:
            return self._success(
                request=request,
                definition=definition,
                started_at=started_at,
                started=started,
                trace_id=trace_id,
                output={
                    "planned": True,
                    "entrypoint": definition.implementation.entrypoint.model_dump(),
                    "dependencies": definition.contract.dependencies,
                    "effect_class": definition.contract.effect_class,
                },
                adapter="dry_run",
            )

        try:
            raw = self._invoke(definition, request.input)
            return self._normalize_result(
                request=request,
                definition=definition,
                raw=raw,
                started_at=started_at,
                started=started,
                trace_id=trace_id,
            )
        except ValidationError as exc:
            return self._failure(
                request=request,
                definition=definition,
                started_at=started_at,
                started=started,
                trace_id=trace_id,
                state=KAExecutionState.INVALID,
                outcome=KAOutcomeType.INVALID_INPUT,
                code=KAFailureCode.INVALID_INPUT,
                message="Knowledge Algorithm input is invalid.",
                details={"validation_errors": exc.errors()},
            )
        except Exception as exc:  # noqa: BLE001 - canonical failure boundary
            return self._failure(
                request=request,
                definition=definition,
                started_at=started_at,
                started=started,
                trace_id=trace_id,
                state=KAExecutionState.FAILED,
                outcome=KAOutcomeType.INTERNAL_FAILURE,
                code=KAFailureCode.EXECUTION_FAILED,
                message="Knowledge Algorithm execution failed.",
                details={"exception_type": type(exc).__name__, "exception": str(exc)},
            )

    def execute_legacy(
        self,
        ka_id: str,
        input_data: dict[str, Any] | None = None,
        *,
        production_workflow: bool = False,
    ) -> dict[str, Any]:
        request = KAExecutionRequest(
            ka_id=ka_id,
            input=input_data or {},
            mode=(
                KAExecutionMode.PRODUCTION
                if production_workflow
                else KAExecutionMode.EVALUATION
            ),
        )
        result = self.execute(request)
        payload = result.model_dump(mode="json", exclude_none=True)
        return {
            "success": result.success,
            "ka_id": result.canonical_id,
            "output": result.output,
            "execution_time_ms": result.duration_ms,
            "trace_id": result.trace_id,
            "canonical_result": payload,
            **(
                {
                    "error": result.error.message,
                    "error_code": result.error.code.value,
                }
                if result.error
                else {}
            ),
        }

    @staticmethod
    def _invoke(definition: KADefinition, input_data: dict[str, Any]) -> Any:
        entrypoint = definition.implementation.entrypoint
        if entrypoint is None:
            raise RuntimeError("implementation entrypoint is unavailable")
        module = importlib.import_module(entrypoint.module)
        if entrypoint.adapter == "module_run":
            return getattr(module, entrypoint.callable)(input_data)
        if entrypoint.adapter == "class_execute":
            if not entrypoint.class_name:
                raise RuntimeError("class_execute entrypoint has no class name")
            implementation_class = getattr(module, entrypoint.class_name)
            instance = implementation_class({})
            return getattr(instance, entrypoint.callable)(input_data)
        raise RuntimeError(f"Unsupported KA adapter: {entrypoint.adapter}")

    def _normalize_result(
        self,
        *,
        request: KAExecutionRequest,
        definition: KADefinition,
        raw: Any,
        started_at: datetime,
        started: float,
        trace_id: str,
    ) -> KAExecutionResult:
        if not isinstance(raw, dict):
            return self._failure(
                request=request,
                definition=definition,
                started_at=started_at,
                started=started,
                trace_id=trace_id,
                state=KAExecutionState.FAILED,
                outcome=KAOutcomeType.INTERNAL_FAILURE,
                code=KAFailureCode.INVALID_IMPLEMENTATION_RESULT,
                message="Knowledge Algorithm returned an invalid result.",
            )
        success = bool(raw.get("success", raw.get("ok", True)))
        output = raw.get("output")
        if not isinstance(output, dict):
            output = dict(raw)
        if not success:
            details = {
                "legacy_error": raw.get("error"),
                "legacy_errors": raw.get("errors"),
            }
            return self._failure(
                request=request,
                definition=definition,
                started_at=started_at,
                started=started,
                trace_id=trace_id,
                state=KAExecutionState.FAILED,
                outcome=KAOutcomeType.INTERNAL_FAILURE,
                code=KAFailureCode.EXECUTION_FAILED,
                message="Knowledge Algorithm reported failure.",
                details=details,
            )
        return self._success(
            request=request,
            definition=definition,
            started_at=started_at,
            started=started,
            trace_id=trace_id,
            output=output,
            adapter=definition.implementation.entrypoint.adapter,
        )

    def _success(
        self,
        *,
        request: KAExecutionRequest,
        definition: KADefinition,
        started_at: datetime,
        started: float,
        trace_id: str,
        output: dict[str, Any],
        adapter: str,
    ) -> KAExecutionResult:
        return KAExecutionResult(
            canonical_id=definition.canonical_id,
            ka_version=definition.version,
            manifest_version=self.manifest.manifest_version,
            state=KAExecutionState.SUCCEEDED,
            outcome_type=KAOutcomeType.VALUE,
            success=True,
            output=_json_safe(output),
            request_id=request.context.request_id,
            run_id=request.context.run_id,
            trace_id=trace_id,
            started_at=started_at,
            completed_at=datetime.now(UTC),
            duration_ms=(time.perf_counter() - started) * 1000,
            implementation_adapter=adapter,
        )

    def _failure(
        self,
        *,
        request: KAExecutionRequest,
        started_at: datetime,
        started: float,
        trace_id: str,
        state: KAExecutionState,
        outcome: KAOutcomeType,
        code: KAFailureCode,
        message: str,
        definition: KADefinition | None = None,
        canonical_id: str | None = None,
        version: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> KAExecutionResult:
        return KAExecutionResult(
            canonical_id=canonical_id
            or (definition.canonical_id if definition else request.ka_id),
            ka_version=version
            or (definition.version if definition else "unknown"),
            manifest_version=self.manifest.manifest_version,
            state=state,
            outcome_type=outcome,
            success=False,
            error=KAExecutionError(
                code=code,
                message=message,
                internal_details=details or {},
            ),
            request_id=request.context.request_id,
            run_id=request.context.run_id,
            trace_id=trace_id,
            started_at=started_at,
            completed_at=datetime.now(UTC),
            duration_ms=(time.perf_counter() - started) * 1000,
            implementation_adapter=(
                definition.implementation.entrypoint.adapter
                if definition and definition.implementation.entrypoint
                else None
            ),
        )

    def _request_error(self, exc: ValidationError) -> KAExecutionResult:
        now = datetime.now(UTC)
        return KAExecutionResult(
            canonical_id="unknown",
            ka_version="unknown",
            manifest_version=self.manifest.manifest_version,
            state=KAExecutionState.INVALID,
            outcome_type=KAOutcomeType.INVALID_INPUT,
            success=False,
            error=KAExecutionError(
                code=KAFailureCode.INVALID_INPUT,
                message="Knowledge Algorithm request is invalid.",
                internal_details={"validation_errors": exc.errors()},
            ),
            request_id="unknown",
            run_id="unknown",
            trace_id=str(uuid4()),
            started_at=now,
            completed_at=now,
            duration_ms=0.0,
        )


def _json_safe(value: Any) -> Any:
    try:
        return json.loads(json.dumps(value, default=str))
    except (TypeError, ValueError):
        return {"value": str(value)}


@lru_cache(maxsize=1)
def get_ka_controller() -> CanonicalKAController:
    return CanonicalKAController()
