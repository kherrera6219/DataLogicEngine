from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any

class StorageTestRequest(BaseModel):
    service: str = Field(..., pattern="^(postgres|redis|neo4j|vector|object)$")
    host: Optional[str] = "127.0.0.1"
    port: Optional[int] = None
    provider: Optional[str] = "local"
    local_path: Optional[str] = None
    api_key: Optional[str] = None
    endpoint_url: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None

    @field_validator('local_path')
    @classmethod
    def validate_path(cls, v):
        if v and ('..' in v or v.startswith('/') or v.startswith('\\') or ':' in v):
            raise ValueError("Path traversal or absolute paths not allowed")
        return v

class AudioSynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    voice: Optional[str] = "alloy"

class PillarCreateRequest(BaseModel):
    pillar_id: str = Field(..., pattern=r"^PL\d+$")
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    sublevels: Optional[Dict[str, Any]] = None
