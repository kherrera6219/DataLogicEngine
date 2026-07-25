"""Strict helpers for internal consumers of canonical KA results."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from backend.knowledge_algorithms.contracts import KAExecutionResult


@runtime_checkable
class TypedKAExecutor(Protocol):
    """Internal execution boundary implemented by canonical KA facades."""

    def execute_typed(
        self,
        ka_id: str,
        input_data: dict[str, Any] | None = None,
        *,
        production_workflow: bool = False,
    ) -> KAExecutionResult: ...


def execute_required_ka(
    controller: Any,
    ka_id: str,
    payload: dict[str, Any],
    *,
    production_workflow: bool = False,
) -> KAExecutionResult:
    """Execute one required KA and reject legacy/failed result shapes."""
    execute_typed = getattr(controller, "execute_typed", None)
    if not callable(execute_typed):
        raise TypeError(
            f"{type(controller).__name__} does not implement execute_typed"
        )
    result = (
        execute_typed(
            ka_id,
            payload,
            production_workflow=True,
        )
        if production_workflow
        else execute_typed(ka_id, payload)
    )
    if not isinstance(result, KAExecutionResult):
        raise TypeError(f"{ka_id} returned a non-canonical execution result")
    result.require_output()
    return result


def require_output_field(
    result: KAExecutionResult,
    field: str,
) -> Any:
    """Read a required KA output field without an optimistic default."""
    output = result.require_output()
    if field not in output:
        raise RuntimeError(
            f"{result.canonical_id} output is missing required field {field!r}"
        )
    return output[field]
