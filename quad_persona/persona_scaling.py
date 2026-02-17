"""
Persona Scaling / Sufficiency Tool

This module implements the Persona Sufficiency Tool that determines whether the base
Quad Persona (4 personas) is sufficient for a query, or whether expansion into larger
pods is needed for complex, high-stakes queries.

The tool computes sufficiency signals (complexity, stakes, conflict, coverage) and
applies threshold-based decision logic to determine expansion requirements.
"""

import logging
from typing import Dict, List, Any

from quad_persona.pod_models import (
    SufficiencySignals,
    ExpansionPlan,
    ScalingDecision,
    SubsystemProfile
)


logger = logging.getLogger(__name__)


# =============================================================================
# Subsystem Detection Profiles
# =============================================================================

# Defense/Aerospace subsystem profiles for F-22 and similar programs
DEFENSE_SUBSYSTEM_PROFILES = {
    "radar": SubsystemProfile(
        subsystem_id="radar_sme",
        name="Radar Systems SME",
        domain="avionics",
        specialization="Active Electronically Scanned Array (AESA) radar systems",
        keywords=["radar", "aesa", "apg", "detection", "tracking", "modes"],
        required_certifications=["Security Clearance", "Radar Systems Certification"],
        related_standards=["MIL-STD-461", "MIL-STD-464"],
        job_role={"title": "Radar Systems Engineer", "level": "Principal"},
        education={"degree": "MS/PhD Electrical Engineering", "focus": "RF Systems"},
        skills={"items": ["Antenna Design", "Signal Processing", "RF Engineering"]}
    ),
    "ew": SubsystemProfile(
        subsystem_id="ew_sme",
        name="Electronic Warfare SME",
        domain="avionics",
        specialization="Electronic attack, protection, and support systems",
        keywords=["electronic warfare", "ew", "jamming", "countermeasures", "rwr", "ecm"],
        required_certifications=["Security Clearance", "EW Systems"],
        related_standards=["MIL-STD-461", "MIL-STD-464"],
        job_role={"title": "EW Systems Engineer", "level": "Senior"},
        education={"degree": "MS Electrical Engineering", "focus": "Electronic Warfare"},
        skills={"items": ["Signal Processing", "Threat Analysis", "Countermeasures Design"]}
    ),
    "avionics": SubsystemProfile(
        subsystem_id="avionics_sme",
        name="Mission Computer / Avionics SME",
        domain="avionics",
        specialization="Integrated avionics and mission computer systems",
        keywords=["avionics", "mission computer", "integrated", "cockpit", "displays"],
        required_certifications=["DO-178C", "Security Clearance"],
        related_standards=["DO-178C", "DO-254", "MIL-STD-1553"],
        job_role={"title": "Avionics Systems Engineer", "level": "Principal"},
        education={"degree": "MS Computer Engineering", "focus": "Embedded Systems"},
        skills={"items": ["Real-time Systems", "Ada/C++", "Avionics Integration"]}
    ),
    "datalink": SubsystemProfile(
        subsystem_id="datalink_sme",
        name="Datalink / Communications SME",
        domain="communications",
        specialization="Tactical datalinks and secure communications",
        keywords=["datalink", "link 16", "communications", "satcom", "secure"],
        required_certifications=["Security Clearance", "COMSEC"],
        related_standards=["MIL-STD-6016", "STANAG 5516"],
        job_role={"title": "Communications Systems Engineer", "level": "Senior"},
        education={"degree": "MS Electrical Engineering", "focus": "Communications"},
        skills={"items": ["Waveform Design", "Network Protocols", "Cryptography"]}
    ),
    "propulsion": SubsystemProfile(
        subsystem_id="propulsion_sme",
        name="Propulsion SME",
        domain="propulsion",
        specialization="Turbofan engines and propulsion systems",
        keywords=["propulsion", "engine", "turbofan", "thrust", "afterburner"],
        required_certifications=["FAA/DoD Propulsion"],
        related_standards=["MIL-E-5007", "MIL-STD-1783"],
        job_role={"title": "Propulsion Engineer", "level": "Senior"},
        education={"degree": "MS Aerospace Engineering", "focus": "Propulsion"},
        skills={"items": ["Thermodynamics", "Turbomachinery", "Performance Analysis"]}
    ),
    "structures": SubsystemProfile(
        subsystem_id="structures_sme",
        name="Airframe Structures SME",
        domain="structures",
        specialization="Aircraft structural design and analysis",
        keywords=["structure", "airframe", "composite", "fatigue", "stress"],
        required_certifications=["Structural Analysis Certification"],
        related_standards=["MIL-STD-1530", "MIL-HDBK-5"],
        job_role={"title": "Structural Engineer", "level": "Senior"},
        education={"degree": "MS Aerospace/Mechanical Engineering"},
        skills={"items": ["FEA", "Composite Materials", "Fatigue Analysis"]}
    ),
    "software": SubsystemProfile(
        subsystem_id="software_sme",
        name="Software / Integration SME",
        domain="software",
        specialization="Mission software and system integration",
        keywords=["software", "integration", "oop", "operational flight program", "ofp"],
        required_certifications=["DO-178C", "CMMI"],
        related_standards=["DO-178C", "MIL-STD-498"],
        job_role={"title": "Software Systems Engineer", "level": "Principal"},
        education={"degree": "MS Computer Science/Software Engineering"},
        skills={"items": ["Ada", "Real-time Systems", "Integration Testing"]}
    ),
    "test": SubsystemProfile(
        subsystem_id="test_sme",
        name="Test & Evaluation SME",
        domain="test",
        specialization="Developmental and operational test and evaluation",
        keywords=["test", "evaluation", "dte", "ote", "flight test", "verification"],
        required_certifications=["Test Pilot School", "DT&E Certification"],
        related_standards=["MIL-STD-810", "MIL-STD-461"],
        job_role={"title": "Test Engineer", "level": "Senior"},
        education={"degree": "MS Engineering", "focus": "Flight Test"},
        skills={"items": ["Test Planning", "Data Analysis", "Requirements Verification"]}
    )
}

