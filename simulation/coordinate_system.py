"""
Unified Coordinate System

Enterprise-grade 17-axis coordinate framework for UKG.
Implements Nuremberg hierarchical numbering and SAM.gov-style
canonical naming with organic ID preservation.

Every knowledge element is uniquely identified, hierarchically
located, and deterministically parseable.
"""

import logging
import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# Axis Groups
# =============================================================================

class AxisGroup(Enum):
    """The four axis groups."""
    KNOWLEDGE = "knowledge"       # Axes 1-7: What the knowledge is about
    PERSONA = "persona"           # Axes 8-11: Who reasons about it
    CONTEXT = "context"           # Axes 12-13: Where and when
    GOVERNANCE = "governance"     # Axes 14-17: How it's handled, trusted, and controlled


# =============================================================================
# A14-17 Canonical States (Governance Axes)
# =============================================================================

class SourceProvenance(Enum):
    """A14 - Where did this knowledge come from?"""
    FED_REGISTER = "fed_register"
    INTERNAL_KB = "internal_kb"
    VENDOR_DATA = "vendor_data"
    ACADEMIC_JOURNAL = "academic_journal"
    STANDARDS_BODY = "standards_body"
    LLM_GENERATED = "llm_generated"
    HUMAN_AUTHORED = "human_authored"
    HYBRID = "hybrid"  # Multi-source


class ObjectType(Enum):
    """A15 - What kind of thing is this?"""
    STATUTE = "statute"
    REGULATION = "regulation"
    CLAUSE = "clause"
    CONTROL = "control"
    REQUIREMENT = "requirement"
    PROCEDURE = "procedure"
    POLICY = "policy"
    DATASET = "dataset"
    METRIC = "metric"
    MODEL_OUTPUT = "model_output"
    SCENARIO = "scenario"
    RECOMMENDATION = "recommendation"
    ENTITY = "entity"
    ROLE = "role"
    TEST = "test"


class ValidationState(Enum):
    """
    A16 - How verified is this?
    Progresses monotonically. Cannot skip levels.
    """
    RAW = (0, "raw")
    INGESTED = (1, "ingested")
    NORMALIZED = (2, "normalized")
    CROSS_REFERENCED = (3, "cross_referenced")
    CURATED = (4, "curated")
    VALIDATED = (5, "validated")
    AUDITED = (6, "audited")
    CERTIFIED = (7, "certified")
    
    def __init__(self, level: int, label: str):
        self.level = level
        self.label = label
    
    def __ge__(self, other):
        return self.level >= other.level
    
    def __gt__(self, other):
        return self.level > other.level
    
    def __le__(self, other):
        return self.level <= other.level
    
    def __lt__(self, other):
        return self.level < other.level


