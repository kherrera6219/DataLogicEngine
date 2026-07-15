"""Process-local correlation/run context for requests and background tasks."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Iterator

_CORRELATION_ID: ContextVar[str] = ContextVar("dle_correlation_id", default="startup")
_RUN_ID: ContextVar[str | None] = ContextVar("dle_run_id", default=None)


def current_correlation_id() -> str:
    return _CORRELATION_ID.get()


def current_run_id() -> str | None:
    return _RUN_ID.get()


def bind_correlation_id(correlation_id: str) -> Token[str]:
    if not correlation_id:
        raise ValueError("correlation_id_required")
    return _CORRELATION_ID.set(correlation_id)


def reset_correlation_id(token: Token[str]) -> None:
    _CORRELATION_ID.reset(token)


def correlation_headers() -> dict[str, str]:
    correlation_id = current_correlation_id()
    return {
        "X-Correlation-ID": correlation_id,
        "X-Request-ID": correlation_id,
    }


@contextmanager
def bound_observation_context(
    correlation_id: str,
    *,
    run_id: str | None = None,
) -> Iterator[None]:
    correlation_token = _CORRELATION_ID.set(correlation_id)
    run_token = _RUN_ID.set(run_id)
    try:
        yield
    finally:
        _RUN_ID.reset(run_token)
        _CORRELATION_ID.reset(correlation_token)
