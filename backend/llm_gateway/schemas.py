from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Dict, Any, Union, Literal

class Message(BaseModel):
    role: Literal["user", "system", "assistant"]
    content: Union[str, List[Dict[str, Any]]] = Field(...)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value):
        if isinstance(value, str):
            if not value.strip():
                raise ValueError("content must not be empty")
            return value
        if isinstance(value, list):
            if len(value) == 0:
                raise ValueError("content must not be empty")
            return value
        raise ValueError("content must be a string or multimodal content array")

class TraceSettings(BaseModel):
    enabled: bool = True
    level: Literal["basic", "full"] = "full"

class GatewayChatRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    messages: List[Message] = Field(..., min_length=1)
    provider: Optional[str] = None
    model: Optional[str] = Field(None, min_length=1)
    mode: Literal[
        "chat",
        "trace",
        "explain",
        "quad",
        "standard",
        "enhanced",
        "local_review",
        "simulation",
    ] = "standard"
    constraints: Dict[str, Any] = Field(default_factory=dict)
    run_ukg_pipeline: bool = True
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1)
    session_id: Optional[str] = None
    
    # Trace specific
    trace_settings: Optional[TraceSettings] = None
    
    # Metadata for 17-axis resolution
    meta: Dict[str, Any] = Field(default_factory=dict)

class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    permissions: Dict[str, bool] = Field(default_factory=lambda: {"read": True, "write": True})
    allowed_providers: Optional[List[str]] = None
    expires_in_days: Optional[int] = Field(None, ge=1)
    rate_limit_rpm: int = Field(60, ge=1)

class ProviderCreate(BaseModel):
    name: str = Field(..., min_length=1)
    provider_type: Literal["openai", "azure", "anthropic", "google", "custom"]
    endpoint: Optional[str] = None
    model_id: Optional[str] = None
    api_key: Optional[str] = None
    is_active: bool = True
    is_default: bool = False
    priority: int = 100
    timeout_seconds: int = Field(30, ge=1)
