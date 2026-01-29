from __future__ import annotations

import os
from typing import Dict, List, Optional, Any

from .base import LLMProvider, LLMResponse

import logging

logger = logging.getLogger(__name__)

class GoogleGeminiProvider(LLMProvider):
    """Google Gemini provider using google-generativeai SDK.

    Env vars:
      - GOOGLE_API_KEY or GEMINI_API_KEY
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-pro"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Missing GOOGLE_API_KEY or GEMINI_API_KEY")
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.genai = genai
        except ImportError:
            raise ImportError("Please install google-generativeai to use GoogleGeminiProvider")

        self.default_model = model

    async def complete(self, *, messages: List[Dict[str, str]], model: str, temperature: float = 0.2, max_tokens: int = 1024) -> LLMResponse:
        """Generate completion using Gemini."""
        model_name = model or self.default_model
        
        # Map common model aliases (2025/2026 Generation)
        if "gemini-3-pro" in model_name and "preview" not in model_name:
            model_name = "gemini-3-pro-preview"
        elif "gemini-3-flash" in model_name and "preview" not in model_name:
            model_name = "gemini-3-flash-preview"
        elif "gemini-1.5" in model_name:
             # Basic mapping, can be refined
            model_name = "gemini-1.5-pro-latest"

        try:
            # Convert OpenAI-style messages to Gemini history
            # Gemini expects 'user' and 'model' roles. 'system' instructions are handled separately in newer models 
            # or prepended to the first message for older ones.
            
            gemini_history = []
            system_instruction = ""
            
            for msg in messages:
                role = msg.get("role")
                content = msg.get("content")
                
                if role == "system":
                    system_instruction += content + "\n"
                elif role == "user":
                    gemini_history.append({"role": "user", "parts": [content]})
                elif role == "assistant":
                    gemini_history.append({"role": "model", "parts": [content]})
            
            # Initialize model
            # Note: For Gemini 1.5, system instructions can be passed to GenerativeModel constructor
            generation_config = self.genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
            
            gemini_model = self.genai.GenerativeModel(model_name)
            
            # If system instruction exists, we might need to prepend it to the first user message 
            # if the SDK version/model doesn't support system_instruction arg cleanly yet.
            # safe conversion: Prepend to history if possible or first message.
            
            # Using chat session for multi-turn
            chat = gemini_model.start_chat(history=gemini_history[:-1] if gemini_history else [])
            
            last_message = gemini_history[-1]["parts"][0] if gemini_history else "Hello"
            if system_instruction and gemini_history:
                 # Prepend system prompt to the actual last message sent if not handled otherwise
                 # This is a robust fallback for "system" role
                 last_message = f"System Instruction: {system_instruction}\n\nUser Message: {last_message}"

            response = await chat.send_message_async(
                last_message,
                generation_config=generation_config
            )
            
            text = response.text
            usage = {
                # Dummy usage as Gemini SDK doesn't always return token counts simply in response object
                "prompt_tokens": 0,
                "completion_tokens": 0, 
                "total_tokens": 0
            }
            
            return LLMResponse(
                text=text,
                raw={"response": response},
                model=model_name,
                usage=usage
            )

        except Exception as e:
            logger.error(f"Google Gemini API error: {e}")
            raise

    async def embed(self, text: str) -> List[float]:
        """Generate embeddings using Gemini."""
        try:
            # Use embedding-001 by default
            result = self.genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']
        except Exception as e:
            logger.error(f"Google Gemini Embedding error: {e}")
            raise
