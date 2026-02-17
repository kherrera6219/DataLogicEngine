"""
Pod Models for Persona Scaling System

This module defines data models for the Persona Scaling System, including:
- PodType enumeration
- ExpandedPersona for subsystem-specialized personas
- PodState for tracking pod processing state
- ScalingDecision for sufficiency tool output
- SubsystemProfile for domain-specific expert profiles
"""

import uuid
import logging
from enum import Enum
from datetime import datetime, UTC
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


logger = logging.getLogger(__name__)


class PodType(Enum):
    """Enumeration of pod types corresponding to the base quad personas."""
    KNOWLEDGE = "knowledge"
    SECTOR = "sector"
    REGULATORY = "regulatory"
    COMPLIANCE = "compliance"
    
    @classmethod
    def from_axis(cls, axis_number: int) -> Optional['PodType']:
        """Get pod type from axis number."""
        mapping = {
            8: cls.KNOWLEDGE,
            9: cls.SECTOR,
            10: cls.REGULATORY,
            11: cls.COMPLIANCE
        }
        return mapping.get(axis_number)
    
    @property
    def axis_number(self) -> int:
        """Get the corresponding axis number."""
        mapping = {
            PodType.KNOWLEDGE: 8,
            PodType.SECTOR: 9,
            PodType.REGULATORY: 10,
            PodType.COMPLIANCE: 11
        }
        return mapping[self]
    
    @property
    def max_personas(self) -> int:
        """Get maximum personas allowed in this pod type."""
        caps = {
            PodType.KNOWLEDGE: 6,
            PodType.SECTOR: 6,
            PodType.REGULATORY: 3,
            PodType.COMPLIANCE: 3
        }
        return caps[self]


