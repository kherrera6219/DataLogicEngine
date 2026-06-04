"""
POV Delta Normalizer & Evidence Binder

Enterprise-grade module for converting viewpoint outputs into structured,
mergeable deltas with schema validation, deduplication, and evidence binding.
"""

import logging
import uuid
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional, Set
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Constants
# =============================================================================

class DeltaType(Enum):
    """Types of POV deltas."""
    CONSTRAINT = "constraint"           # Hard requirement or blocker
    RISK = "risk"                       # Identified risk
    REQUIREMENT = "requirement"         # Missing requirement
    ASSUMPTION = "assumption"           # Unstated assumption
    QUESTION = "question"               # Needs resolution
    RECOMMENDATION = "recommendation"   # Suggested action
    GAP = "gap"                         # Coverage gap


class Severity(Enum):
    """Delta severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    
    @property
    def priority(self) -> int:
        """Numerical priority (lower = more urgent)."""
        return {"critical": 1, "high": 2, "medium": 3, "low": 4}[self.value]


class Lane(Enum):
    """Owner lanes for deltas."""
    KNOWLEDGE = "knowledge"
    SECTOR = "sector"
    REGULATORY = "regulatory"
    COMPLIANCE = "compliance"
    STAKEHOLDER = "stakeholder"
    CROSS_CUTTING = "cross_cutting"


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class EvidenceRef:
    """Reference to supporting evidence."""
    ref_id: str
    ref_type: str           # node/doc/memory/external
    uri: str                # Location reference
    relevance: float = 0.8  # 0-1 relevance score
    excerpt: str = ""       # Relevant snippet
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "ref_id": self.ref_id,
            "ref_type": self.ref_type,
            "uri": self.uri,
            "relevance": self.relevance,
            "excerpt": self.excerpt[:200] if self.excerpt else ""
        }


@dataclass
class POVDelta:
    """
    A single POV delta (finding/output).
    
    Represents a constraint, risk, requirement, or other finding
    from a viewpoint evaluation.
    """
    delta_id: str = ""
    delta_type: DeltaType = DeltaType.REQUIREMENT
    severity: Severity = Severity.MEDIUM
    owner_lane: Lane = Lane.CROSS_CUTTING
    
    # Content
    description: str = ""
    rationale: str = ""
    
    # Source
    source_viewpoint: str = ""
    source_lane: str = ""
    
    # Evidence
    evidence_refs: List[EvidenceRef] = field(default_factory=list)
    
    # Resolution
    resolved: bool = False
    resolution: str = ""
    resolution_method: str = ""
    
    # Metadata
    confidence: float = 0.8
    created_at: str = ""
    tags: List[str] = field(default_factory=list)
    
    # Deduplication
    content_hash: str = ""
    
    def __post_init__(self):
        if not self.delta_id:
            self.delta_id = f"delta_{uuid.uuid4().hex[:12]}"
        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()
        if not self.content_hash:
            self._compute_hash()
    
    def _compute_hash(self):
        """Compute content hash for deduplication."""
        content = f"{self.delta_type.value}:{self.description}:{self.owner_lane.value}"
        # Non-security content fingerprint for deduplication only.
        self.content_hash = hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()[:16]
    
    def add_evidence(self, evidence: EvidenceRef):
        """Add evidence reference."""
        self.evidence_refs.append(evidence)
    
    def mark_resolved(self, resolution: str, method: str = "manual"):
        """Mark delta as resolved."""
        self.resolved = True
        self.resolution = resolution
        self.resolution_method = method
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "delta_id": self.delta_id,
            "delta_type": self.delta_type.value,
            "severity": self.severity.value,
            "owner_lane": self.owner_lane.value,
            "description": self.description,
            "rationale": self.rationale,
            "source_viewpoint": self.source_viewpoint,
            "source_lane": self.source_lane,
            "evidence_refs": [e.to_dict() for e in self.evidence_refs],
            "resolved": self.resolved,
            "resolution": self.resolution,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "tags": self.tags,
            "content_hash": self.content_hash
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "POVDelta":
        """Create from dictionary."""
        evidence = [
            EvidenceRef(**e) for e in data.get("evidence_refs", [])
        ]
        
        return cls(
            delta_id=data.get("delta_id", ""),
            delta_type=DeltaType(data.get("delta_type", "requirement")),
            severity=Severity(data.get("severity", "medium")),
            owner_lane=Lane(data.get("owner_lane", "cross_cutting")),
            description=data.get("description", ""),
            rationale=data.get("rationale", ""),
            source_viewpoint=data.get("source_viewpoint", ""),
            source_lane=data.get("source_lane", ""),
            evidence_refs=evidence,
            resolved=data.get("resolved", False),
            resolution=data.get("resolution", ""),
            confidence=data.get("confidence", 0.8),
            tags=data.get("tags", [])
        )


@dataclass
class POVDeltaCollection:
    """
    Collection of POV deltas organized by type.
    
    Output format for Layer 5 integration.
    """
    constraints: List[POVDelta] = field(default_factory=list)
    risks: List[POVDelta] = field(default_factory=list)
    missing_requirements: List[POVDelta] = field(default_factory=list)
    assumptions: List[POVDelta] = field(default_factory=list)
    questions_to_resolve: List[POVDelta] = field(default_factory=list)
    recommendations: List[POVDelta] = field(default_factory=list)
    gaps: List[POVDelta] = field(default_factory=list)
    
    @property
    def total_count(self) -> int:
        """Total number of deltas."""
        return (len(self.constraints) + len(self.risks) + 
                len(self.missing_requirements) + len(self.assumptions) +
                len(self.questions_to_resolve) + len(self.recommendations) +
                len(self.gaps))
    
    @property
    def critical_count(self) -> int:
        """Count of critical/high severity items."""
        all_deltas = self._all_deltas()
        return sum(1 for d in all_deltas 
                   if d.severity in (Severity.CRITICAL, Severity.HIGH))
    
    @property
    def unresolved_count(self) -> int:
        """Count of unresolved items."""
        return sum(1 for d in self._all_deltas() if not d.resolved)
    
    def _all_deltas(self) -> List[POVDelta]:
        """Get all deltas as flat list."""
        return (self.constraints + self.risks + self.missing_requirements +
                self.assumptions + self.questions_to_resolve + 
                self.recommendations + self.gaps)
    
    def add_delta(self, delta: POVDelta):
        """Add delta to appropriate category."""
        if delta.delta_type == DeltaType.CONSTRAINT:
            self.constraints.append(delta)
        elif delta.delta_type == DeltaType.RISK:
            self.risks.append(delta)
        elif delta.delta_type == DeltaType.REQUIREMENT:
            self.missing_requirements.append(delta)
        elif delta.delta_type == DeltaType.ASSUMPTION:
            self.assumptions.append(delta)
        elif delta.delta_type == DeltaType.QUESTION:
            self.questions_to_resolve.append(delta)
        elif delta.delta_type == DeltaType.RECOMMENDATION:
            self.recommendations.append(delta)
        elif delta.delta_type == DeltaType.GAP:
            self.gaps.append(delta)
    
    def get_by_lane(self, lane: Lane) -> List[POVDelta]:
        """Get all deltas owned by a lane."""
        return [d for d in self._all_deltas() if d.owner_lane == lane]
    
    def get_by_severity(self, severity: Severity) -> List[POVDelta]:
        """Get all deltas of a severity level."""
        return [d for d in self._all_deltas() if d.severity == severity]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "constraints": [d.to_dict() for d in self.constraints],
            "risks": [d.to_dict() for d in self.risks],
            "missing_requirements": [d.to_dict() for d in self.missing_requirements],
            "assumptions": [d.to_dict() for d in self.assumptions],
            "questions_to_resolve": [d.to_dict() for d in self.questions_to_resolve],
            "recommendations": [d.to_dict() for d in self.recommendations],
            "gaps": [d.to_dict() for d in self.gaps],
            "summary": {
                "total_count": self.total_count,
                "critical_count": self.critical_count,
                "unresolved_count": self.unresolved_count
            }
        }


@dataclass 
class POVRecommendations:
    """Recommendations for next steps."""
    needs_more_retrieval: bool = False
    retrieval_hints: List[str] = field(default_factory=list)
    needs_recursion: bool = False
    recursion_reason: str = ""
    suggested_viewpoints: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "needs_more_retrieval": self.needs_more_retrieval,
            "retrieval_hints": self.retrieval_hints,
            "needs_recursion": self.needs_recursion,
            "recursion_reason": self.recursion_reason,
            "suggested_viewpoints": self.suggested_viewpoints
        }


@dataclass
class POVTelemetry:
    """Telemetry data for observability."""
    start_time: str = ""
    end_time: str = ""
    latency_ms: int = 0
    viewpoints_requested: int = 0
    viewpoints_run: int = 0
    viewpoints_failed: int = 0
    recursions: int = 0
    deltas_generated: int = 0
    evidence_bindings: int = 0
    budget_exceeded: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "latency_ms": self.latency_ms,
            "viewpoints_requested": self.viewpoints_requested,
            "viewpoints_run": self.viewpoints_run,
            "viewpoints_failed": self.viewpoints_failed,
            "recursions": self.recursions,
            "deltas_generated": self.deltas_generated,
            "evidence_bindings": self.evidence_bindings,
            "budget_exceeded": self.budget_exceeded
        }


@dataclass
class POVResponse:
    """
    Complete POV Engine response.
    
    Enterprise output format for Layer 5 integration.
    """
    response_id: str = ""
    query_id: str = ""
    
    # Selected viewpoints
    selected_viewpoints: List[str] = field(default_factory=list)
    
    # Deltas
    pov_deltas: POVDeltaCollection = field(default_factory=POVDeltaCollection)
    
    # Evidence bindings
    evidence_bindings: Dict[str, List[str]] = field(default_factory=dict)
    
    # Recommendations
    recommendations: POVRecommendations = field(default_factory=POVRecommendations)
    
    # Telemetry
    telemetry: POVTelemetry = field(default_factory=POVTelemetry)
    
    # Overall confidence
    confidence: float = 0.8
    
    def __post_init__(self):
        if not self.response_id:
            self.response_id = f"pov_resp_{uuid.uuid4().hex[:12]}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "response_id": self.response_id,
            "query_id": self.query_id,
            "selected_viewpoints": self.selected_viewpoints,
            "pov_deltas": self.pov_deltas.to_dict(),
            "evidence_bindings": self.evidence_bindings,
            "recommendations": self.recommendations.to_dict(),
            "telemetry": self.telemetry.to_dict(),
            "confidence": self.confidence
        }


# =============================================================================
# Delta Normalizer
# =============================================================================

class POVDeltaNormalizer:
    """
    Normalizes viewpoint outputs into structured POV deltas.
    
    Features:
    - Schema validation
    - Deduplication/clustering
    - Severity scoring
    - Evidence binding
    """
    
    # Keywords for severity classification
    CRITICAL_KEYWORDS = {
        "catastrophic", "critical", "blocker", "showstopper", "fatal",
        "safety", "life-threatening", "classified", "breach"
    }
    HIGH_KEYWORDS = {
        "major", "significant", "important", "urgent", "required",
        "compliance", "regulatory", "must", "mandatory"
    }
    MEDIUM_KEYWORDS = {
        "moderate", "should", "recommended", "consider", "review"
    }
    
    # Keywords for delta type classification
    CONSTRAINT_KEYWORDS = {"must", "required", "mandatory", "constraint", "blocker"}
    RISK_KEYWORDS = {"risk", "threat", "vulnerability", "exposure", "hazard"}
    REQUIREMENT_KEYWORDS = {"requirement", "need", "missing", "gap", "lack"}
    QUESTION_KEYWORDS = {"question", "unclear", "ambiguous", "clarify", "unknown"}
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the normalizer."""
        self.config = config or {}
        self._seen_hashes: Set[str] = set()
        
        logger.info("POVDeltaNormalizer initialized")
    
    def normalize(
        self,
        viewpoint_outputs: List[Dict[str, Any]],
        working_subgraph: Dict[str, Any] = None
    ) -> POVDeltaCollection:
        """
        Normalize viewpoint outputs into structured deltas.
        
        Args:
            viewpoint_outputs: Raw outputs from viewpoint execution
            working_subgraph: Reference to working subgraph for evidence binding
            
        Returns:
            POVDeltaCollection with normalized deltas
        """
        collection = POVDeltaCollection()
        self._seen_hashes.clear()
        
        for output in viewpoint_outputs:
            deltas = self._extract_deltas(output)
            
            for delta in deltas:
                # Validate schema
                if not self._validate_delta(delta):
                    logger.warning(f"Invalid delta from {output.get('viewpoint_id')}")
                    continue
                
                # Check for duplicates
                if self._is_duplicate(delta):
                    logger.debug(f"Skipping duplicate delta: {delta.content_hash}")
                    continue
                
                # Bind evidence
                if working_subgraph:
                    self._bind_evidence(delta, working_subgraph)
                
                # Add to collection
                collection.add_delta(delta)
                self._seen_hashes.add(delta.content_hash)
        
        logger.info(f"Normalized {collection.total_count} deltas from {len(viewpoint_outputs)} viewpoints")
        
        return collection
    
    def _extract_deltas(self, output: Dict[str, Any]) -> List[POVDelta]:
        """Extract deltas from a single viewpoint output."""
        deltas = []
        viewpoint_id = output.get("viewpoint_id", "unknown")
        source_lane = output.get("lane", "cross_cutting")
        
        # Extract from structured findings if present
        if "findings" in output:
            for finding in output["findings"]:
                delta = self._parse_finding(finding, viewpoint_id, source_lane)
                if delta:
                    deltas.append(delta)
        
        # Extract from narrative/text if present
        if "perspective" in output:
            perspective = output["perspective"]
            if isinstance(perspective, dict):
                for point in perspective.get("key_points", []):
                    delta = self._parse_text(point, viewpoint_id, source_lane)
                    if delta:
                        deltas.append(delta)
        
        # Extract from constraints/risks lists
        for field_name, delta_type in [
            ("constraints", DeltaType.CONSTRAINT),
            ("risks", DeltaType.RISK),
            ("requirements", DeltaType.REQUIREMENT),
            ("questions", DeltaType.QUESTION)
        ]:
            if field_name in output:
                for item in output[field_name]:
                    delta = POVDelta(
                        delta_type=delta_type,
                        description=item if isinstance(item, str) else item.get("description", ""),
                        source_viewpoint=viewpoint_id,
                        source_lane=source_lane,
                        severity=self._classify_severity(str(item)),
                        owner_lane=self._classify_lane(str(item), source_lane)
                    )
                    deltas.append(delta)
        
        return deltas
    
    def _parse_finding(
        self,
        finding: Dict[str, Any],
        viewpoint_id: str,
        source_lane: str
    ) -> Optional[POVDelta]:
        """Parse a structured finding into a delta."""
        try:
            delta_type = DeltaType(finding.get("type", "requirement"))
        except ValueError:
            delta_type = DeltaType.REQUIREMENT
        
        try:
            severity = Severity(finding.get("severity", "medium"))
        except ValueError:
            severity = self._classify_severity(finding.get("description", ""))
        
        try:
            owner_lane = Lane(finding.get("owner_lane", source_lane))
        except ValueError:
            owner_lane = Lane.CROSS_CUTTING
        
        return POVDelta(
            delta_type=delta_type,
            severity=severity,
            owner_lane=owner_lane,
            description=finding.get("description", ""),
            rationale=finding.get("rationale", ""),
            source_viewpoint=viewpoint_id,
            source_lane=source_lane,
            confidence=finding.get("confidence", 0.8),
            tags=finding.get("tags", [])
        )
    
    def _parse_text(
        self,
        text: str,
        viewpoint_id: str,
        source_lane: str
    ) -> Optional[POVDelta]:
        """Parse narrative text into a delta."""
        if not text or len(text) < 10:
            return None
        
        return POVDelta(
            delta_type=self._classify_type(text),
            severity=self._classify_severity(text),
            owner_lane=self._classify_lane(text, source_lane),
            description=text,
            source_viewpoint=viewpoint_id,
            source_lane=source_lane
        )
    
    def _classify_type(self, text: str) -> DeltaType:
        """Classify delta type from text."""
        text_lower = text.lower()
        
        if any(kw in text_lower for kw in self.CONSTRAINT_KEYWORDS):
            return DeltaType.CONSTRAINT
        if any(kw in text_lower for kw in self.RISK_KEYWORDS):
            return DeltaType.RISK
        if any(kw in text_lower for kw in self.QUESTION_KEYWORDS):
            return DeltaType.QUESTION
        if any(kw in text_lower for kw in self.REQUIREMENT_KEYWORDS):
            return DeltaType.REQUIREMENT
        
        return DeltaType.RECOMMENDATION
    
    def _classify_severity(self, text: str) -> Severity:
        """Classify severity from text."""
        text_lower = text.lower()
        
        if any(kw in text_lower for kw in self.CRITICAL_KEYWORDS):
            return Severity.CRITICAL
        if any(kw in text_lower for kw in self.HIGH_KEYWORDS):
            return Severity.HIGH
        if any(kw in text_lower for kw in self.MEDIUM_KEYWORDS):
            return Severity.MEDIUM
        
        return Severity.LOW
    
    def _classify_lane(self, text: str, default_lane: str) -> Lane:
        """Classify owner lane from text."""
        text_lower = text.lower()
        
        regulatory_kw = {"regulatory", "regulation", "law", "legal", "itar", "far"}
        compliance_kw = {"compliance", "audit", "control", "policy", "standard"}
        sector_kw = {"industry", "market", "business", "operational", "cost"}
        knowledge_kw = {"technical", "engineering", "design", "architecture"}
        
        if any(kw in text_lower for kw in regulatory_kw):
            return Lane.REGULATORY
        if any(kw in text_lower for kw in compliance_kw):
            return Lane.COMPLIANCE
        if any(kw in text_lower for kw in sector_kw):
            return Lane.SECTOR
        if any(kw in text_lower for kw in knowledge_kw):
            return Lane.KNOWLEDGE
        
        try:
            return Lane(default_lane)
        except ValueError:
            return Lane.CROSS_CUTTING
    
    def _validate_delta(self, delta: POVDelta) -> bool:
        """Validate delta against schema."""
        if not delta.description or len(delta.description) < 5:
            return False
        if not delta.source_viewpoint:
            return False
        return True
    
    def _is_duplicate(self, delta: POVDelta) -> bool:
        """Check if delta is a duplicate."""
        return delta.content_hash in self._seen_hashes
    
    def _bind_evidence(
        self,
        delta: POVDelta,
        working_subgraph: Dict[str, Any]
    ):
        """Bind evidence from working subgraph to delta."""
        # Simple keyword matching for evidence binding
        # In production, would use semantic similarity
        
        nodes = working_subgraph.get("nodes", [])
        description_lower = delta.description.lower()
        
        for node in nodes[:10]:  # Limit to prevent performance issues
            node_content = str(node.get("content", "")).lower()
            
            # Check for keyword overlap
            desc_words = set(w for w in description_lower.split() if len(w) > 4)
            node_words = set(w for w in node_content.split() if len(w) > 4)
            
            overlap = len(desc_words & node_words)
            if overlap >= 2:
                evidence = EvidenceRef(
                    ref_id=f"ev_{uuid.uuid4().hex[:8]}",
                    ref_type="node",
                    uri=f"node://{node.get('node_id', 'unknown')}",
                    relevance=min(0.95, 0.5 + overlap * 0.1),
                    excerpt=node_content[:100]
                )
                delta.add_evidence(evidence)


# =============================================================================
# Factory Function
# =============================================================================

def create_delta_normalizer(config: Dict[str, Any] = None) -> POVDeltaNormalizer:
    """Create and configure a POVDeltaNormalizer instance."""
    return POVDeltaNormalizer(config)
