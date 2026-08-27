import json

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import List, Optional, Dict, Any, Union, Literal

class Message(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "system", "assistant"]
    content: Union[str, List[Dict[str, Any]]] = Field(...)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value):
        if isinstance(value, str):
            if not value.strip():
                raise ValueError("content must not be empty")
            if len(value.encode("utf-8")) > 200_000:
                raise ValueError("message content exceeds 200000 bytes")
            return value
        if isinstance(value, list):
            if len(value) == 0:
                raise ValueError("content must not be empty")
            if len(value) > 20:
                raise ValueError("multimodal content exceeds 20 parts")
            if len(json.dumps(value, ensure_ascii=False).encode("utf-8")) > 200_000:
                raise ValueError("multimodal content exceeds 200000 bytes")
            return value
        raise ValueError("content must be a string or multimodal content array")

class GatewayChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    messages: List[Message] = Field(..., min_length=1, max_length=64)
    request_id: Optional[str] = Field(None, min_length=8, max_length=128)
    idempotency_key: Optional[str] = Field(None, min_length=8, max_length=128)
    provider: Optional[str] = None
    model: Optional[str] = Field(None, min_length=1)
    virtual_model: Optional[Literal[
        "dle-standard",
        "dle-enhanced",
        "dle-local-review",
    ]] = None
    mode: Optional[Literal[
        "chat",
        "trace",
        "explain",
        "quad",
        "standard",
        "enhanced",
        "local_review",
        "simulation",
    ]] = None
    constraints: Dict[str, Any] = Field(default_factory=dict)
    run_ukg_pipeline: bool = True
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1)
    session_id: Optional[str] = Field(None, min_length=1, max_length=128)
    
    # Metadata for 17-axis resolution
    meta: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("constraints", "meta")
    @classmethod
    def validate_bounded_object(cls, value):
        if len(json.dumps(value, ensure_ascii=False).encode("utf-8")) > 32_768:
            raise ValueError("object exceeds 32768 bytes")
        return value


class GatewaySessionCreateRequest(BaseModel):
    """Desktop-internal idempotent chat-session create/ensure request."""

    model_config = ConfigDict(extra="forbid")

    session_id: Optional[str] = Field(None, min_length=36, max_length=36)
    mode: Literal["chat", "quad", "standard", "enhanced", "local_review"] = "chat"


class GatewayAsyncRunCreate(GatewayChatRequest):
    """A durable job must have an explicit retry identity."""

    idempotency_key: str = Field(..., min_length=8, max_length=128)


class OpenAIChatCompletionRequest(BaseModel):
    """Deliberately small, fail-closed OpenAI compatibility request."""

    model_config = ConfigDict(extra="forbid")

    model: Literal[
        "dle-standard",
        "dle-enhanced",
        "dle-local-review",
    ]
    messages: List[Message] = Field(..., min_length=1, max_length=64)
    stream: bool = False
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1)
    max_completion_tokens: Optional[int] = Field(None, ge=1)
    n: Literal[1] = 1
    user: Optional[str] = Field(None, min_length=1, max_length=128)

    @model_validator(mode="after")
    def validate_output_budget(self):
        if self.max_tokens is not None and self.max_completion_tokens is not None:
            raise ValueError("Use only one output-token limit field")
        return self

class APIKeyCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=100)
    scopes: List[Literal[
        "chat",
        "stream",
        "run:create",
        "run:read",
        "run:cancel",
        "trace:read",
        "evidence:read",
        "models:read",
        "routing:override",
    ]] = Field(default_factory=lambda: ["chat"])
    allowed_providers: Optional[List[str]] = None
    allowed_models: Optional[List[str]] = None
    expires_in_days: Optional[int] = Field(None, ge=1)
    rate_limit_rpm: int = Field(60, ge=1)
    rate_limit_daily: Optional[int] = Field(None, ge=1)
    max_tokens_per_request: Optional[int] = Field(None, ge=1)
    max_concurrent_requests: int = Field(2, ge=1, le=100)


class APIKeyRotate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overlap_seconds: int = Field(300, ge=0, le=86400)
    name: Optional[str] = Field(None, min_length=1, max_length=100)


class APIKeyExpire(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: Optional[str] = Field(None, max_length=240)

class ProviderCreate(BaseModel):
    name: str = Field(..., min_length=1)
    provider_type: Literal["openai", "google"]
    endpoint: Optional[str] = None
    model_id: Optional[str] = None
    api_key: Optional[str] = None
    is_active: bool = True
    is_default: bool = False
    priority: int = 100
    timeout_seconds: int = Field(30, ge=1)
