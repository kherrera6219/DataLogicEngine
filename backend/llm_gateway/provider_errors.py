"""Typed provider failure classification and replay/retry policy."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class ProviderFailureClass(StrEnum):
    INVALID_KEY = "invalid_key"
    UNAUTHORIZED_MODEL = "unauthorized_model"
    INVALID_MODEL = "invalid_model"
    QUOTA_EXHAUSTED = "quota_exhausted"
    BILLING_SUSPENDED = "billing_suspended"
    RATE_LIMITED = "rate_limited"
    NETWORK = "network"
    PROVIDER_OUTAGE = "provider_outage"
    TIMEOUT = "timeout"
    POLICY_BLOCK = "policy_block"
    MALFORMED_RESPONSE = "malformed_response"
    CANCELLED = "cancelled"
    PERSISTENCE = "persistence"
    INTERNAL = "internal_error"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ClassifiedProviderFailure:
    failure_class: ProviderFailureClass
    retryable: bool
    replayable: bool
    http_status: int | None = None
    retry_after_seconds: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "class": self.failure_class.value,
            "retryable": self.retryable,
            "replayable": self.replayable,
            "http_status": self.http_status,
            "retry_after_seconds": self.retry_after_seconds,
        }


def _status_code(error: Any) -> int | None:
    for attribute in ("status_code", "code"):
        value = getattr(error, attribute, None)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    response = getattr(error, "response", None)
    value = getattr(response, "status_code", None)
    return value if isinstance(value, int) else None


def _retry_after(error: Any) -> float | None:
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", None) or getattr(error, "headers", None)
    if not headers:
        return None
    value = headers.get("retry-after") or headers.get("Retry-After")
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return None


def classify_provider_failure(error: Any) -> ClassifiedProviderFailure:
    """Classify an exception or error string; unknown failures fail closed."""
    status = _status_code(error)
    name = type(error).__name__.lower()
    message = str(error or "").lower()
    combined = f"{name} {message}"

    def result(
        failure_class: ProviderFailureClass,
        *,
        retryable: bool = False,
        replayable: bool = False,
    ) -> ClassifiedProviderFailure:
        return ClassifiedProviderFailure(
            failure_class,
            retryable=retryable,
            replayable=replayable,
            http_status=status,
            retry_after_seconds=_retry_after(error),
        )

    if "cancel" in combined:
        return result(ProviderFailureClass.CANCELLED)
    if "timeout" in combined or "timed out" in combined or status == 504:
        return result(ProviderFailureClass.TIMEOUT, retryable=True, replayable=True)
    if status == 401 or any(marker in combined for marker in ("invalid api key", "incorrect api key", "authentication")):
        return result(ProviderFailureClass.INVALID_KEY)
    if any(marker in combined for marker in ("billing suspended", "billing inactive", "billing disabled")):
        return result(ProviderFailureClass.BILLING_SUSPENDED)
    if any(marker in combined for marker in ("insufficient_quota", "quota exceeded", "quota exhausted")):
        return result(ProviderFailureClass.QUOTA_EXHAUSTED)
    if status == 429 or any(marker in combined for marker in ("rate limit", "rate_limit", "resource exhausted")):
        return result(ProviderFailureClass.RATE_LIMITED)
    if status == 403 or any(marker in combined for marker in ("not entitled", "model access", "permission denied")):
        return result(ProviderFailureClass.UNAUTHORIZED_MODEL)
    if status == 404 or any(
        marker in combined
        for marker in (
            "model not found",
            "invalid model",
            "unsupported model",
            "not found for api version",
            "not supported for generatecontent",
        )
    ):
        return result(ProviderFailureClass.INVALID_MODEL)
    if any(marker in combined for marker in ("policy block", "blocked by security policy", "content filter")):
        return result(ProviderFailureClass.POLICY_BLOCK)
    if any(marker in combined for marker in ("malformed response", "empty response", "missing output")):
        return result(ProviderFailureClass.MALFORMED_RESPONSE)
    if status in {500, 502, 503} or any(marker in combined for marker in ("service unavailable", "provider outage", "overloaded")):
        return result(ProviderFailureClass.PROVIDER_OUTAGE, retryable=True, replayable=True)
    if any(
        marker in combined
        for marker in (
            "connectionerror",
            "connecterror",
            "connection reset",
            "connection aborted",
            "dns",
            "name resolution",
            "tls",
            "ssl",
            "network",
        )
    ):
        return result(ProviderFailureClass.NETWORK, retryable=True, replayable=True)
    return result(ProviderFailureClass.UNKNOWN)