# Sector-specific profiles
SECTOR_SUBSYSTEM_PROFILES = {
    "program": SubsystemProfile(
        subsystem_id="program_sme",
        name="Program Execution (Cost/Schedule)",
        domain="program_management",
        specialization="Defense acquisition and program management",
        keywords=["program", "cost", "schedule", "milestone", "acquisition", "budget"],
        required_certifications=["PMP", "DAU Level III"],
        related_standards=["FAR", "DFARS", "DoD 5000"],
        job_role={"title": "Program Manager", "level": "Director"},
        education={"degree": "MBA/MS Program Management"},
        skills={"items": ["Earned Value", "Schedule Management", "Risk Management"]}
    ),
    "sustainment": SubsystemProfile(
        subsystem_id="sustainment_sme",
        name="Sustainment / Depot / Readiness",
        domain="sustainment",
        specialization="Weapon system sustainment and readiness",
        keywords=["sustainment", "readiness", "depot", "maintenance", "logistics"],
        required_certifications=["DAWIA Logistics"],
        related_standards=["MIL-STD-1388", "GEIA-STD-0007"],
        job_role={"title": "Sustainment Manager", "level": "Senior"},
        education={"degree": "MS Logistics/Engineering"},
        skills={"items": ["Reliability Engineering", "Supply Chain", "Depot Operations"]}
    ),
    "manufacturing": SubsystemProfile(
        subsystem_id="manufacturing_sme",
        name="Manufacturing / Supply Chain",
        domain="manufacturing",
        specialization="Aerospace manufacturing and supply chain",
        keywords=["manufacturing", "supply chain", "production", "supplier", "fabrication"],
        required_certifications=["AS9100", "Lean Six Sigma"],
        related_standards=["AS9100", "NADCAP"],
        job_role={"title": "Manufacturing Engineer", "level": "Senior"},
        education={"degree": "MS Manufacturing/Industrial Engineering"},
        skills={"items": ["Lean Manufacturing", "Quality Control", "Supply Chain Management"]}
    ),
    "operations": SubsystemProfile(
        subsystem_id="operations_sme",
        name="Operational User (Tactics)",
        domain="operations",
        specialization="Operational employment and tactics",
        keywords=["operational", "tactics", "employment", "mission", "combat"],
        required_certifications=["Weapons School", "Operational Experience"],
        related_standards=["JCIDS", "CONOPS"],
        job_role={"title": "Operational Requirements Officer", "level": "Lt Col/Colonel"},
        education={"degree": "Advanced Studies", "focus": "Military Operations"},
        skills={"items": ["Tactics Development", "Mission Planning", "Requirements Analysis"]}
    ),
    "cyber": SubsystemProfile(
        subsystem_id="cyber_sme",
        name="Cyber Operations / Mission Assurance",
        domain="cybersecurity",
        specialization="Weapon system cybersecurity and mission assurance",
        keywords=["cyber", "mission assurance", "security", "network", "protection"],
        required_certifications=["CISSP", "CAP", "RMF"],
        related_standards=["NIST 800-53", "RMF"],
        job_role={"title": "Cybersecurity Engineer", "level": "Senior"},
        education={"degree": "MS Cybersecurity/Computer Science"},
        skills={"items": ["Vulnerability Assessment", "RMF", "Secure Development"]}
    ),
    "systems_engineering": SubsystemProfile(
        subsystem_id="systems_eng_sme",
        name="Systems Engineering / Integration Lead",
        domain="systems_engineering",
        specialization="Weapon system integration and SE processes",
        keywords=["systems engineering", "integration", "interface", "architecture", "requirements"],
        required_certifications=["INCOSE CSEP"],
        related_standards=["ISO 15288", "MIL-STD-881"],
        job_role={"title": "Chief Systems Engineer", "level": "Principal"},
        education={"degree": "MS Systems Engineering"},
        skills={"items": ["MBSE", "Requirements Management", "Technical Integration"]}
    )
}

