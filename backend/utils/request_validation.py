"""
Request payload validation helpers.
"""

from __future__ import annotations

from typing import Any, Optional, Type

from pydantic import BaseModel, ValidationError

from backend.utils.responses import validation_error


def validate_pydantic_payload(
    schema: Type[BaseModel],
    payload: Any,
) -> tuple[Optional[BaseModel], Optional[tuple]]:
    """Validate payload and convert validation errors to standardized API response tuples."""
    try:
        validated = schema.model_validate(payload or {})
        return validated, None
    except ValidationError as exc:
        field_errors: dict[str, list[str]] = {}
        for err in exc.errors():
            loc = err.get("loc", ())
            field = ".".join(str(part) for part in loc) or "body"
            field_errors.setdefault(field, []).append(str(err.get("msg", "Invalid value")))
        return None, validation_error(field_errors)
