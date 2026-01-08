from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class KAInfo(BaseModel):
    """Metadata for a Knowledge Algorithm (KA)."""

    ka_id: str = Field(..., description="Canonical KA identifier, e.g. KA-001")
    name: str
    short_name: Optional[str] = None
    purpose: Optional[str] = None
    category: Optional[str] = None
    primary_layers: List[str] = Field(default_factory=list)
    allowed_layers: List[str] = Field(default_factory=list)

    inputs: Optional[str] = None
    outputs: Optional[str] = None

    reads_memory: bool = False
    writes_memory: bool = False
    can_invoke_chaos: bool = False
    can_invoke_external_research: bool = False
    can_trigger_recursion: bool = False
    can_veto: bool = False

    risk_class: Optional[str] = None
    confidence_impact: Optional[str] = None
    entropy_signal: Optional[str] = None

    default_params: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)

    produces_artifacts: bool = False
    audit_events: bool = True

    version: str = "1.0.0"
    owner: str = "UKG/USKD Core"
    status: str = "Active"


class KARegistry(BaseModel):
    """Collection of KAInfo items."""

    items: Dict[str, KAInfo] = Field(default_factory=dict)

    def get(self, ka_id: str) -> KAInfo:
        return self.items[ka_id]

    def has(self, ka_id: str) -> bool:
        return ka_id in self.items

    def list_ids(self) -> List[str]:
        return sorted(self.items.keys())