@dataclass
class SubsystemProfile:
    """
    Profile for a subsystem-specific expert.
    
    Used to specialize personas based on detected subsystems in the query.
    """
    subsystem_id: str
    name: str
    domain: str
    specialization: str
    keywords: List[str] = field(default_factory=list)
    required_certifications: List[str] = field(default_factory=list)
    related_standards: List[str] = field(default_factory=list)
    
    # 7-part persona components tailored to this subsystem
    job_role: Dict[str, Any] = field(default_factory=dict)
    education: Dict[str, Any] = field(default_factory=dict)
    certifications: Dict[str, Any] = field(default_factory=dict)
    skills: Dict[str, Any] = field(default_factory=dict)
    training: Dict[str, Any] = field(default_factory=dict)
    career_path: Dict[str, Any] = field(default_factory=dict)
    related_jobs: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "subsystem_id": self.subsystem_id,
            "name": self.name,
            "domain": self.domain,
            "specialization": self.specialization,
            "keywords": self.keywords,
            "required_certifications": self.required_certifications,
            "related_standards": self.related_standards,
            "components": {
                "job_role": self.job_role,
                "education": self.education,
                "certifications": self.certifications,
                "skills": self.skills,
                "training": self.training,
                "career_path": self.career_path,
                "related_jobs": self.related_jobs
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SubsystemProfile':
        """Create from dictionary."""
        components = data.get("components", {})
        return cls(
            subsystem_id=data.get("subsystem_id", str(uuid.uuid4())),
            name=data.get("name", ""),
            domain=data.get("domain", ""),
            specialization=data.get("specialization", ""),
            keywords=data.get("keywords", []),
            required_certifications=data.get("required_certifications", []),
            related_standards=data.get("related_standards", []),
            job_role=components.get("job_role", {}),
            education=components.get("education", {}),
            certifications=components.get("certifications", {}),
            skills=components.get("skills", {}),
            training=components.get("training", {}),
            career_path=components.get("career_path", {}),
            related_jobs=components.get("related_jobs", {})
        )


@dataclass
class ExpandedPersona:
    """
    An expanded persona with subsystem specialization.
    
    Extends the base persona structure with:
    - Subsystem-specific expertise
    - Pod membership
    - Specialization context
    """
    persona_id: str
    pod_type: PodType
    name: str
    description: str
    subsystem_profile: Optional[SubsystemProfile] = None
    
    # Base persona components
    axis_number: int = 0
    persona_type: str = ""
    
    # 7-part persona structure
    components: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "job_role": {},
        "education": {},
        "certifications": {},
        "skills": {},
        "training": {},
        "career_path": {},
        "related_jobs": {}
    })
    
    # Processing state
    is_active: bool = True
    confidence: float = 0.0
    response: str = ""
    processing_time_ms: float = 0.0
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize derived fields."""
        if not self.axis_number:
            self.axis_number = self.pod_type.axis_number
        if not self.persona_type:
            self.persona_type = self.pod_type.value
    
    def set_component(self, component_type: str, data: Dict[str, Any]) -> bool:
        """Set data for a specific component."""
        if component_type not in self.components:
            logger.error(f"Invalid component type: {component_type}")
            return False
        self.components[component_type] = data
        return True
    
    def get_component(self, component_type: str) -> Dict[str, Any]:
        """Get data for a specific component."""
        return self.components.get(component_type, {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "persona_id": self.persona_id,
            "pod_type": self.pod_type.value,
            "name": self.name,
            "description": self.description,
            "axis_number": self.axis_number,
            "persona_type": self.persona_type,
            "components": self.components,
            "is_active": self.is_active,
            "confidence": self.confidence,
            "response": self.response,
            "processing_time_ms": self.processing_time_ms,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }
        if self.subsystem_profile:
            result["subsystem_profile"] = self.subsystem_profile.to_dict()
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExpandedPersona':
        """Create from dictionary."""
        subsystem_data = data.get("subsystem_profile")
        subsystem_profile = SubsystemProfile.from_dict(subsystem_data) if subsystem_data else None
        
        persona = cls(
            persona_id=data.get("persona_id", str(uuid.uuid4())),
            pod_type=PodType(data.get("pod_type", "knowledge")),
            name=data.get("name", ""),
            description=data.get("description", ""),
            subsystem_profile=subsystem_profile,
            axis_number=data.get("axis_number", 0),
            persona_type=data.get("persona_type", ""),
            is_active=data.get("is_active", True),
            confidence=data.get("confidence", 0.0),
            response=data.get("response", ""),
            processing_time_ms=data.get("processing_time_ms", 0.0),
            metadata=data.get("metadata", {})
        )
        
        # Load components
        components = data.get("components", {})
        for comp_type, comp_data in components.items():
            persona.set_component(comp_type, comp_data)
        
        # Parse timestamp
        if "created_at" in data:
            persona.created_at = datetime.fromisoformat(data["created_at"])
        
        return persona


@dataclass
class SufficiencySignals:
    """
    Signals used to determine if expansion is needed.
    
    These are computed from the query context and base quad results.
    """
    complexity_score: float = 0.0      # 0-100: Cross-domain breadth, reasoning depth
    stakes_score: float = 0.0          # 0-100: Domain criticality, user policy
    conflict_score: float = 0.0        # 0-1: Disagreement level between personas
    coverage_score: float = 1.0        # 0-1: How well personas answered their lens
    
    # Additional context signals
    pillars_activated: int = 0
    sectors_activated: int = 0
    subsystems_detected: int = 0
    regulatory_frameworks: int = 0
    
    # Derived flags
    is_high_assurance: bool = False
    is_defense_domain: bool = False
    has_safety_critical: bool = False
    has_export_control: bool = False
    
    def exceeds_thresholds(self, thresholds: Dict[str, float]) -> bool:
        """Check if any signal exceeds its threshold."""
        return (
            self.complexity_score > thresholds.get("complexity", 60) or
            self.stakes_score > thresholds.get("stakes", 40) or
            self.conflict_score > thresholds.get("conflict", 0.2) or
            self.coverage_score < thresholds.get("coverage", 0.85)
        )
    
    def get_expansion_reasons(self, thresholds: Dict[str, float]) -> List[str]:
        """Get list of reasons for expansion."""
        reasons = []
        
        if self.complexity_score > thresholds.get("complexity", 60):
            reasons.append(f"High complexity: {self.complexity_score:.1f} (threshold: {thresholds.get('complexity', 60)})")
        
        if self.stakes_score > thresholds.get("stakes", 40):
            reasons.append(f"High stakes: {self.stakes_score:.1f} (threshold: {thresholds.get('stakes', 40)})")
        
        if self.conflict_score > thresholds.get("conflict", 0.2):
            reasons.append(f"High conflict: {self.conflict_score:.2f} (threshold: {thresholds.get('conflict', 0.2)})")
        
        if self.coverage_score < thresholds.get("coverage", 0.85):
            reasons.append(f"Low coverage: {self.coverage_score:.2f} (threshold: {thresholds.get('coverage', 0.85)})")
        
        if self.is_defense_domain:
            reasons.append("Defense domain: requires expanded expert committee")
        
        if self.has_safety_critical:
            reasons.append("Safety-critical context: requires additional validation")
        
        if self.has_export_control:
            reasons.append("Export control context: requires ITAR/EAR expertise")
        
        if self.subsystems_detected > 3:
            reasons.append(f"Multiple subsystems detected: {self.subsystems_detected}")
        
        return reasons
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "complexity_score": self.complexity_score,
            "stakes_score": self.stakes_score,
            "conflict_score": self.conflict_score,
            "coverage_score": self.coverage_score,
            "pillars_activated": self.pillars_activated,
            "sectors_activated": self.sectors_activated,
            "subsystems_detected": self.subsystems_detected,
            "regulatory_frameworks": self.regulatory_frameworks,
            "is_high_assurance": self.is_high_assurance,
            "is_defense_domain": self.is_defense_domain,
            "has_safety_critical": self.has_safety_critical,
            "has_export_control": self.has_export_control
        }


@dataclass
class ExpansionPlan:
    """
    Plan for expanding personas into pods.
    
    Specifies how many personas to spawn in each pod lane.
    """
    spawn_counts: Dict[str, int] = field(default_factory=lambda: {
        "knowledge": 0,
        "sector": 0,
        "regulatory": 0,
        "compliance": 0
    })
    
    subsystems_to_spawn: Dict[str, List[str]] = field(default_factory=dict)
    reasons: List[str] = field(default_factory=list)
    
    # Caps
    caps: Dict[str, int] = field(default_factory=lambda: {
        "knowledge_max": 6,
        "sector_max": 6,
        "regulatory_max": 3,
        "compliance_max": 3
    })
    
    # Stop conditions
    stop_conditions: List[str] = field(default_factory=lambda: [
        "confidence >= 0.995",
        "no unresolved conflicts remain",
        "coverage score >= threshold per lane"
    ])
    
    @property
    def total_personas(self) -> int:
        """Get total personas to spawn across all pods."""
        return sum(self.spawn_counts.values())
    
    def get_spawn_for_pod(self, pod_type: PodType) -> int:
        """Get spawn count for a specific pod type."""
        return self.spawn_counts.get(pod_type.value, 0)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "spawn_counts": self.spawn_counts,
            "subsystems_to_spawn": self.subsystems_to_spawn,
            "reasons": self.reasons,
            "caps": self.caps,
            "stop_conditions": self.stop_conditions,
            "total_personas": self.total_personas
        }


@dataclass
class ScalingDecision:
    """
    Output of the Persona Sufficiency Tool.
    
    Contains the decision on whether to expand and the expansion plan.
    """
    mode: str = "quad_only"  # "quad_only" or "expanded_committee"
    signals: SufficiencySignals = field(default_factory=SufficiencySignals)
    expansion_plan: Optional[ExpansionPlan] = None
    
    # Decision metadata
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    threshold_mode: str = "standard"  # "standard" or "high_assurance"
    thresholds_used: Dict[str, float] = field(default_factory=dict)
    
    @property
    def should_expand(self) -> bool:
        """Check if expansion is recommended."""
        return self.mode == "expanded_committee"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "decision_id": self.decision_id,
            "mode": self.mode,
            "should_expand": self.should_expand,
            "signals": self.signals.to_dict(),
            "expansion_plan": self.expansion_plan.to_dict() if self.expansion_plan else None,
            "threshold_mode": self.threshold_mode,
            "thresholds_used": self.thresholds_used,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class PodState:
    """
    Processing state for a persona pod.
    
    Tracks the personas in the pod and their collective output.
    """
    pod_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pod_type: PodType = PodType.KNOWLEDGE
    
    # Personas in this pod
    personas: List[ExpandedPersona] = field(default_factory=list)
    
    # Processing state
    status: str = "initialized"  # initialized, processing, synthesizing, completed, failed
    current_phase: str = ""
    
    # Collective outputs
    individual_responses: Dict[str, str] = field(default_factory=dict)
    synthesized_output: str = ""
    collective_confidence: float = 0.0
    
    # Conflicts detected within this pod
    internal_conflicts: List[Dict[str, Any]] = field(default_factory=list)
    
    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: Optional[datetime] = None
    processing_time_ms: float = 0.0
    
    @property
    def persona_count(self) -> int:
        """Get number of personas in this pod."""
        return len(self.personas)
    
    @property
    def active_persona_count(self) -> int:
        """Get number of active personas."""
        return sum(1 for p in self.personas if p.is_active)
    
    def add_persona(self, persona: ExpandedPersona) -> bool:
        """Add a persona to this pod."""
        if persona.pod_type != self.pod_type:
            logger.error(f"Persona pod type mismatch: {persona.pod_type} != {self.pod_type}")
            return False
        
        if len(self.personas) >= self.pod_type.max_personas:
            logger.warning(f"Pod {self.pod_id} at capacity: {len(self.personas)}/{self.pod_type.max_personas}")
            return False
        
        self.personas.append(persona)
        return True
    
    def update_status(self, new_status: str, phase: str = ""):
        """Update pod status."""
        self.status = new_status
        if phase:
            self.current_phase = phase
        
        if new_status in ("completed", "failed"):
            self.completed_at = datetime.now(UTC)
            if self.created_at:
                self.processing_time_ms = (self.completed_at - self.created_at).total_seconds() * 1000
    
    def set_persona_response(self, persona_id: str, response: str, confidence: float):
        """Set response from a specific persona."""
        self.individual_responses[persona_id] = response
        
        for persona in self.personas:
            if persona.persona_id == persona_id:
                persona.response = response
                persona.confidence = confidence
                break
    
    def calculate_collective_confidence(self) -> float:
        """Calculate collective confidence from all personas."""
        if not self.personas:
            return 0.0
        
        confidences = [p.confidence for p in self.personas if p.is_active and p.confidence > 0]
        if not confidences:
            return 0.0
        
        # Weighted average with emphasis on higher confidences
        sorted_conf = sorted(confidences, reverse=True)
        weights = [1.0 / (i + 1) for i in range(len(sorted_conf))]
        total_weight = sum(weights)
        
        self.collective_confidence = sum(c * w for c, w in zip(sorted_conf, weights)) / total_weight
        return self.collective_confidence
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pod_id": self.pod_id,
            "pod_type": self.pod_type.value,
            "persona_count": self.persona_count,
            "active_persona_count": self.active_persona_count,
            "personas": [p.to_dict() for p in self.personas],
            "status": self.status,
            "current_phase": self.current_phase,
            "individual_responses": self.individual_responses,
            "synthesized_output": self.synthesized_output,
            "collective_confidence": self.collective_confidence,
            "internal_conflicts": self.internal_conflicts,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "processing_time_ms": self.processing_time_ms
        }


@dataclass
class CrossPodConflict:
    """
    A conflict detected between different pods.
    """
    conflict_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_pod: PodType = PodType.KNOWLEDGE
    target_pod: PodType = PodType.REGULATORY
    
    source_claim: str = ""
    target_claim: str = ""
    conflict_type: str = ""  # contradiction, tension, gap, ambiguity
    severity: str = "medium"  # low, medium, high, critical
    
    resolution: Optional[str] = None
    resolution_method: Optional[str] = None
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "conflict_id": self.conflict_id,
            "source_pod": self.source_pod.value,
            "target_pod": self.target_pod.value,
            "source_claim": self.source_claim,
            "target_claim": self.target_claim,
            "conflict_type": self.conflict_type,
            "severity": self.severity,
            "resolution": self.resolution,
            "resolution_method": self.resolution_method,
            "resolved": self.resolved
        }


@dataclass 
class ScalingOrchestrationState:
    """
    Complete state for persona scaling orchestration.
    
    Tracks all pods, conflicts, and synthesis progress.
    """
    orchestration_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query_id: str = ""
    query_text: str = ""
    
    # Decision
    scaling_decision: Optional[ScalingDecision] = None
    
    # Pods
    pods: Dict[str, PodState] = field(default_factory=dict)
    
    # Cross-pod state
    cross_pod_conflicts: List[CrossPodConflict] = field(default_factory=list)
    deconfliction_passes: int = 0
    max_deconfliction_passes: int = 3
    
    # Final synthesis
    final_synthesis: str = ""
    final_confidence: float = 0.0
    threshold_met: bool = False
    
    # Status
    status: str = "initialized"
    current_phase: str = ""
    
    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: Optional[datetime] = None
    
    def add_pod(self, pod: PodState):
        """Add a pod to the orchestration."""
        self.pods[pod.pod_type.value] = pod
    
    def get_pod(self, pod_type: PodType) -> Optional[PodState]:
        """Get a pod by type."""
        return self.pods.get(pod_type.value)
    
    def all_pods_completed(self) -> bool:
        """Check if all pods have completed processing."""
        return all(p.status == "completed" for p in self.pods.values())
    
    def has_unresolved_conflicts(self) -> bool:
        """Check if there are unresolved cross-pod conflicts."""
        return any(not c.resolved for c in self.cross_pod_conflicts)
    
    def update_status(self, new_status: str, phase: str = ""):
        """Update orchestration status."""
        self.status = new_status
        if phase:
            self.current_phase = phase
        
        if new_status in ("completed", "failed"):
            self.completed_at = datetime.now(UTC)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "orchestration_id": self.orchestration_id,
            "query_id": self.query_id,
            "query_text": self.query_text[:200] + "..." if len(self.query_text) > 200 else self.query_text,
            "scaling_decision": self.scaling_decision.to_dict() if self.scaling_decision else None,
            "pods": {k: v.to_dict() for k, v in self.pods.items()},
            "cross_pod_conflicts": [c.to_dict() for c in self.cross_pod_conflicts],
            "deconfliction_passes": self.deconfliction_passes,
            "final_synthesis": self.final_synthesis[:500] + "..." if len(self.final_synthesis) > 500 else self.final_synthesis,
            "final_confidence": self.final_confidence,
            "threshold_met": self.threshold_met,
            "status": self.status,
            "current_phase": self.current_phase,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