# Regulatory/Compliance profiles
REGULATORY_PROFILES = {
    "airworthiness": SubsystemProfile(
        subsystem_id="airworthiness_sme",
        name="Airworthiness / Safety Authority",
        domain="regulatory",
        specialization="Flight safety and airworthiness certification",
        keywords=["airworthiness", "safety", "certification", "mea", "flight"],
        required_certifications=["ASP", "Flight Safety"],
        related_standards=["MIL-HDBK-516", "SAE ARP4754"],
        job_role={"title": "Airworthiness Engineer", "level": "Senior"},
        education={"degree": "MS Aerospace Engineering"},
        skills={"items": ["Safety Analysis", "Certification", "Hazard Assessment"]}
    ),
    "export": SubsystemProfile(
        subsystem_id="export_sme",
        name="Export Controls / ITAR",
        domain="regulatory",
        specialization="Export control regulations and compliance",
        keywords=["export", "itar", "ear", "technology control", "foreign"],
        required_certifications=["Export Compliance Certification"],
        related_standards=["ITAR", "EAR"],
        job_role={"title": "Export Control Officer", "level": "Manager"},
        education={"degree": "JD/MS International Trade"},
        skills={"items": ["Export Classification", "License Applications", "TCP"]}
    ),
    "contracting": SubsystemProfile(
        subsystem_id="contracting_sme",
        name="Contracting / FAR-DFARS",
        domain="regulatory",
        specialization="Federal acquisition regulations",
        keywords=["contract", "far", "dfars", "acquisition", "proposal"],
        required_certifications=["DAU Contracting Level III"],
        related_standards=["FAR", "DFARS"],
        job_role={"title": "Contracting Officer", "level": "Senior"},
        education={"degree": "MBA/JD"},
        skills={"items": ["Contract Negotiation", "FAR/DFARS", "Cost Analysis"]}
    )
}

