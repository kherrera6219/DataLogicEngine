from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class QueryRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    query: str = Field(..., min_length=1, max_length=5000)
    confidenceThreshold: float = Field(default=0.85, ge=0.0, le=1.0)
    maxLayer: int = Field(default=5, ge=1, le=10)


class SimulationRunRequest(QueryRequest):
    model_config = ConfigDict(extra="ignore")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    refinementSteps: int = Field(default=8, ge=1, le=50)


class SimulationCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    parameters: dict[str, Any] = Field(default_factory=dict)


class PillarLevelCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    pillar_id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    sublevels: Any | None = None


class SectorCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    sector_code: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    parent_sector_id: int | None = None


class DomainCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    domain_code: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    sector_id: int | None = None
    parent_domain_id: int | None = None


class KnowledgeNodeCreateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1, max_length=20000)
    content_type: str = Field(..., min_length=1, max_length=100)
    pillar_level_id: int | None = None
    domain_id: int | None = None
    location_id: int | None = None
    metadata: dict[str, Any] | None = None


class ComplianceStandardCreateRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str = Field(..., min_length=1, max_length=255)
    parent_id: str | None = Field(default=None, min_length=1, max_length=128)


class RegulatoryComplianceMapRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    regulatory_uid: str = Field(..., min_length=1, max_length=128)
    compliance_uid: str = Field(..., min_length=1, max_length=128)
    relationship_type: str = Field(default="implements", min_length=1, max_length=128)
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)


class ComplianceReportRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    framework: str = Field(default="SOC2", min_length=1, max_length=64)
    data_points: list[dict[str, Any]] = Field(default_factory=list)

