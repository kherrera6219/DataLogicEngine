"""
Layer 3 Data Models
Defines the structured outputs for the Deep Research Agent Layer.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime, UTC
import uuid

@dataclass
class EvidenceItem:
    """
    A single unit of evidence gathered by a Persona.
    Corresponds to a fact, citation, or data point.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""              # The actual fact/claim text
    source_uri: str = ""           # URL, Doc Ref, or Memory ID
    source_type: str = "unknown"   # "web", "document", "memory", "inference"
    confidence: float = 0.0        # 0.0 to 1.0
    
    # Governance Axes (A14-A17)
    provenance: str = "unknown"    # A14: Who said this? (Author/Authority)
    object_type: str = "claim"     # A15: What is this? (Fact, Rule, Opinion)
    validation_state: str = "raw"  # A16: Has this been checked?
    security_level: str = "unclassified" # A17: Who can see this?
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "source_uri": self.source_uri,
            "source_type": self.source_type,
            "confidence": self.confidence,
            "provenance": self.provenance,
            "object_type": self.object_type,
            "validation_state": self.validation_state,
            "security_level": self.security_level,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }

@dataclass
class EvidencePack:
    """
    A collection of evidence gathered by the L3 Agents.
    This is the primary handoff object from L3 to L4.
    """
    pack_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    items: List[EvidenceItem] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)  # Questions unable to be answered
    
    # Metadata about the research process
    research_tier: str = "tier1" # tier1, tier2, tier3
    agents_involved: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def add_item(self, item: EvidenceItem):
        self.items.append(item)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "items": [item.to_dict() for item in self.items],
            "gaps": self.gaps,
            "research_tier": self.research_tier,
            "agents_involved": self.agents_involved,
            "created_at": self.created_at
        }

@dataclass
class PersonaReport:
    """
    The output of a single Persona Agent (e.g., Regulatory Expert).
    Contains claims, evidence references, and specific analysis.
    """
    persona_id: str
    persona_role: str # Knowledge, Sector, Regulatory, Compliance
    summary: str
    claims: List[str]             # High-level assertions
    evidence_refs: List[str]      # IDs of EvidenceItems that support these claims
    open_questions: List[str]
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "persona_id": self.persona_id,
            "persona_role": self.persona_role,
            "summary": self.summary,
            "claims": self.claims,
            "evidence_refs": self.evidence_refs,
            "open_questions": self.open_questions,
            "confidence": self.confidence
        }

# --- Layer 1 & 2 Models (Refactor) ---

@dataclass
class Coord17Intent:
    """
    Layer 1 Artifact: What the system INTENDS to retrieve.
    Maps to the 17-Axis Coordinate System.
    """
    # Core Axes (1-5)
    axis_1_pillar: List[str] = field(default_factory=list)
    axis_2_sector: List[str] = field(default_factory=list)
    axis_3_topic: List[str] = field(default_factory=list)
    axis_4_method: List[str] = field(default_factory=list)
    axis_5_tool: List[str] = field(default_factory=list)
    
    # Governance Axes (6-7, 14-17)
    axis_6_regulation: List[str] = field(default_factory=list)
    axis_7_standard: List[str] = field(default_factory=list)
    axis_14_provenance: List[str] = field(default_factory=list) # e.g. "Primary Source", "Internal"
    axis_15_object_type: List[str] = field(default_factory=list)
    axis_16_validation: List[str] = field(default_factory=list)
    axis_17_security: List[str] = field(default_factory=list) # e.g. "Unclassified", "Secret"

    # Context Axes (12-13)
    axis_12_location: List[str] = field(default_factory=list)
    axis_13_time: List[str] = field(default_factory=list)
    
    # Unset/Ambiguous Axes (to be resolved by L2 or Questions)
    ambiguous_axes: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

@dataclass
class ProblemSpec:
    """
    Layer 1 Artifact: Machine-readable specification of the user's problem.
    """
    task_type: str = "unknown" # explain, compare, design, compliance_check
    success_criteria: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list) # e.g. "no_external_search"
    ambiguities: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__

@dataclass
class TierPlan:
    """
    Layer 1 Artifact: Execution Plan (Budget & Routing).
    Wraps the QAS TierDecision.
    """
    tier: int = 3
    tier_name: str = "standard"
    allowed_layers: List[int] = field(default_factory=list)
    max_budget_ms: int = 5000
    features_enabled: List[str] = field(default_factory=list) # e.g. "deep_research", "frost"
    
    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__

@dataclass
class RetrievalPlan:
    """
    Layer 2 Artifact: Internals for HOW to fetch data.
    """
    search_queries: List[str] = field(default_factory=list)
    target_indices: List[str] = field(default_factory=list) # e.g. "regulatory_db", "internal_kb"
    filters: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__

@dataclass
class Coord17Bindings:
    """
    Layer 2 Artifact: What was ACTUALLY found (Resolved Coordinates).
    Attached to the WorkingSubgraph.
    """
    resolved_axes: Dict[int, List[str]] = field(default_factory=dict)
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__