COMPLIANCE_PROFILES = {
    "rmf": SubsystemProfile(
        subsystem_id="rmf_sme",
        name="Security Compliance (RMF/ATO)",
        domain="compliance",
        specialization="Risk Management Framework and authorization",
        keywords=["rmf", "ato", "authorization", "accreditation", "security"],
        required_certifications=["CISM", "CAP"],
        related_standards=["NIST 800-37", "NIST 800-53"],
        job_role={"title": "ISSO/ISSM", "level": "Senior"},
        education={"degree": "MS Cybersecurity"},
        skills={"items": ["RMF Process", "Security Controls", "POA&M Management"]}
    ),
    "quality": SubsystemProfile(
        subsystem_id="quality_sme",
        name="Quality Compliance (AS9100)",
        domain="compliance",
        specialization="Aerospace quality management systems",
        keywords=["quality", "as9100", "iso", "audit", "nonconformance"],
        required_certifications=["CQA", "Lead Auditor"],
        related_standards=["AS9100", "AS9102"],
        job_role={"title": "Quality Manager", "level": "Senior"},
        education={"degree": "MS Quality Engineering"},
        skills={"items": ["Quality Systems", "Root Cause Analysis", "Audit"]}
    ),
    "config": SubsystemProfile(
        subsystem_id="config_sme",
        name="Configuration Management / Data Gov",
        domain="compliance",
        specialization="Configuration and data management",
        keywords=["configuration", "config", "baseline", "change", "data"],
        required_certifications=["CM Certification"],
        related_standards=["MIL-STD-973", "EIA-649"],
        job_role={"title": "Configuration Manager", "level": "Senior"},
        education={"degree": "MS Engineering/IT"},
        skills={"items": ["Baseline Management", "Change Control", "Data Rights"]}
    )
}


# =============================================================================
# High-Assurance Detection
# =============================================================================

class HighAssuranceDetector:
    """
    Detects if a query requires high-assurance mode based on domain signals.
    
    High-assurance domains include:
    - Defense/military systems
    - Safety-critical systems (aviation, medical devices)
    - Export-controlled technology
    - Financial/regulatory compliance
    """
    
    # Keywords indicating high-assurance domains
    DEFENSE_KEYWORDS = {
        "weapon", "military", "defense", "dod", "classified", "secret",
        "combat", "warfighter", "tactical", "fighter", "bomber", "missile",
        "f-22", "f-35", "b-21", "c-17", "aegis", "patriot", "thaad",
        "army", "navy", "air force", "marines", "space force"
    }
    
    SAFETY_CRITICAL_KEYWORDS = {
        "safety", "safety-critical", "flight safety", "airworthiness",
        "do-178", "do-254", "arp4754", "hazard", "catastrophic",
        "medical device", "fda", "life-critical", "patient safety"
    }
    
    EXPORT_CONTROL_KEYWORDS = {
        "itar", "ear", "export control", "export license", "foreign national",
        "technology control", "classified", "cui", "fouo", "noforn"
    }
    
    PROGRAM_KEYWORDS = {
        "modernization", "upgrade", "fielding", "program", "acquisition",
        "milestone", "production", "deployment", "sustainment"
    }
    
    @classmethod
    def detect(cls, query: str, context: Dict[str, Any] = None) -> Dict[str, bool]:
        """
        Detect high-assurance signals in query and context.
        
        Returns:
            dict: Detection results for each category
        """
        query_lower = query.lower()
        context = context or {}
        
        # Check each category
        is_defense = any(kw in query_lower for kw in cls.DEFENSE_KEYWORDS)
        is_safety_critical = any(kw in query_lower for kw in cls.SAFETY_CRITICAL_KEYWORDS)
        has_export_control = any(kw in query_lower for kw in cls.EXPORT_CONTROL_KEYWORDS)
        is_major_program = any(kw in query_lower for kw in cls.PROGRAM_KEYWORDS)
        
        # Check context for additional signals
        domain = context.get("domain", "").lower()
        sector = context.get("sector", "").lower()
        
        if domain in ("defense", "military", "aerospace"):
            is_defense = True
        if sector in ("government", "defense", "aerospace"):
            is_defense = True
            
        is_high_assurance = is_defense or is_safety_critical or has_export_control
        
        return {
            "is_high_assurance": is_high_assurance,
            "is_defense_domain": is_defense,
            "has_safety_critical": is_safety_critical,
            "has_export_control": has_export_control,
            "is_major_program": is_major_program
        }


# =============================================================================
# Subsystem Detection
# =============================================================================

