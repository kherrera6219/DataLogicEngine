"""Provider-neutral completion disposition carried through governed execution."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any


class CompletionDisposition(StrEnum):
    COMPLETE = "complete"
    LENGTH_LIMITED = "length_limited"
    SAFETY_BLOCKED = "safety_blocked"
    PROVIDER_INCOMPLETE = "provider_incomplete"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ProviderCompletion:
    """Bounded provider completion metadata with no inferred success."""

    disposition: CompletionDisposition
    native_reason: str | None = None
    response_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "disposition",
            CompletionDisposition(self.disposition),
        )
        object.__setattr__(self, "native_reason", _bounded(self.native_reason, 128))
        object.__setattr__(self, "response_id", _bounded(self.response_id, 160))

    def to_dict(self) -> dict[str, str | None]:
        payload = asdict(self)
        payload["disposition"] = self.disposition.value
        return payload

    @classmethod
    def from_value(cls, value: Any) -> "ProviderCompletion | None":
        if value is None:
            return None
        if isinstance(value, cls):
            return value
        if not isinstance(value, dict):
            raise ValueError("Provider completion metadata must be an object")
        return cls(
            disposition=CompletionDisposition(
                str(value.get("disposition") or "provider_incomplete")
            ),
            native_reason=value.get("native_reason"),
            response_id=value.get("response_id"),
        )


def native_reason(value: Any) -> str | None:
    """Normalize SDK enums and strings without retaining unbounded objects."""

    if value is None:
        return None
    candidate = getattr(value, "name", None)
    if candidate is None:
        candidate = getattr(value, "value", None)
    if candidate is None:
        candidate = str(value)
    normalized = str(candidate).strip()
    if "." in normalized:
        normalized = normalized.rsplit(".", 1)[-1]
    return _bounded(normalized.upper(), 128)


def _bounded(value: Any, limit: int) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized[:limit] or None