class SecurityClassification(Enum):
    """A17 - Who can see or use this?"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    CUI = "cui"  # Controlled Unclassified Information
    RESTRICTED = "restricted"
    SECRET = "secret"


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class OrganicMeta:
    """
    Preserved organic identifiers.
    Canonical IDs never overwrite source identifiers.
    """
    source: str = ""           # e.g., "NAICS", "UKG_PILLAR"
    code: str = ""             # Original code
    name: str = ""             # Original name
    aliases: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "code": self.code,
            "name": self.name,
            "aliases": self.aliases
        }


@dataclass
class AxisValue:
    """
    Single axis value with Nuremberg numbering.
    """
    axis_number: int
    canonical_id: str           # Nuremberg-style: "1.32.4.2"
    canonical_name: str         # SAM-style: "ARTIFICIAL_INTELLIGENCE"
    organic: OrganicMeta = field(default_factory=OrganicMeta)
    
    # Optional hierarchy
    hierarchy_depth: int = 0
    parent_id: Optional[str] = None
    children: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "axis_number": self.axis_number,
            "canonical_id": self.canonical_id,
            "canonical_name": self.canonical_name,
            "organic": self.organic.to_dict(),
            "hierarchy_depth": self.hierarchy_depth,
            "parent_id": self.parent_id
        }


@dataclass
class AxisCoordinate:
    """
    Complete 17-axis coordinate tuple.
    
    Group I - Knowledge Organization (1-7):
        axis1_pillar: Top-level knowledge domain
        axis2_sector: Industry context (NAICS etc.)
        axis3_honeycomb: Cross-domain semantic bridges
        axis4_branch: Hierarchical sub-domains
        axis5_node: Interdisciplinary convergence
        axis6_octopus: Meta-regulatory aggregation
        axis7_spiderweb: Compliance constraint mesh
    
    Group II - Personas (8-11):
        axis8_knowledge: Knowledge Expert persona
        axis9_sector: Sector Expert persona
        axis10_regulatory: Regulatory Expert persona
        axis11_compliance: Compliance Expert persona
    
    Group III - Context (12-13):
        axis12_location: Jurisdiction, geography
        axis13_temporal: Time, version, validity
    
    Group IV - Governance (14-17):
        axis14_provenance: Where did this come from?
        axis15_object_type: What kind of thing is this?
        axis16_validation: How verified is it?
        axis17_security: Who can see/use it?
    """
    
    # Group I - Knowledge
    axis1_pillar: Optional[AxisValue] = None
    axis2_sector: Optional[AxisValue] = None
    axis3_honeycomb: List[AxisValue] = field(default_factory=list)
    axis4_branch: Optional[AxisValue] = None
    axis5_node: Optional[AxisValue] = None
    axis6_octopus: List[AxisValue] = field(default_factory=list)
    axis7_spiderweb: List[AxisValue] = field(default_factory=list)
    
    # Group II - Personas
    axis8_knowledge: Optional[AxisValue] = None
    axis9_sector: Optional[AxisValue] = None
    axis10_regulatory: Optional[AxisValue] = None
    axis11_compliance: Optional[AxisValue] = None
    
    # Group III - Context
    axis12_location: Optional[AxisValue] = None
    axis13_temporal: Optional[AxisValue] = None
    
    # Group IV - Governance (Meta-axes)
    axis14_provenance: Optional[AxisValue] = None        # Source lineage
    axis15_object_type: Optional[AxisValue] = None       # Semantic identity
    axis16_validation: Optional[AxisValue] = None        # Trust state
    axis17_security: Optional[AxisValue] = None          # Access control
    
    # Metadata
    coordinate_id: str = ""
    created_at: str = ""
    locked: bool = False
    
    def __post_init__(self):
        if not self.coordinate_id:
            self.coordinate_id = f"coord_{self._generate_hash()}"
        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()
    
    def _generate_hash(self) -> str:
        """Generate hash from axis values."""
        parts = [
            self.axis1_pillar.canonical_id if self.axis1_pillar else "",
            self.axis2_sector.canonical_id if self.axis2_sector else "",
            self.axis12_location.canonical_id if self.axis12_location else "",
            self.axis13_temporal.canonical_id if self.axis13_temporal else "",
        ]
        return hashlib.md5("|".join(parts).encode()).hexdigest()[:12]
    
    def get_axis(self, axis_number: int) -> Optional[AxisValue]:
        """Get axis value by number."""
        axis_map = {
            1: self.axis1_pillar,
            2: self.axis2_sector,
            4: self.axis4_branch,
            5: self.axis5_node,
            8: self.axis8_knowledge,
            9: self.axis9_sector,
            10: self.axis10_regulatory,
            11: self.axis11_compliance,
            12: self.axis12_location,
            13: self.axis13_temporal,
            14: self.axis14_provenance,
            15: self.axis15_object_type,
            16: self.axis16_validation,
            17: self.axis17_security,
        }
        return axis_map.get(axis_number)
    
    def to_compact_string(self) -> str:
        """Compressed coordinate string for logging."""
        parts = []
        for i in [1, 2, 4, 5, 12, 13]:
            axis = self.get_axis(i)
            if axis:
                parts.append(f"A{i}={axis.canonical_id}")
        return " | ".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Full serialization."""
        return {
            "coordinate_id": self.coordinate_id,
            "axis1_pillar": self.axis1_pillar.to_dict() if self.axis1_pillar else None,
            "axis2_sector": self.axis2_sector.to_dict() if self.axis2_sector else None,
            "axis3_honeycomb": [a.to_dict() for a in self.axis3_honeycomb],
            "axis4_branch": self.axis4_branch.to_dict() if self.axis4_branch else None,
            "axis5_node": self.axis5_node.to_dict() if self.axis5_node else None,
            "axis6_octopus": [a.to_dict() for a in self.axis6_octopus],
            "axis7_spiderweb": [a.to_dict() for a in self.axis7_spiderweb],
            "axis8_knowledge": self.axis8_knowledge.to_dict() if self.axis8_knowledge else None,
            "axis9_sector": self.axis9_sector.to_dict() if self.axis9_sector else None,
            "axis10_regulatory": self.axis10_regulatory.to_dict() if self.axis10_regulatory else None,
            "axis11_compliance": self.axis11_compliance.to_dict() if self.axis11_compliance else None,
            "axis12_location": self.axis12_location.to_dict() if self.axis12_location else None,
            "axis13_temporal": self.axis13_temporal.to_dict() if self.axis13_temporal else None,
            "axis14_provenance": self.axis14_provenance.to_dict() if self.axis14_provenance else None,
            "axis15_object_type": self.axis15_object_type.to_dict() if self.axis15_object_type else None,
            "axis16_validation": self.axis16_validation.to_dict() if self.axis16_validation else None,
            "axis17_security": self.axis17_security.to_dict() if self.axis17_security else None,
            "created_at": self.created_at,
            "locked": self.locked
        }


