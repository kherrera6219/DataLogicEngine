from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class LLMResponse:
    text: str
    raw: Dict[str, Any]
    model: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None


class LLMProvider(ABC):
    """LLM provider abstraction used by the UKG Overlay."""

    @abstractmethod
    async def complete(self, *, messages: List[Dict[str, str]], model: str, temperature: float = 0.2, max_tokens: int = 1024) -> LLMResponse: ...
