from __future__ import annotations

import os
from typing import Dict, List, Optional, Any

from .base import LLMProvider, LLMResponse

import logging

logger = logging.getLogger(__name__)

class GoogleGeminiProvider(LLMProvider):
    """Google Gemini provider using modern google-genai SDK (v1.0+).
    
    Supports Gemini 3.0+ models and Thinking Mode.

    Env vars:
      - GOOGLE_API_KEY
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-3-pro-preview"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Missing GOOGLE_API_KEY")
        
        try:
            from google import genai
            from google.genai import types
            self.client = genai.Client(api_key=self.api_key)
            self.types = types
        except ImportError:
            raise ImportError("Please install google-genai to use GoogleGeminiProvider")

        self.default_model = model

    async def complete(self, *, messages: List[Dict[str, str]], model: str, temperature: float = 0.7, max_tokens: int = 1024) -> LLMResponse:
        """Generate completion using Gemini 3 Client."""
        model_name = model or self.default_model
        
        # Backward compatibility / Aliasing
        if "gemini-3" in model_name and "preview" not in model_name:
             model_name = "gemini-3-pro-preview"
        
        try:
            # Convert messages to string for simple generation if not handling chat history explicitly here
            # or usage of client.chats for multi-turn. 
            # For simplicity and robustness with the new SDK's single-turn generate_content for now:
            
            # Extract system instruction if present
            system_instruction = None
            prompt_parts = []
            
            for msg in messages:
                role = msg.get("role")
                content = msg.get("content")
                if role == "system":
                    system_instruction = content
                elif role == "user":
                    prompt_parts.append(f"User: {content}")
                elif role == "assistant":
                    prompt_parts.append(f"Model: {content}")
            
            full_prompt = "\n".join(prompt_parts)
            
            # Configure generation
            config = self.types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                system_instruction=system_instruction
            )
            
            # Gemini 3 Thinking Config check
            if "gemini-3" in model_name:
                # Enable high reasoning for complex tasks if hinted? 
                # For now, default to standard, but can be enabled via dynamic config in future
                pass

            response = self.client.models.generate_content(
                model=model_name,
                contents=full_prompt,
                config=config
            )
            
            text = response.text
            
            # Estimate usage (SDK v0.6 might not return it easily in sync object, checking attrs)
            usage = {
                "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", 0) if response.usage_metadata else 0,
                "completion_tokens": getattr(response.usage_metadata, "candidates_token_count", 0) if response.usage_metadata else 0,
                "total_tokens": getattr(response.usage_metadata, "total_token_count", 0) if response.usage_metadata else 0
            }
            
            return LLMResponse(
                text=text,
                raw={"response": str(response)},
                model=model_name,
                usage=usage
            )

        except Exception as e:
            logger.error(f"Google Gemini (genai) error: {e}")
            raise

    async def embed(self, text: str) -> List[float]:
        """Generate embeddings using Gemini."""
        try:
            # Use text-embedding-004 as standard for genai sdk
            result = self.client.models.embed_content(
                model="text-embedding-004",
                contents=text,
            )
            # result.embeddings is a list of embeddings (one per content)
            return result.embeddings[0].values
        except Exception as e:
            logger.error(f"Google Gemini Embedding error: {e}")
            raise
