from __future__ import annotations

import logging
from typing import Dict, List
import aiohttp

from .base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)

class LocalSLMProvider(LLMProvider):
    """
    Local SLM Provider (vLLM / Ollama).
    Implements the OpenAI-compatible chat completions API for local serving.
    """

    def __init__(self, base_url: str = "http://localhost:11434/v1"):
        self.base_url = base_url.rstrip("/")

    async def complete(
        self,
        *,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.2,
        max_tokens: int = 1024
    ) -> LLMResponse:
        """Point to local inference endpoint."""
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"Local SLM failed: {resp.status} - {error_text}")
                        return LLMResponse(text="", raw={"error": error_text, "ok": False})
                    
                    data = await resp.json()
                    content = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})
                    
                    return LLMResponse(
                        text=content,
                        model=model,
                        usage=usage,
                        raw=data
                    )
        except Exception as e:
            logger.error(f"Local SLM exception: {e}")
            return LLMResponse(text="", raw={"error": str(e), "ok": False})
