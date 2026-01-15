"""
Viewpoint Registry

Enterprise-grade governed catalog of approved viewpoint definitions.
Provides versioned profiles with domain restrictions, evidence requirements,
and RBAC placeholders.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional, Set
from enum import Enum
import json

logger = logging.getLogger(__name__)


# =============================================================================
# Data Models
# =============================================================================

@dataclass
class ExpertProfile:
    """
    7-part expert profile for a viewpoint.
    
    Based on the Quad Persona component structure.
    """
    job_role: Dict[str, Any] = field(default_factory=dict)
    education: Dict[str, Any] = field(default_factory=dict)
    certifications: Dict[str, Any] = field(default_factory=dict)
    skills: Dict[str, Any] = field(default_factory=dict)
    training: Dict[str, Any] = field(default_factory=dict)
    career_path: Dict[str, Any] = field(default_factory=dict)
    related_jobs: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "job_role": self.job_role,
            "education": self.education,
            "certifications": self.certifications,
            "skills": self.skills,
            "training": self.training,
            "career_path": self.career_path,
            "related_jobs": self.related_jobs
        }


@dataclass
class RedactionPolicy:
    """Policy for redacting sensitive information."""
    redact_pii: bool = True
    redact_classified: bool = True
    redact_proprietary: bool = True
    allowed_classification_levels: List[str] = field(default_factory=lambda: ["UNCLASSIFIED"])
    max_output_length: int = 10000
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "redact_pii": self.redact_pii,
            "redact_classified": self.redact_classified,
            "redact_proprietary": self.redact_proprietary,
            "allowed_classification_levels": self.allowed_classification_levels,
            "max_output_length": self.max_output_length
        }


@dataclass
class ViewpointProfile:
    """
    Complete viewpoint profile definition.
    
    Version-controlled and governance-ready.
    """
    id: str
    name: str
    lane: str  # Knowledge/Sector/Regulatory/Compliance/Stakeholder
    
    # Domain restrictions
    allowed_domains: List[str] = field(default_factory=list)
    blocked_domains: List[str] = field(default_factory=list)
    
    # Evidence requirements
    required_evidence_types: List[str] = field(default_factory=list)
    
    # Versioning
    prompt_template_version: str = "1.0.0"
    output_schema_version: str = "1.0.0"
    
    # Governance
    redaction_policy: RedactionPolicy = field(default_factory=RedactionPolicy)
    
    # Expert profile
    expert_profile: ExpertProfile = field(default_factory=ExpertProfile)
    
    # Metadata
    description: str = ""
    keywords: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    created_by: str = "system"
    approved_by: str = ""
    status: str = "active"  # active/deprecated/pending_review
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(UTC).isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
    
    def is_allowed_for_domain(self, domain: str) -> bool:
        """Check if viewpoint is allowed for a domain."""
        domain_lower = domain.lower()
        
        # Check blocked first
        if self.blocked_domains:
            if domain_lower in [d.lower() for d in self.blocked_domains]:
                return False
        
        # Check allowed (empty = all allowed)
        if self.allowed_domains:
            return domain_lower in [d.lower() for d in self.allowed_domains]
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "lane": self.lane,
            "allowed_domains": self.allowed_domains,
            "blocked_domains": self.blocked_domains,
            "required_evidence_types": self.required_evidence_types,
            "prompt_template_version": self.prompt_template_version,
            "output_schema_version": self.output_schema_version,
            "redaction_policy": self.redaction_policy.to_dict(),
            "expert_profile": self.expert_profile.to_dict(),
            "description": self.description,
            "keywords": self.keywords,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by,
            "approved_by": self.approved_by,
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ViewpointProfile":
        """Create from dictionary."""
        redaction = RedactionPolicy(**data.get("redaction_policy", {}))
        expert = ExpertProfile(**data.get("expert_profile", {}))
        
        return cls(
            id=data["id"],
            name=data["name"],
            lane=data["lane"],
            allowed_domains=data.get("allowed_domains", []),
            blocked_domains=data.get("blocked_domains", []),
            required_evidence_types=data.get("required_evidence_types", []),
            prompt_template_version=data.get("prompt_template_version", "1.0.0"),
            output_schema_version=data.get("output_schema_version", "1.0.0"),
            redaction_policy=redaction,
            expert_profile=expert,
            description=data.get("description", ""),
            keywords=data.get("keywords", []),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            created_by=data.get("created_by", "system"),
            approved_by=data.get("approved_by", ""),
            status=data.get("status", "active")
        )


# =============================================================================
# Viewpoint Registry
# =============================================================================

class ViewpointRegistry:
    """
    Governed catalog of approved viewpoint definitions.
    
    Features:
    - Version-controlled profiles
    - Domain restrictions
    - RBAC placeholders
    - Audit logging
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the registry."""
        self.config = config or {}
        
        # In-memory registry
        self._profiles: Dict[str, ViewpointProfile] = {}
        
        # Audit log
        self._audit_log: List[Dict[str, Any]] = []
        
        # Load built-in profiles
        self._load_builtin_profiles()
        
        logger.info(f"ViewpointRegistry initialized with {len(self._profiles)} profiles")
    
    def _load_builtin_profiles(self):
        """Load built-in viewpoint profiles."""
        
        # ===== KNOWLEDGE LANE =====
        self._register_profile(ViewpointProfile(
            id="radar_sme",
            name="Radar Systems SME",
            lane="knowledge",
            allowed_domains=["defense", "aerospace", "technology"],
            required_evidence_types=["technical_spec", "mil_std"],
            description="Expert in AESA radar systems and modes",
            keywords=["radar", "aesa", "apg", "detection", "tracking"],
            expert_profile=ExpertProfile(
                job_role={"title": "Radar Systems Engineer", "level": "Principal"},
                education={"degree": "MS/PhD Electrical Engineering", "focus": "RF Systems"},
                certifications={"items": ["Security Clearance", "Radar Certification"]},
                skills={"items": ["Antenna Design", "Signal Processing", "RF Engineering"]}
            )
        ))
        
        self._register_profile(ViewpointProfile(
            id="ew_sme",
            name="Electronic Warfare SME",
            lane="knowledge",
            allowed_domains=["defense", "aerospace"],
            required_evidence_types=["technical_spec", "threat_data"],
            description="Expert in EW attack, protection, and support",
            keywords=["electronic warfare", "ew", "jamming", "countermeasures"],
            expert_profile=ExpertProfile(
                job_role={"title": "EW Systems Engineer", "level": "Senior"},
                education={"degree": "MS Electrical Engineering", "focus": "EW"},
                skills={"items": ["Signal Processing", "Threat Analysis", "ECM Design"]}
            )
        ))
        
        self._register_profile(ViewpointProfile(
            id="avionics_sme",
            name="Avionics Systems SME",
            lane="knowledge",
            allowed_domains=["defense", "aerospace", "aviation"],
            required_evidence_types=["technical_spec", "do178"],
            description="Expert in mission computers and integrated avionics",
            keywords=["avionics", "mission computer", "cockpit", "displays"],
            expert_profile=ExpertProfile(
                job_role={"title": "Avionics Systems Engineer", "level": "Principal"},
                education={"degree": "MS Computer Engineering"},
                certifications={"items": ["DO-178C", "Security Clearance"]},
                skills={"items": ["Real-time Systems", "Ada/C++", "Integration"]}
            )
        ))
        
        self._register_profile(ViewpointProfile(
            id="software_sme",
            name="Software Integration SME",
            lane="knowledge",
            allowed_domains=["defense", "aerospace", "technology"],
            required_evidence_types=["technical_spec", "do178", "test_results"],
            description="Expert in mission software and OFP development",
            keywords=["software", "ofp", "integration", "testing"],
            expert_profile=ExpertProfile(
                job_role={"title": "Software Systems Engineer", "level": "Principal"},
                education={"degree": "MS Computer Science"},
                certifications={"items": ["DO-178C", "CMMI"]},
                skills={"items": ["Ada", "Real-time Systems", "Integration Testing"]}
            )
        ))
        
        # ===== SECTOR LANE =====
        self._register_profile(ViewpointProfile(
            id="program_manager",
            name="Program Manager",
            lane="sector",
            allowed_domains=["defense", "government", "aerospace"],
            required_evidence_types=["schedule", "cost_estimate", "risk_register"],
            description="Expert in defense acquisition and program execution",
            keywords=["program", "cost", "schedule", "milestone", "acquisition"],
            expert_profile=ExpertProfile(
                job_role={"title": "Program Manager", "level": "Director"},
                education={"degree": "MBA/MS Program Management"},
                certifications={"items": ["PMP", "DAU Level III"]},
                skills={"items": ["Earned Value", "Schedule Management", "Risk"]}
            )
        ))
        
        self._register_profile(ViewpointProfile(
            id="sustainment_sme",
            name="Sustainment SME",
            lane="sector",
            description="Expert in weapon system sustainment and readiness",
            keywords=["sustainment", "readiness", "depot", "maintenance"],
            expert_profile=ExpertProfile(
                job_role={"title": "Sustainment Manager", "level": "Senior"},
                skills={"items": ["Reliability Engineering", "Supply Chain", "Depot Ops"]}
            )
        ))
        
        self._register_profile(ViewpointProfile(
            id="operator",
            name="Operational User",
            lane="sector",
            description="Expert in operational employment and tactics",
            keywords=["operational", "tactics", "employment", "mission"],
            expert_profile=ExpertProfile(
                job_role={"title": "Operational Requirements Officer", "level": "Lt Col"},
                skills={"items": ["Tactics", "Mission Planning", "Requirements"]}
            )
        ))
        
        # ===== REGULATORY LANE =====
        self._register_profile(ViewpointProfile(
            id="airworthiness_sme",
            name="Airworthiness Authority",
            lane="regulatory",
            required_evidence_types=["safety_analysis", "hazard_assessment"],
            description="Expert in flight safety and airworthiness certification",
            keywords=["airworthiness", "safety", "certification", "mea"],
            expert_profile=ExpertProfile(
                job_role={"title": "Airworthiness Engineer", "level": "Senior"},
                certifications={"items": ["ASP", "Flight Safety"]},
                skills={"items": ["Safety Analysis", "Certification", "Hazard Assessment"]}
            )
        ))
        
        self._register_profile(ViewpointProfile(
            id="export_control_sme",
            name="Export Control Officer",
            lane="regulatory",
            allowed_domains=["defense", "technology"],
            required_evidence_types=["classification", "license"],
            description="Expert in ITAR/EAR export regulations",
            keywords=["itar", "ear", "export", "technology control"],
            expert_profile=ExpertProfile(
                job_role={"title": "Export Control Officer", "level": "Manager"},
                education={"degree": "JD/MS International Trade"},
                skills={"items": ["Export Classification", "License Applications", "TCP"]}
            )
        ))
        
        self._register_profile(ViewpointProfile(
            id="contracting_sme",
            name="Contracting Officer",
            lane="regulatory",
            allowed_domains=["defense", "government"],
            required_evidence_types=["contract", "far_dfars"],
            description="Expert in federal acquisition regulations",
            keywords=["contract", "far", "dfars", "acquisition"],
            expert_profile=ExpertProfile(
                job_role={"title": "Contracting Officer", "level": "Senior"},
                certifications={"items": ["DAU Contracting Level III"]},
                skills={"items": ["Contract Negotiation", "FAR/DFARS", "Cost Analysis"]}
            )
        ))
        
        # ===== COMPLIANCE LANE =====
        self._register_profile(ViewpointProfile(
            id="rmf_sme",
            name="RMF/ATO Compliance",
            lane="compliance",
            required_evidence_types=["security_control", "poam"],
            description="Expert in Risk Management Framework and authorization",
            keywords=["rmf", "ato", "authorization", "security"],
            expert_profile=ExpertProfile(
                job_role={"title": "ISSO/ISSM", "level": "Senior"},
                certifications={"items": ["CISM", "CAP"]},
                skills={"items": ["RMF Process", "Security Controls", "POA&M"]}
            )
        ))
        
        self._register_profile(ViewpointProfile(
            id="quality_sme",
            name="Quality Compliance",
            lane="compliance",
            required_evidence_types=["audit_report", "nonconformance"],
            description="Expert in aerospace quality management",
            keywords=["quality", "as9100", "audit", "nonconformance"],
            expert_profile=ExpertProfile(
                job_role={"title": "Quality Manager", "level": "Senior"},
                certifications={"items": ["CQA", "Lead Auditor"]},
                skills={"items": ["Quality Systems", "Root Cause", "Audit"]}
            )
        ))
        
        self._register_profile(ViewpointProfile(
            id="auditor",
            name="Audit & Verification",
            lane="compliance",
            description="General audit and verification perspective",
            keywords=["audit", "verification", "assurance", "controls"],
            expert_profile=ExpertProfile(
                job_role={"title": "Internal Auditor", "level": "Senior"},
                skills={"items": ["Audit Planning", "Controls Testing", "Evidence"]}
            )
        ))
        
        # ===== STAKEHOLDER LANE =====
        self._register_profile(ViewpointProfile(
            id="decision_maker",
            name="Decision Maker",
            lane="stakeholder",
            description="Executive/leadership perspective",
            keywords=["decision", "executive", "leadership", "strategy"],
            expert_profile=ExpertProfile(
                job_role={"title": "Executive Director", "level": "SES"},
                skills={"items": ["Strategic Planning", "Resource Allocation", "Risk Mgmt"]}
            )
        ))
        
        self._register_profile(ViewpointProfile(
            id="administrator",
            name="Administrator",
            lane="stakeholder",
            description="Administrative and operational oversight",
            keywords=["administration", "operations", "implementation"],
            expert_profile=ExpertProfile(
                job_role={"title": "Operations Administrator", "level": "Manager"},
                skills={"items": ["Operations Management", "Implementation", "Coordination"]}
            )
        ))
        
        self._register_profile(ViewpointProfile(
            id="safety_advocate",
            name="Safety Advocate",
            lane="stakeholder",
            description="Safety and human factors perspective",
            keywords=["safety", "human factors", "risk", "protection"],
            expert_profile=ExpertProfile(
                job_role={"title": "Safety Officer", "level": "Senior"},
                skills={"items": ["Hazard Analysis", "Human Factors", "Safety Culture"]}
            )
        ))
    
    def _register_profile(self, profile: ViewpointProfile):
        """Register a profile (internal)."""
        self._profiles[profile.id] = profile
    
    # ===== CRUD Operations =====
    
    def get_profile(self, profile_id: str) -> Optional[ViewpointProfile]:
        """Get a profile by ID."""
        return self._profiles.get(profile_id)
    
    def list_profiles(
        self,
        lane: str = None,
        domain: str = None,
        status: str = "active"
    ) -> List[ViewpointProfile]:
        """List profiles with optional filtering."""
        profiles = list(self._profiles.values())
        
        if lane:
            profiles = [p for p in profiles if p.lane == lane]
        
        if domain:
            profiles = [p for p in profiles if p.is_allowed_for_domain(domain)]
        
        if status:
            profiles = [p for p in profiles if p.status == status]
        
        return profiles
    
    def add_profile(
        self,
        profile: ViewpointProfile,
        added_by: str = "system"
    ) -> bool:
        """
        Add a new profile to the registry.
        
        RBAC placeholder - would check permissions in production.
        """
        if profile.id in self._profiles:
            logger.warning(f"Profile {profile.id} already exists")
            return False
        
        profile.created_by = added_by
        profile.created_at = datetime.now(UTC).isoformat()
        profile.updated_at = profile.created_at
        profile.status = "pending_review"  # Require approval
        
        self._profiles[profile.id] = profile
        
        self._log_audit("add_profile", profile.id, added_by)
        logger.info(f"Added profile: {profile.id}")
        
        return True
    
    def update_profile(
        self,
        profile_id: str,
        updates: Dict[str, Any],
        updated_by: str = "system"
    ) -> bool:
        """
        Update an existing profile.
        
        RBAC placeholder - would check permissions in production.
        """
        if profile_id not in self._profiles:
            logger.warning(f"Profile {profile_id} not found")
            return False
        
        profile = self._profiles[profile_id]
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        profile.updated_at = datetime.now(UTC).isoformat()
        
        self._log_audit("update_profile", profile_id, updated_by, updates)
        logger.info(f"Updated profile: {profile_id}")
        
        return True
    
    def deprecate_profile(
        self,
        profile_id: str,
        deprecated_by: str = "system"
    ) -> bool:
        """Mark a profile as deprecated."""
        return self.update_profile(
            profile_id,
            {"status": "deprecated"},
            deprecated_by
        )
    
    def approve_profile(
        self,
        profile_id: str,
        approved_by: str
    ) -> bool:
        """Approve a pending profile."""
        if profile_id not in self._profiles:
            return False
        
        profile = self._profiles[profile_id]
        profile.status = "active"
        profile.approved_by = approved_by
        profile.updated_at = datetime.now(UTC).isoformat()
        
        self._log_audit("approve_profile", profile_id, approved_by)
        return True
    
    # ===== Query Methods =====
    
    def get_profiles_by_lane(self, lane: str) -> List[ViewpointProfile]:
        """Get all active profiles for a lane."""
        return [p for p in self._profiles.values() 
                if p.lane == lane and p.status == "active"]
    
    def get_profiles_for_domain(self, domain: str) -> List[ViewpointProfile]:
        """Get all profiles allowed for a domain."""
        return [p for p in self._profiles.values()
                if p.is_allowed_for_domain(domain) and p.status == "active"]
    
    def search_profiles(self, keyword: str) -> List[ViewpointProfile]:
        """Search profiles by keyword."""
        keyword_lower = keyword.lower()
        return [
            p for p in self._profiles.values()
            if keyword_lower in p.name.lower() or
               keyword_lower in p.description.lower() or
               any(keyword_lower in kw.lower() for kw in p.keywords)
        ]
    
    # ===== Audit =====
    
    def _log_audit(
        self,
        action: str,
        profile_id: str,
        actor: str,
        details: Dict[str, Any] = None
    ):
        """Log an audit event."""
        self._audit_log.append({
            "timestamp": datetime.now(UTC).isoformat(),
            "action": action,
            "profile_id": profile_id,
            "actor": actor,
            "details": details or {}
        })
    
    def get_audit_log(
        self,
        profile_id: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit log entries."""
        log = self._audit_log
        
        if profile_id:
            log = [e for e in log if e["profile_id"] == profile_id]
        
        return log[-limit:]
    
    # ===== Export/Import =====
    
    def export_profiles(self) -> List[Dict[str, Any]]:
        """Export all profiles as dictionaries."""
        return [p.to_dict() for p in self._profiles.values()]
    
    def import_profiles(
        self,
        profiles: List[Dict[str, Any]],
        imported_by: str = "system"
    ) -> int:
        """Import profiles from dictionaries."""
        count = 0
        for data in profiles:
            try:
                profile = ViewpointProfile.from_dict(data)
                if self.add_profile(profile, imported_by):
                    count += 1
            except Exception as e:
                logger.error(f"Failed to import profile: {e}")
        return count


# =============================================================================
# Factory Function
# =============================================================================

def create_viewpoint_registry(config: Dict[str, Any] = None) -> ViewpointRegistry:
    """Create and configure a ViewpointRegistry instance."""
    return ViewpointRegistry(config)