class SubsystemDetector:
    """
    Detects subsystems mentioned in a query for persona specialization.
    """
    
    @classmethod
    def detect_subsystems(cls, query: str, context: Dict[str, Any] = None) -> Dict[str, List[SubsystemProfile]]:
        """
        Detect subsystems in query and return matching profiles.
        
        Returns:
            dict: Detected profiles organized by pod type
        """
        query_lower = query.lower()
        
        detected = {
            "knowledge": [],
            "sector": [],
            "regulatory": [],
            "compliance": []
        }
        
        # Check defense/knowledge subsystems
        for key, profile in DEFENSE_SUBSYSTEM_PROFILES.items():
            if any(kw in query_lower for kw in profile.keywords):
                detected["knowledge"].append(profile)
        
        # Check sector subsystems
        for key, profile in SECTOR_SUBSYSTEM_PROFILES.items():
            if any(kw in query_lower for kw in profile.keywords):
                detected["sector"].append(profile)
        
        # Check regulatory profiles
        for key, profile in REGULATORY_PROFILES.items():
            if any(kw in query_lower for kw in profile.keywords):
                detected["regulatory"].append(profile)
        
        # Check compliance profiles
        for key, profile in COMPLIANCE_PROFILES.items():
            if any(kw in query_lower for kw in profile.keywords):
                detected["compliance"].append(profile)
        
        return detected


# =============================================================================
# Persona Sufficiency Tool
# =============================================================================

