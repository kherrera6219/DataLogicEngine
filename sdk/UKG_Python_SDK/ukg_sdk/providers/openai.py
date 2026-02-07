from __future__ import annotations

import os
from typing import Dict, List, Optional, Any

from .base import LLMProvider, LLMResponse

import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class OpenAIProvider(LLMProvider):
    """OpenAI Provider (Production: Uses official SDK with Responses API).

    Env vars:
      - OPENAI_API_KEY
      - OPENAI_BASE_URL (optional)
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, timeout_s: float = 60.0):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        if not self.api_key:
            raise ValueError("Missing OPENAI_API_KEY")
        
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL"))
        self.timeout_s = timeout_s
        
        # Initialize official client
        try:
            from openai import OpenAI, APIError, APITimeoutError, RateLimitError
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout_s
            )
            self._errors = (APIError, APITimeoutError, RateLimitError)
        except ImportError:
            raise ImportError("Please install 'openai' package: pip install openai")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def complete(self, *, messages: List[Dict[str, str]], model: str, temperature: float = 0.7, max_tokens: int = 1024) -> LLMResponse:
        """
        Generate completion using OpenAI Responses API (GPT-5.2 Standard).
        """
        # Keep explicit model IDs unchanged; only normalize generic aliases.
        alias_map = {
            "gpt-5": "gpt-5.2",
            "gpt-5-latest": "gpt-5.2",
            "gpt-5-chat": "gpt-5.2-chat-latest",
        }
        target_model = alias_map.get(model, model or "gpt-5.2")
        
        # Construct input for Responses API
        # It accepts string or list of messages
        input_payload = messages # Pass the list directly as chat-style input

        try:
            # Use new 2026 pattern: client.responses.create
            # Note: The synchronous client is wrapped in async context in older frameworks, 
            # but standard OpenAI v1+ client is sync by default unless AsyncOpenAI used.
            # For this provider base which is async, we should use AsyncOpenAI ideally.
            # But to match the user's snippets exact style first:
            
            # Use Async Client if possible, else wrap
            from openai import AsyncOpenAI
            async_client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout_s)
            
            response = await async_client.responses.create(
                model=target_model,
                input=input_payload,
                max_output_tokens=max_tokens,
                temperature=temperature
            )
            
            text = response.output_text
            
            # Map usage (Responses API structure)
            # Assuming response.usage object exists
            usage = {
                "prompt_tokens": 0, # Often abstracted in Responses API
                "completion_tokens": 0,
                "total_tokens": 0
            }
            if hasattr(response, 'usage'):
                 usage["total_tokens"] = getattr(response.usage, 'total_tokens', 0)

            return LLMResponse(
                text=text,
                raw={"response": str(response)},
                model=target_model,
                usage=usage
            )

        except Exception as e:
            logger.error(f"OpenAI Responses API error: {e}")
            raise
