"""
LLM Provider Adapters

Provides unified interface for multiple LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Optional
import httpx
import json
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """Standard message format."""
    role: str  # system, user, assistant
    content: str
    name: Optional[str] = None


@dataclass
class ChatResponse:
    """Standard response format."""
    content: str
    model: str
    tokens_in: int
    tokens_out: int
    finish_reason: str
    raw_response: Optional[dict] = None


@dataclass
class ProviderConfig:
    """Provider configuration."""
    api_key: str
    endpoint: Optional[str] = None
    model_id: Optional[str] = None
    deployment_name: Optional[str] = None
    api_version: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    extra: Optional[dict] = None


class BaseProvider(ABC):
    """Base class for LLM providers."""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name."""
        pass
    
    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> ChatResponse:
        """Send chat completion request."""
        pass
    
    @abstractmethod
    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream chat completion response."""
        pass
    
    async def health_check(self) -> dict[str, Any]:
        """Check provider health."""
        try:
            # Simple test with minimal tokens
            response = await self.chat(
                messages=[ChatMessage(role="user", content="Hi")],
                max_tokens=5,
            )
            return {"status": "healthy", "model": response.model}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if not self._client:
            self._client = httpx.AsyncClient(timeout=self.config.timeout)
        return self._client


class OpenAIProvider(BaseProvider):
    """OpenAI API provider (also works for OpenAI-compatible APIs)."""
    
    DEFAULT_ENDPOINT = "https://api.openai.com/v1"
    DEFAULT_MODEL = "gpt-4"
    
    @property
    def provider_name(self) -> str:
        return "openai"
    
    async def chat(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> ChatResponse:
        client = self._get_client()
        endpoint = self.config.endpoint or self.DEFAULT_ENDPOINT
        model = model or self.config.model_id or self.DEFAULT_MODEL
        
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        payload.update(kwargs)
        
        response = await client.post(
            f"{endpoint}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        
        choice = data["choices"][0]
        usage = data.get("usage", {})
        
        return ChatResponse(
            content=choice["message"]["content"],
            model=data["model"],
            tokens_in=usage.get("prompt_tokens", 0),
            tokens_out=usage.get("completion_tokens", 0),
            finish_reason=choice.get("finish_reason", "stop"),
            raw_response=data,
        )
    
    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        client = self._get_client()
        endpoint = self.config.endpoint or self.DEFAULT_ENDPOINT
        model = model or self.config.model_id or self.DEFAULT_MODEL
        
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        payload.update(kwargs)
        
        async with client.stream(
            "POST",
            f"{endpoint}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]
                    except json.JSONDecodeError:
                        continue


class AzureOpenAIProvider(BaseProvider):
    """Azure OpenAI provider."""
    
    DEFAULT_API_VERSION = "2024-02-15-preview"
    
    @property
    def provider_name(self) -> str:
        return "azure"
    
    async def chat(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> ChatResponse:
        client = self._get_client()
        
        if not self.config.endpoint:
            raise ValueError("Azure endpoint required")
        
        deployment = model or self.config.deployment_name
        if not deployment:
            raise ValueError("Azure deployment name required")
        
        api_version = self.config.api_version or self.DEFAULT_API_VERSION
        
        url = f"{self.config.endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
        
        payload = {
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        payload.update(kwargs)
        
        response = await client.post(
            url,
            headers={
                "api-key": self.config.api_key,
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        
        choice = data["choices"][0]
        usage = data.get("usage", {})
        
        return ChatResponse(
            content=choice["message"]["content"],
            model=data.get("model", deployment),
            tokens_in=usage.get("prompt_tokens", 0),
            tokens_out=usage.get("completion_tokens", 0),
            finish_reason=choice.get("finish_reason", "stop"),
            raw_response=data,
        )
    
    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        client = self._get_client()
        
        if not self.config.endpoint:
            raise ValueError("Azure endpoint required")
        
        deployment = model or self.config.deployment_name
        if not deployment:
            raise ValueError("Azure deployment name required")
        
        api_version = self.config.api_version or self.DEFAULT_API_VERSION
        
        url = f"{self.config.endpoint}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
        
        payload = {
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        payload.update(kwargs)
        
        async with client.stream(
            "POST",
            url,
            headers={
                "api-key": self.config.api_key,
                "Content-Type": "application/json",
            },
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]
                    except json.JSONDecodeError:
                        continue


class AnthropicProvider(BaseProvider):
    """Anthropic Claude provider."""
    
    DEFAULT_ENDPOINT = "https://api.anthropic.com/v1"
    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
    API_VERSION = "2023-06-01"
    
    @property
    def provider_name(self) -> str:
        return "anthropic"
    
    async def chat(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> ChatResponse:
        client = self._get_client()
        endpoint = self.config.endpoint or self.DEFAULT_ENDPOINT
        model = model or self.config.model_id or self.DEFAULT_MODEL
        
        # Anthropic uses different message format
        # Extract system message if present
        system_msg = None
        chat_messages = []
        for m in messages:
            if m.role == "system":
                system_msg = m.content
            else:
                chat_messages.append({"role": m.role, "content": m.content})
        
        payload = {
            "model": model,
            "messages": chat_messages,
            "max_tokens": max_tokens or 4096,
        }
        if system_msg:
            payload["system"] = system_msg
        if temperature != 1.0:
            payload["temperature"] = temperature
        
        response = await client.post(
            f"{endpoint}/messages",
            headers={
                "x-api-key": self.config.api_key,
                "anthropic-version": self.API_VERSION,
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        
        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")
        
        usage = data.get("usage", {})
        
        return ChatResponse(
            content=content,
            model=data["model"],
            tokens_in=usage.get("input_tokens", 0),
            tokens_out=usage.get("output_tokens", 0),
            finish_reason=data.get("stop_reason", "end_turn"),
            raw_response=data,
        )
    
    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        client = self._get_client()
        endpoint = self.config.endpoint or self.DEFAULT_ENDPOINT
        model = model or self.config.model_id or self.DEFAULT_MODEL
        
        system_msg = None
        chat_messages = []
        for m in messages:
            if m.role == "system":
                system_msg = m.content
            else:
                chat_messages.append({"role": m.role, "content": m.content})
        
        payload = {
            "model": model,
            "messages": chat_messages,
            "max_tokens": max_tokens or 4096,
            "stream": True,
        }
        if system_msg:
            payload["system"] = system_msg
        if temperature != 1.0:
            payload["temperature"] = temperature
        
        async with client.stream(
            "POST",
            f"{endpoint}/messages",
            headers={
                "x-api-key": self.config.api_key,
                "anthropic-version": self.API_VERSION,
                "Content-Type": "application/json",
            },
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        if data.get("type") == "content_block_delta":
                            delta = data.get("delta", {})
                            if delta.get("type") == "text_delta":
                                yield delta.get("text", "")
                    except json.JSONDecodeError:
                        continue


class GoogleProvider(BaseProvider):
    """Google Gemini provider."""
    
    DEFAULT_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta"
    DEFAULT_MODEL = "gemini-1.5-pro"
    
    @property
    def provider_name(self) -> str:
        return "google"
    
    async def chat(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> ChatResponse:
        client = self._get_client()
        endpoint = self.config.endpoint or self.DEFAULT_ENDPOINT
        model = model or self.config.model_id or self.DEFAULT_MODEL
        
        # Convert to Gemini format
        contents = []
        system_instruction = None
        
        for m in messages:
            if m.role == "system":
                system_instruction = m.content
            else:
                role = "user" if m.role == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": m.content}]
                })
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
            }
        }
        if max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = max_tokens
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        
        url = f"{endpoint}/models/{model}:generateContent?key={self.config.api_key}"
        
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Extract content
        content = ""
        candidates = data.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            for part in parts:
                content += part.get("text", "")
        
        usage = data.get("usageMetadata", {})
        
        return ChatResponse(
            content=content,
            model=model,
            tokens_in=usage.get("promptTokenCount", 0),
            tokens_out=usage.get("candidatesTokenCount", 0),
            finish_reason=candidates[0].get("finishReason", "STOP") if candidates else "STOP",
            raw_response=data,
        )
    
    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        client = self._get_client()
        endpoint = self.config.endpoint or self.DEFAULT_ENDPOINT
        model = model or self.config.model_id or self.DEFAULT_MODEL
        
        contents = []
        system_instruction = None
        
        for m in messages:
            if m.role == "system":
                system_instruction = m.content
            else:
                role = "user" if m.role == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": m.content}]
                })
        
        payload = {
            "contents": contents,
            "generationConfig": {"temperature": temperature}
        }
        if max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = max_tokens
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        
        url = f"{endpoint}/models/{model}:streamGenerateContent?key={self.config.api_key}&alt=sse"
        
        async with client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            for part in parts:
                                text = part.get("text", "")
                                if text:
                                    yield text
                    except json.JSONDecodeError:
                        continue


class CustomProvider(BaseProvider):
    """Custom/OpenAI-compatible endpoint provider."""
    
    @property
    def provider_name(self) -> str:
        return "custom"
    
    async def chat(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> ChatResponse:
        # Use OpenAI-compatible format by default
        client = self._get_client()
        
        if not self.config.endpoint:
            raise ValueError("Custom endpoint required")
        
        model = model or self.config.model_id or "default"
        
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        payload.update(kwargs)
        
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        
        # Add any extra headers from config
        if self.config.extra and "headers" in self.config.extra:
            headers.update(self.config.extra["headers"])
        
        response = await client.post(
            self.config.endpoint,
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        
        # Try OpenAI format first
        if "choices" in data:
            choice = data["choices"][0]
            usage = data.get("usage", {})
            return ChatResponse(
                content=choice["message"]["content"],
                model=data.get("model", model),
                tokens_in=usage.get("prompt_tokens", 0),
                tokens_out=usage.get("completion_tokens", 0),
                finish_reason=choice.get("finish_reason", "stop"),
                raw_response=data,
            )
        # Fallback for other formats
        else:
            content = data.get("text", data.get("content", data.get("response", str(data))))
            return ChatResponse(
                content=content,
                model=model,
                tokens_in=0,
                tokens_out=0,
                finish_reason="stop",
                raw_response=data,
            )
    
    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        # Fallback to non-streaming for custom providers
        response = await self.chat(messages, model, temperature, max_tokens, **kwargs)
        yield response.content


# Provider registry
PROVIDERS = {
    "openai": OpenAIProvider,
    "azure": AzureOpenAIProvider,
    "anthropic": AnthropicProvider,
    "google": GoogleProvider,
    "custom": CustomProvider,
}


def get_provider(provider_type: str, config: ProviderConfig) -> BaseProvider:
    """Get provider instance by type."""
    provider_class = PROVIDERS.get(provider_type.lower())
    if not provider_class:
        raise ValueError(f"Unknown provider type: {provider_type}. Available: {list(PROVIDERS.keys())}")
    return provider_class(config)
