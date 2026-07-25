from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class KAInfo(BaseModel):
    """Metadata for a Knowledge Algorithm (KA)."""

    ka_id: str = Field(..., description="Canonical KA identifier, e.g. KA-001")
    name: str
    short_name: str | None = None
    purpose: str | None = None
    category: str | None = None
    primary_layers: list[str] = Field(default_factory=list)
    allowed_layers: list[str] = Field(default_factory=list)

    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)

    reads_memory: bool = False
    writes_memory: bool = False
    can_invoke_chaos: bool = False
    can_invoke_external_research: bool = False
    can_trigger_recursion: bool = False
    can_veto: bool = False

    risk_class: str | None = None
    confidence_impact: str | None = None
    entropy_signal: str | None = None

    default_params: dict[str, Any] = Field(default_factory=dict)
    dependencies: list[str] = Field(default_factory=list)

    produces_artifacts: bool = False
    audit_events: bool = True

    version: str = "1.0.0"
    owner: str = "UKG/USKD Core"
    status: str = "Active"
    aliases: list[str] = Field(default_factory=list)
    implementation_status: str | None = None
    production_enabled: bool = False
    classification: str | None = None
    limitations: str | None = None


class KARegistry(BaseModel):
    """Collection of KAInfo items."""

    items: dict[str, KAInfo] = Field(default_factory=dict)

    def get(self, ka_id: str) -> KAInfo:
        return self.items[ka_id]

    def has(self, ka_id: str) -> bool:
        return ka_id in self.items

    def list_ids(self) -> list[str]:
        return sorted(self.items.keys())
