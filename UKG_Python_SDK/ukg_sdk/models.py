from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RiskClass(str, Enum):
    low = "Low"
    medium = "Medium"
    high = "High"
    critical = "Critical"


class UKGEnvelope(BaseModel):
    """Lightweight wrapper for responses to preserve trace metadata."""

    data: Any = None
    trace_id: Optional[str] = None
    request_id: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    source: str
    uri: Optional[str] = None
    excerpt: Optional[str] = None
    hash: Optional[str] = None
    trust_weight: Optional[float] = None
    timestamp: Optional[str] = None


class EvidencePacket(BaseModel):
    items: List[EvidenceItem] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class WorkflowResult(BaseModel):
    tier: str
    answer: Any = None
    confidence: Optional[float] = None
    entropy: Optional[float] = None
    evidence: Optional[EvidencePacket] = None
    audit_events: List[Dict[str, Any]] = Field(default_factory=list)
    artifacts: Dict[str, Any] = Field(default_factory=dict)
