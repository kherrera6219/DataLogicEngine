"""
Unified Artifact Envelope (UAE) Models

This module defines the standard envelope for all artifacts produced by the UKG system.
Every output from a Knowledge Algorithm, Simulation Layer, Persona, or Refinement Step
must be wrapped in a UnifiedArtifactEnvelope to ensure traceability and auditability.
"""

from datetime import datetime, UTC
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from core.coordinate_system import UnifiedCoordinate

class ProvenanceEntry(BaseModel):
    """Represents a single step in an artifact's provenance chain."""
    source_id: str = Field(..., description="ID of the component/KA/Persona that produced this")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    operation: str = Field(..., description="Action performed (e.g., 'retrieval', 'synthesis')")
    input_ids: List[str] = Field(default_factory=list, description="IDs of artifacts used as input")
    meta: Dict[str, Any] = Field(default_factory=dict)

class ConfidenceVector(BaseModel):
    """Multi-dimensional confidence metrics for the artifact."""
    overall: float = Field(0.0, ge=0.0, le=1.0)
    factual: Optional[float] = Field(None, ge=0.0, le=1.0)
    logical: Optional[float] = Field(None, ge=0.0, le=1.0)
    regulatory: Optional[float] = Field(None, ge=0.0, le=1.0)
    compliance: Optional[float] = Field(None, ge=0.0, le=1.0)
    semantic: Optional[float] = Field(None, ge=0.0, le=1.0)
    meta: Dict[str, float] = Field(default_factory=dict)

class UnifiedArtifactEnvelope(BaseModel):
    """
    The standard wrapper for every UKG output.
    Ensures that every piece of knowledge is coordinate-addressable and traceable.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True)

    artifact_id: str = Field(..., description="Canonical UKGID for this artifact")
    run_id: str = Field(..., description="Execution ID for the current simulation run")
    snapshot_id: Optional[str] = Field(None, description="FROST snapshot ID for state pinning")
    
    # Coordinate Plane
    coord17: UnifiedCoordinate = Field(..., description="Unified 17-axis coordinate data")
    
    # Numbering & Naming Plane
    numberpaths: List[str] = Field(default_factory=list, description="Hierarchical Nuremberg paths (UNS)")
    aliases: List[str] = Field(default_factory=list, description="Standard aliases (SAM.gov, NAICS, etc.)")
    
    # Trace & Governance Plane
    provenance: List[ProvenanceEntry] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list, description="IDs of supporting evidence nodes")
    trace_refs: List[str] = Field(default_factory=list, description="IDs of trace events in the audit log")
    confidence_vector: ConfidenceVector = Field(default_factory=ConfidenceVector)
    
    # Content Plane
    payload_type: str = Field(..., description="Type of the payload (e.g., 'ka_output', 'layer_result')")
    payload: Any = Field(..., description="The actual content/data of the artifact")
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_provenance(self, source_id: str, operation: str, input_ids: Optional[List[str]] = None):
        """Helper to add a provenance entry."""
        self.provenance.append(ProvenanceEntry(
            source_id=source_id,
            operation=operation,
            input_ids=input_ids or []
        ))