class PersonaSufficiencyTool:
    """
    Determines if the base Quad Persona is sufficient or if expansion is needed.
    
    Decision is based on four signals:
    1. Complexity Score (0-100): Cross-domain breadth, reasoning depth required
    2. Stakes Score (0-100): Domain criticality, high-assurance requirements
    3. Conflict Score (0-1): Disagreement level between base personas
    4. Coverage Score (0-1): How well base personas answered their lens
    
    If any signal exceeds its threshold, expansion is recommended.
    """
    
    # Threshold configurations
    THRESHOLDS = {
        "standard": {
            "complexity": 60,
            "stakes": 40,
            "conflict": 0.2,
            "coverage": 0.85
        },
        "high_assurance": {
            "complexity": 40,
            "stakes": 30,
            "conflict": 0.1,
            "coverage": 0.95
        }
    }
    
    # Pod spawn caps
    POD_CAPS = {
        "knowledge_max": 6,
        "sector_max": 6,
        "regulatory_max": 3,
        "compliance_max": 3
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the sufficiency tool."""
        self.config = config or {}
        
        # Allow configuration override of thresholds
        if "thresholds" in self.config:
            self.THRESHOLDS.update(self.config["thresholds"])
        
        if "pod_caps" in self.config:
            self.POD_CAPS.update(self.config["pod_caps"])
        
        logger.info("PersonaSufficiencyTool initialized")
    
    def evaluate(
        self,
        query: str,
        context: Dict[str, Any],
        axis_vector: Dict[int, Any],
        persona_results: Dict[str, Dict[str, Any]]
    ) -> ScalingDecision:
        """
        Evaluate if the base quad personas are sufficient.
        
        Args:
            query: Original query text
            context: Query context from layers 1-2
            axis_vector: 17-axis coordinate vector
            persona_results: Results from base quad persona processing
            
        Returns:
            ScalingDecision with mode and expansion plan
        """
        logger.info(f"Evaluating persona sufficiency for query: {query[:50]}...")
        
        # Step 1: Detect high-assurance signals
        ha_signals = HighAssuranceDetector.detect(query, context)
        
        # Step 2: Detect subsystems
        detected_subsystems = SubsystemDetector.detect_subsystems(query, context)
        
        # Step 3: Compute sufficiency signals
        signals = self._compute_signals(
            query, context, axis_vector, persona_results, 
            ha_signals, detected_subsystems
        )
        
        # Step 4: Select threshold mode
        threshold_mode = "high_assurance" if signals.is_high_assurance else "standard"
        thresholds = self.THRESHOLDS[threshold_mode]
        
        # Step 5: Make decision
        should_expand = signals.exceeds_thresholds(thresholds)
        
        if not should_expand:
            logger.info("Quad-only mode: All signals within thresholds")
            return ScalingDecision(
                mode="quad_only",
                signals=signals,
                expansion_plan=None,
                threshold_mode=threshold_mode,
                thresholds_used=thresholds
            )
        
        # Step 6: Calculate expansion plan
        expansion_plan = self._calculate_expansion_plan(
            signals, detected_subsystems, thresholds
        )
        
        logger.info(f"Expanded committee mode: Spawning {expansion_plan.total_personas} additional personas")
        
        return ScalingDecision(
            mode="expanded_committee",
            signals=signals,
            expansion_plan=expansion_plan,
            threshold_mode=threshold_mode,
            thresholds_used=thresholds
        )
    
    def _compute_signals(
        self,
        query: str,
        context: Dict[str, Any],
        axis_vector: Dict[int, Any],
        persona_results: Dict[str, Dict[str, Any]],
        ha_signals: Dict[str, bool],
        detected_subsystems: Dict[str, List[SubsystemProfile]]
    ) -> SufficiencySignals:
        """Compute all sufficiency signals."""
        
        signals = SufficiencySignals()
        
        # Transfer high-assurance flags
        signals.is_high_assurance = ha_signals.get("is_high_assurance", False)
        signals.is_defense_domain = ha_signals.get("is_defense_domain", False)
        signals.has_safety_critical = ha_signals.get("has_safety_critical", False)
        signals.has_export_control = ha_signals.get("has_export_control", False)
        
        # Count detected items
        signals.subsystems_detected = sum(len(v) for v in detected_subsystems.values())
        
        # Compute complexity score
        signals.complexity_score = self._compute_complexity_score(
            query, context, axis_vector, detected_subsystems
        )
        
        # Compute stakes score
        signals.stakes_score = self._compute_stakes_score(
            query, context, ha_signals
        )
        
        # Compute conflict score from persona results
        signals.conflict_score = self._compute_conflict_score(persona_results)
        
        # Compute coverage score from persona results
        signals.coverage_score = self._compute_coverage_score(persona_results)
        
        # Count activated axes
        signals.pillars_activated = len([
            v for k, v in axis_vector.items() 
            if k == 1 and v
        ])
        signals.sectors_activated = len([
            v for k, v in axis_vector.items()
            if k == 2 and v
        ])
        
        return signals
    
    def _compute_complexity_score(
        self,
        query: str,
        context: Dict[str, Any],
        axis_vector: Dict[int, Any],
        detected_subsystems: Dict[str, List[SubsystemProfile]]
    ) -> float:
        """
        Compute complexity score (0-100).
        
        Factors:
        - Number of subsystems detected
        - Number of activated axes
        - Query length and structure
        - Cross-domain indicators
        """
        score = 0.0
        
        # Subsystem count contribution (max 40 points)
        subsystem_count = sum(len(v) for v in detected_subsystems.values())
        score += min(40, subsystem_count * 8)
        
        # Activated axes contribution (max 20 points)
        active_axes = sum(1 for v in axis_vector.values() if v)
        score += min(20, active_axes * 2)
        
        # Query complexity (max 20 points)
        words = query.split()
        if len(words) > 30:
            score += 10
        if len(words) > 50:
            score += 10
        
        # Cross-domain indicators (max 20 points)
        cross_domain_keywords = ["and", "plus", "with", "including", "combined"]
        cross_count = sum(1 for kw in cross_domain_keywords if kw in query.lower())
        score += min(20, cross_count * 5)
        
        return min(100, score)
    
    def _compute_stakes_score(
        self,
        query: str,
        context: Dict[str, Any],
        ha_signals: Dict[str, bool]
    ) -> float:
        """
        Compute stakes score (0-100).
        
        Factors:
        - High-assurance domain detection
        - Safety-critical indicators
        - Export control implications
        - Program size indicators
        """
        score = 0.0
        
        # High-assurance domain (25 points)
        if ha_signals.get("is_high_assurance"):
            score += 25
        
        # Defense domain (25 points)
        if ha_signals.get("is_defense_domain"):
            score += 25
        
        # Safety-critical (25 points)
        if ha_signals.get("has_safety_critical"):
            score += 25
        
        # Export control (15 points)
        if ha_signals.get("has_export_control"):
            score += 15
        
        # Major program (10 points)
        if ha_signals.get("is_major_program"):
            score += 10
        
        return min(100, score)
    
    def _compute_conflict_score(
        self,
        persona_results: Dict[str, Dict[str, Any]]
    ) -> float:
        """
        Compute conflict score (0-1) from persona results.
        
        Measures disagreement between persona responses.
        """
        if not persona_results:
            return 0.0
        
        # Check for explicit conflict markers
        conflicts = 0
        total_pairs = 0
        
        persona_types = list(persona_results.keys())
        
        for i, pt1 in enumerate(persona_types):
            for pt2 in persona_types[i+1:]:
                total_pairs += 1
                
                r1 = persona_results.get(pt1, {})
                r2 = persona_results.get(pt2, {})
                
                # Check confidence variance
                c1 = r1.get("confidence", 0.5)
                c2 = r2.get("confidence", 0.5)
                
                if abs(c1 - c2) > 0.3:
                    conflicts += 0.5
                
                # Check for explicit disagreement flags
                if r1.get("disagrees_with") or r2.get("disagrees_with"):
                    conflicts += 0.5
        
        if total_pairs == 0:
            return 0.0
        
        return min(1.0, conflicts / total_pairs)
    
    def _compute_coverage_score(
        self,
        persona_results: Dict[str, Dict[str, Any]]
    ) -> float:
        """
        Compute coverage score (0-1) from persona results.
        
        Measures how well each persona could answer its lens.
        """
        if not persona_results:
            return 0.5
        
        coverages = []
        
        for persona_type, result in persona_results.items():
            # Use confidence as proxy for coverage
            confidence = result.get("confidence", 0.5)
            
            # Penalize if persona flagged gaps
            if result.get("has_gaps"):
                confidence *= 0.8
            if result.get("needs_more_info"):
                confidence *= 0.9
            
            coverages.append(confidence)
        
        return sum(coverages) / len(coverages) if coverages else 0.5
    
    def _calculate_expansion_plan(
        self,
        signals: SufficiencySignals,
        detected_subsystems: Dict[str, List[SubsystemProfile]],
        thresholds: Dict[str, float]
    ) -> ExpansionPlan:
        """
        Calculate how many personas to spawn in each pod.
        """
        plan = ExpansionPlan()
        plan.reasons = signals.get_expansion_reasons(thresholds)
        
        # Base spawn counts on detected subsystems
        plan.spawn_counts["knowledge"] = min(
            len(detected_subsystems.get("knowledge", [])),
            self.POD_CAPS["knowledge_max"]
        )
        plan.spawn_counts["sector"] = min(
            len(detected_subsystems.get("sector", [])),
            self.POD_CAPS["sector_max"]
        )
        plan.spawn_counts["regulatory"] = min(
            len(detected_subsystems.get("regulatory", [])),
            self.POD_CAPS["regulatory_max"]
        )
        plan.spawn_counts["compliance"] = min(
            len(detected_subsystems.get("compliance", [])),
            self.POD_CAPS["compliance_max"]
        )
        
        # Ensure minimum spawns for high complexity
        if signals.complexity_score > 70:
            plan.spawn_counts["knowledge"] = max(plan.spawn_counts["knowledge"], 3)
            plan.spawn_counts["sector"] = max(plan.spawn_counts["sector"], 2)
        
        # Ensure minimum spawns for high stakes
        if signals.stakes_score > 60:
            plan.spawn_counts["regulatory"] = max(plan.spawn_counts["regulatory"], 2)
            plan.spawn_counts["compliance"] = max(plan.spawn_counts["compliance"], 2)
        
        # Store subsystems to spawn
        plan.subsystems_to_spawn = {
            pod: [p.subsystem_id for p in profiles]
            for pod, profiles in detected_subsystems.items()
        }
        
        return plan


# =============================================================================
# Factory Function
# =============================================================================

def create_sufficiency_tool(config: Dict[str, Any] = None) -> PersonaSufficiencyTool:
    """Create and configure a PersonaSufficiencyTool instance."""
    return PersonaSufficiencyTool(config)
