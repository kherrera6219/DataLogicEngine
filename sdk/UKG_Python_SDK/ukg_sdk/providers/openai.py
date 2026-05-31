from __future__ import annotations

import os
from typing import Dict, List, Optional

from .base import LLMProvider, LLMResponse

import logging
from tenacity import retry, stop_after_attempt, wait_exponential

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
        Generate completion using the OpenAI Responses API (GPT-5.5).

        GPT-5.x are reasoning models: they reject a custom ``temperature`` and
        count reasoning tokens against ``max_output_tokens``, so the budget must
        leave room for both reasoning and the visible answer.
        """
        # Normalize generic aliases to the standard model; keep explicit IDs.
        alias_map = {
            "gpt-5": "gpt-5.5",
            "gpt-5-latest": "gpt-5.5",
            "gpt-5-chat": "gpt-5.5",
        }
        target_model = alias_map.get(model, model or "gpt-5.5")

        # Construct input for Responses API (accepts a list of chat-style messages).
        input_payload = messages

        try:
            from openai import AsyncOpenAI
            async_client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout_s)

            # Reasoning models (gpt-5.x / o-series) reserve part of the budget for
            # reasoning, so floor the output budget; the Responses API also
            # requires max_output_tokens >= 16.
            is_reasoning = target_model.lower().startswith(("gpt-5", "o1", "o3", "o4"))
            output_budget = max(int(max_tokens) if max_tokens else 0, 1024 if is_reasoning else 16)

            request_kwargs: Dict = {
                "model": target_model,
                "input": input_payload,
                "max_output_tokens": output_budget,
            }
            if is_reasoning:
                # gpt-5.x do not accept a custom temperature; use reasoning effort.
                request_kwargs["reasoning"] = {"effort": "medium"}
            else:
                request_kwargs["temperature"] = temperature

            response = await async_client.responses.create(**request_kwargs)
            
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
