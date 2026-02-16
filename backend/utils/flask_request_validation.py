"""
Flask helpers for centralized request-schema validation.
"""

from __future__ import annotations

from functools import wraps
from typing import Optional, Type, TypeVar

from flask import g, request
from pydantic import BaseModel

from backend.utils.request_validation import validate_pydantic_payload


TModel = TypeVar("TModel", bound=BaseModel)


def validate_json_payload(schema: Type[TModel]):
    """Validate request JSON using a Pydantic schema and store typed payload in flask.g."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            payload = request.get_json(silent=True)
            validated, error_response = validate_pydantic_payload(schema, payload)
            if error_response is not None:
                return error_response

            g.validated_payload = validated
            return func(*args, **kwargs)

        return wrapper

    return decorator


def get_validated_payload(schema: Type[TModel]) -> Optional[TModel]:
    payload = getattr(g, "validated_payload", None)
    if isinstance(payload, schema):
        return payload
    return None

