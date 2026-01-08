from __future__ import annotations

import os
from typing import Dict, List, Optional

import httpx

from .base import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    """OpenAI Chat Completions provider (HTTP, no SDK dependency).

    Env vars:
      - OPENAI_API_KEY
      - OPENAI_BASE_URL (optional; default https://api.openai.com/v1)
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, timeout_s: float = 60.0):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        if not self.api_key:
            raise ValueError("Missing OPENAI_API_KEY")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.timeout_s = timeout_s

    async def complete(self, *, messages: List[Dict[str, str]], model: str, temperature: float = 0.2, max_tokens: int = 1024) -> LLMResponse:
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
        text = data["choices"][0]["message"]["content"]
        return LLMResponse(text=text, raw=data, model=data.get("model"), usage=data.get("usage"))
