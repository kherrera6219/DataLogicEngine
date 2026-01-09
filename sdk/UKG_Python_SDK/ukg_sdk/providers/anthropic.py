from __future__ import annotations

import os
from typing import Dict, List, Optional

import httpx

from .base import LLMProvider, LLMResponse


import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class AnthropicProvider(LLMProvider):
    """Anthropic Messages API provider (HTTP, no SDK dependency).

    Env vars:
      - ANTHROPIC_API_KEY
      - ANTHROPIC_BASE_URL (optional; default https://api.anthropic.com)
      - ANTHROPIC_VERSION (default 2023-06-01)
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, anthropic_version: Optional[str] = None, timeout_s: float = 60.0):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        if not self.api_key:
            raise ValueError("Missing ANTHROPIC_API_KEY")
        self.base_url = (base_url or os.getenv("ANTHROPIC_BASE_URL") or "https://api.anthropic.com").rstrip("/")
        self.anthropic_version = anthropic_version or os.getenv("ANTHROPIC_VERSION") or "2023-06-01"
        self.timeout_s = timeout_s

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException, httpx.HTTPStatusError)),
        reraise=True
    )
    async def complete(self, *, messages: List[Dict[str, str]], model: str, temperature: float = 0.2, max_tokens: int = 1024) -> LLMResponse:
        # Anthropic expects system separately; we fold role=system messages into system string.
        system_parts = [m["content"] for m in messages if m.get("role") == "system"]
        user_assistant = [m for m in messages if m.get("role") in {"user", "assistant"}]
        content = []
        for m in user_assistant:
            content.append({"role": m["role"], "content": m["content"]})
        url = f"{self.base_url}/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.anthropic_version,
            "content-type": "application/json",
        }
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": "\n\n".join(system_parts) if system_parts else None,
            "messages": content,
        }
        # remove None fields
        payload = {k: v for k, v in payload.items() if v is not None}
        
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            try:
                r = await client.post(url, headers=headers, json=payload)
                r.raise_for_status()
                data = r.json()
            except httpx.HTTPStatusError as e:
                # 429 and 529 are common for Anthropic rate limiting/overload
                if e.response.status_code in {429, 529} or e.response.status_code >= 500:
                    logger.warning(f"Anthropic API error {e.response.status_code}. Retrying...")
                    raise
                raise
            except (httpx.NetworkError, httpx.TimeoutException) as e:
                logger.warning(f"Anthropic connection error: {str(e)}. Retrying...")
                raise

        # Anthropic returns list of content blocks; join text blocks
        text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                text += block.get("text", "")
        return LLMResponse(text=text, raw=data, model=data.get("model"), usage=data.get("usage"))
