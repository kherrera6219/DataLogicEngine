from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, UTC

class Layer6Input(BaseModel):
    """Input payload for Quantitative Validation."""
    draft_solution: str = Field(..., min_length=1, description="The qualitative draft from L5")
    claims: List[str] = Field(default_factory=list, description="Extracted atomic claims")
    data_context: Optional[Dict[str, Any]] = Field(default=None, description="Raw data tables/timeseries")
    
    @field_validator('draft_solution')
    def check_draft(cls, v):
        if not v.strip():
            raise ValueError("Draft solution cannot be empty")
        return v

class QuantBundle(BaseModel):
    """Output payload (Validation Report)."""
    is_valid: bool
    risk_score: float = Field(..., ge=0.0, le=1.0)
    confidence_map: Dict[str, float]
    anomalies: List[str]
    validation_flags: List[str]
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
