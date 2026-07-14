"""Backend-owned asynchronous provider contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, AsyncIterator


@dataclass(frozen=True, slots=True)
class LLMResponse:
    text: str
    raw: dict[str, Any]
    model: str
    usage: dict[str, Any]


class LLMProvider(ABC):
    provider_type: str

    @abstractmethod
    async def complete(
        self,
        *,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> LLMResponse: ...

    @abstractmethod
    async def stream(
        self,
        *,
        messages: list[dict[str, Any]],
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]: ...

    async def close(self) -> None:
        return None