# =============================================================================
# Coordinate Builder
# =============================================================================

class CoordinateBuilder:
    """
    Builds AxisCoordinate instances with Nuremberg numbering
    and SAM.gov canonical naming.
    """
    
    def __init__(self):
        self._coordinate = AxisCoordinate()
    
    def reset(self) -> "CoordinateBuilder":
        """Reset builder."""
        self._coordinate = AxisCoordinate()
        return self
    
    def with_pillar(
        self,
        pillar_id: str,
        name: str,
        organic_code: str = None,
        organic_source: str = "UKG_PILLAR"
    ) -> "CoordinateBuilder":
        """Set Axis 1 (Pillar)."""
        canonical_id = f"1.{pillar_id}"
        canonical_name = self._to_sam_name(name)
        
        self._coordinate.axis1_pillar = AxisValue(
            axis_number=1,
            canonical_id=canonical_id,
            canonical_name=canonical_name,
            organic=OrganicMeta(
                source=organic_source,
                code=organic_code or pillar_id,
                name=name
            )
        )
        return self
    
    def with_sector(
        self,
        sector_code: str,
        name: str,
        code_system: str = "NAICS"
    ) -> "CoordinateBuilder":
        """Set Axis 2 (Sector)."""
        canonical_id = f"2.{code_system}.{sector_code}"
        canonical_name = self._to_sam_name(name)
        
        self._coordinate.axis2_sector = AxisValue(
            axis_number=2,
            canonical_id=canonical_id,
            canonical_name=canonical_name,
            organic=OrganicMeta(
                source=code_system,
                code=sector_code,
                name=name
            )
        )
        return self
    
    def with_location(
        self,
        region: str,
        country: str = None,
        state: str = None,
        authority: str = None
    ) -> "CoordinateBuilder":
        """Set Axis 12 (Location)."""
        parts = [region]
        if country:
            parts.append(country)
        if state:
            parts.append(state)
        if authority:
            parts.append(authority)
        
        canonical_id = "12." + ".".join(parts)
        canonical_name = "_".join(parts).upper()
        
        self._coordinate.axis12_location = AxisValue(
            axis_number=12,
            canonical_id=canonical_id,
            canonical_name=canonical_name,
            organic=OrganicMeta(
                source="ISO_3166",
                code=".".join(parts),
                name=f"{region}/{country or ''}/{state or ''}"
            )
        )
        return self
    
    def with_temporal(
        self,
        year: int,
        quarter: str = None,
        version: str = None
    ) -> "CoordinateBuilder":
        """Set Axis 13 (Temporal)."""
        parts = [str(year)]
        if quarter:
            parts.append(quarter)
        if version:
            parts.append(version)
        
        canonical_id = "13." + ".".join(parts)
        canonical_name = f"YEAR_{year}"
        
        self._coordinate.axis13_temporal = AxisValue(
            axis_number=13,
            canonical_id=canonical_id,
            canonical_name=canonical_name,
            organic=OrganicMeta(
                source="ISO_8601",
                code=".".join(parts),
                name=f"{year} {quarter or ''}"
            )
        )
        return self
    
    def with_persona(
        self,
        axis: int,
        profile_id: str,
        name: str
    ) -> "CoordinateBuilder":
        """Set persona axis (8-11)."""
        if axis not in [8, 9, 10, 11]:
            raise ValueError(f"Invalid persona axis: {axis}")
        
        canonical_id = f"{axis}.{profile_id}"
        canonical_name = self._to_sam_name(name)
        
        value = AxisValue(
            axis_number=axis,
            canonical_id=canonical_id,
            canonical_name=canonical_name,
            organic=OrganicMeta(
                source="PERSONA_REGISTRY",
                code=profile_id,
                name=name
            )
        )
        
        if axis == 8:
            self._coordinate.axis8_knowledge = value
        elif axis == 9:
            self._coordinate.axis9_sector = value
        elif axis == 10:
            self._coordinate.axis10_regulatory = value
        elif axis == 11:
            self._coordinate.axis11_compliance = value
        
        return self
    
    def with_regulatory(self, regulations: List[Dict[str, str]]) -> "CoordinateBuilder":
        """Add Axis 6 (Octopus - regulatory mesh)."""
        for reg in regulations:
            self._coordinate.axis6_octopus.append(AxisValue(
                axis_number=6,
                canonical_id=f"6.{reg.get('jurisdiction', 'US')}.{reg.get('code', '')}",
                canonical_name=self._to_sam_name(reg.get("name", "")),
                organic=OrganicMeta(
                    source="REGULATORY",
                    code=reg.get("code", ""),
                    name=reg.get("name", "")
                )
            ))
        return self
    
    def with_provenance(
        self,
        source: "SourceProvenance",
        lineage_hash: str = None,
        additional_sources: List[str] = None
    ) -> "CoordinateBuilder":
        """Set Axis 14 (Provenance - Where did this come from?)."""
        canonical_id = f"14.{source.value}"
        self._coordinate.axis14_provenance = AxisValue(
            axis_number=14,
            canonical_id=canonical_id,
            canonical_name=f"SOURCE_{source.name}",
            organic=OrganicMeta(
                source="PROVENANCE",
                code=source.value,
                name=source.value,
                aliases=additional_sources or []
            )
        )
        return self
    
    def with_object_type(
        self,
        obj_type: "ObjectType"
    ) -> "CoordinateBuilder":
        """Set Axis 15 (Object Type - What kind of thing is this?)."""
        canonical_id = f"15.{obj_type.value}"
        self._coordinate.axis15_object_type = AxisValue(
            axis_number=15,
            canonical_id=canonical_id,
            canonical_name=f"TYPE_{obj_type.name}",
            organic=OrganicMeta(
                source="OBJECT_TYPE",
                code=obj_type.value,
                name=obj_type.value
            )
        )
        return self
    
    def with_validation_state(
        self,
        state: "ValidationState",
        validators: List[str] = None,
        confidence: float = None
    ) -> "CoordinateBuilder":
        """Set Axis 16 (Validation State - How verified is this?)."""
        canonical_id = f"16.{state.level}.{state.label}"
        self._coordinate.axis16_validation = AxisValue(
            axis_number=16,
            canonical_id=canonical_id,
            canonical_name=f"VALIDATION_{state.name}",
            organic=OrganicMeta(
                source="VALIDATION",
                code=str(state.level),
                name=state.label,
                aliases=validators or []
            )
        )
        return self
    
    def with_security(
        self,
        classification: "SecurityClassification",
        allowed_roles: List[str] = None,
        exportable: bool = True
    ) -> "CoordinateBuilder":
        """Set Axis 17 (Security - Who can see/use this?)."""
        canonical_id = f"17.{classification.value}"
        self._coordinate.axis17_security = AxisValue(
            axis_number=17,
            canonical_id=canonical_id,
            canonical_name=f"ACCESS_{classification.name}",
            organic=OrganicMeta(
                source="SECURITY",
                code=classification.value,
                name=classification.value,
                aliases=allowed_roles or []
            )
        )
        return self
    
    def build(self) -> AxisCoordinate:
        """Build and return coordinate."""
        return self._coordinate
    
    def _to_sam_name(self, name: str) -> str:
        """Convert to SAM.gov style name."""
        # Uppercase, remove punctuation, replace spaces
        clean = re.sub(r'[^\w\s]', '', name.upper())
        return re.sub(r'\s+', '_', clean.strip())


