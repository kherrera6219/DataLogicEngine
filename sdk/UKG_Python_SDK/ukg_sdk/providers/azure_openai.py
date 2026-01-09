from __future__ import annotations

import os
from typing import Dict, List, Optional

import httpx

from .base import LLMProvider, LLMResponse


import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI provider (Chat Completions-style endpoint).

    Env vars:
      - AZURE_OPENAI_API_KEY
      - AZURE_OPENAI_ENDPOINT (e.g. https://<resource>.openai.azure.com)
      - AZURE_OPENAI_API_VERSION (default: 2024-02-15-preview)
      - AZURE_OPENAI_DEPLOYMENT (default deployment name if model not set)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        api_version: Optional[str] = None,
        default_deployment: Optional[str] = None,
        timeout_s: float = 60.0,
    ):
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY", "")
        if not self.api_key:
            raise ValueError("Missing AZURE_OPENAI_API_KEY")
        self.endpoint = (endpoint or os.getenv("AZURE_OPENAI_ENDPOINT", "")).rstrip("/")
        if not self.endpoint:
            raise ValueError("Missing AZURE_OPENAI_ENDPOINT")
        self.api_version = api_version or os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        self.default_deployment = default_deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT")
        self.timeout_s = timeout_s

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException, httpx.HTTPStatusError)),
        reraise=True
    )
    async def complete(self, *, messages: List[Dict[str, str]], model: str, temperature: float = 0.2, max_tokens: int = 1024) -> LLMResponse:
        deployment = model or self.default_deployment
        if not deployment:
            raise ValueError("AzureOpenAIProvider requires model=<deployment> or AZURE_OPENAI_DEPLOYMENT")
        url = f"{self.endpoint}/openai/deployments/{deployment}/chat/completions?api-version={self.api_version}"
        headers = {"api-key": self.api_key}
        payload = {"messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            try:
                r = await client.post(url, headers=headers, json=payload)
                r.raise_for_status()
                data = r.json()
            except httpx.HTTPStatusError as e:
                # 429 and 5xx are common for Azure rate limiting/overload
                if e.response.status_code == 429 or e.response.status_code >= 500:
                    logger.warning(f"Azure OpenAI API error {e.response.status_code}. Retrying...")
                    raise
                raise
            except (httpx.NetworkError, httpx.TimeoutException) as e:
                logger.warning(f"Azure OpenAI connection error: {str(e)}. Retrying...")
                raise

        text = data["choices"][0]["message"]["content"]
        return LLMResponse(text=text, raw=data, model=deployment, usage=data.get("usage"))
