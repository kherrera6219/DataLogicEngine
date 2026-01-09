from __future__ import annotations

import os
from typing import Dict, List, Optional

import httpx

from .base import LLMProvider, LLMResponse


import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException, httpx.HTTPStatusError)),
        reraise=True
    )
    async def complete(self, *, messages: List[Dict[str, str]], model: str, temperature: float = 0.2, max_tokens: int = 1024) -> LLMResponse:
        url = f"{self.base_url}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            try:
                r = await client.post(url, headers=headers, json=payload)
                r.raise_for_status()
                data = r.json()
            except httpx.HTTPStatusError as e:
                # Only retry on 429 or 5xx
                if e.response.status_code == 429 or e.response.status_code >= 500:
                    logger.warning(f"OpenAI API error {e.response.status_code}. Retrying...")
                    raise
                # Re-raise for 4xx errors (except 429) - they won't be retried
                raise
            except (httpx.NetworkError, httpx.TimeoutException) as e:
                logger.warning(f"OpenAI connection error: {str(e)}. Retrying...")
                raise

        text = data["choices"][0]["message"]["content"]
        return LLMResponse(text=text, raw=data, model=data.get("model"), usage=data.get("usage"))
