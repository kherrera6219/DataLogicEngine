from pydantic import BaseModel, Field, constr, validator
from typing import List, Optional, Dict, Any, Union, Literal

class Message(BaseModel):
    role: Literal["user", "system", "assistant"]
    content: str = Field(..., min_length=1)

class TraceSettings(BaseModel):
    enabled: bool = True
    level: Literal["basic", "full"] = "full"

class GatewayChatRequest(BaseModel):
    messages: List[Message] = Field(..., min_items=1)
    provider: Optional[str] = None
    model: Optional[str] = None
    mode: Literal["chat", "trace", "explain"] = "chat"
    constraints: Dict[str, Any] = Field(default_factory=dict)
    run_ukg_pipeline: bool = True
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1)
    
    # Trace specific
    trace_settings: Optional[TraceSettings] = None
    
    # Metadata for 17-axis resolution
    meta: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "ignore"

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