# =============================================================================
# Coordinate System Service
# =============================================================================

class UnifiedCoordinateSystem:
    """
    Central coordinate system service.
    Manages coordinate creation, validation, and lookup.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize coordinate system."""
        self.config = config or {}
        self._coordinates: Dict[str, AxisCoordinate] = {}
        
        logger.info("UnifiedCoordinateSystem initialized")
    
    def create_coordinate(self) -> CoordinateBuilder:
        """Create a new coordinate builder."""
        return CoordinateBuilder()
    
    def register(self, coordinate: AxisCoordinate) -> str:
        """Register a coordinate and return its ID."""
        self._coordinates[coordinate.coordinate_id] = coordinate
        logger.info(f"Registered coordinate: {coordinate.coordinate_id}")
        return coordinate.coordinate_id
    
    def get(self, coordinate_id: str) -> Optional[AxisCoordinate]:
        """Get coordinate by ID."""
        return self._coordinates.get(coordinate_id)
    
    def validate(self, coordinate: AxisCoordinate) -> Tuple[bool, List[str]]:
        """Validate coordinate completeness."""
        errors = []
        
        # Required axes for most queries
        if not coordinate.axis1_pillar:
            errors.append("Missing Axis 1 (Pillar)")
        
        if not coordinate.axis12_location:
            errors.append("Missing Axis 12 (Location)")
        
        if not coordinate.axis13_temporal:
            errors.append("Missing Axis 13 (Temporal)")
        
        return len(errors) == 0, errors
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics."""
        return {
            "total_coordinates": len(self._coordinates)
        }


# =============================================================================
# Factory
# =============================================================================

def create_coordinate_system(config: Dict[str, Any] = None) -> UnifiedCoordinateSystem:
    """Create coordinate system instance."""
    return UnifiedCoordinateSystem(config)
