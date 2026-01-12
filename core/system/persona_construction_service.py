"""
Persona Construction Service (Axes 8-11)

This module provides the logic for dynamically generating persona profiles
based on the 17-axis coordinate system. It resolves specific expertise 
requirements into functional personas with canonical UKGIDs.
"""

import logging
import uuid
from datetime import datetime, UTC
from typing import Dict, List, Any, Optional
from quad_persona.quad_engine import PersonaProfile

class PersonaConstructionService:
    """
    Persona Construction Service
    
    Responsibilities:
    1. Resolve Axes 8-11 into concrete expert profiles.
    2. Dynamically seed persona components (skills, training, etc.) from registries.
    3. Management of canonical UKGIDs for persona instances via UIDS.
    4. Integration with Axis 1 (Pillar) and Axis 2 (Sector) for deep role context.
    """
    
    def __init__(self, uids=None, uns=None, mapping=None):
        self.logger = logging.getLogger(__name__)
        self.uids = uids
        self.uns = uns
        self.mapping = mapping
        
        # Mapping from Axis Number to Persona Type
        self.axis_to_type = {
            8: "knowledge",
            9: "sector",
            10: "regulatory",
            11: "compliance"
        }

    def construct_persona(self, 
                          axis_number: int, 
                          coordinate_path: str, 
                          context: Optional[Dict[str, Any]] = None) -> PersonaProfile:
        """
        Dynamically construct a persona based on an axis and a coordinate path.
        
        Example: axis_number=10, coordinate_path="6.4.2" (Regulatory)
        """
        if axis_number not in self.axis_to_type:
            raise ValueError(f"Axis {axis_number} is not a valid persona axis (8-11)")
            
        persona_type = self.axis_to_type[axis_number]
        context = context or {}
        
        # 1. Resolve human-readable labels from UNS
        label = f"{persona_type} Expert"
        if self.uns:
            full_path = self.uns.format_path(axis_number, coordinate_path.split("."))
            label = self.uns.resolve_label(full_path)
            
        # 2. Register identity in UIDS
        ukgid = None
        if self.uids:
            ukgid = self.uids.register_entity(
                name=label,
                entity_type="persona",
                aliases={"coord": coordinate_path},
                metadata={"axis": axis_number, "type": persona_type}
            )
            
        # 3. Create PersonaProfile
        profile = PersonaProfile(
            persona_id=ukgid or f"per_{uuid.uuid4().hex[:8]}",
            axis_number=axis_number,
            persona_type=persona_type,
            name=label,
            description=f"Dynamically generated expert for {label}"
        )
        
        # 4. Seed components based on context and axis
        self._seed_components(profile, axis_number, context)
        
        self.logger.info(f"Constructed dynamic persona: {label} ({profile.persona_id})")
        return profile

    def _seed_components(self, profile: PersonaProfile, axis: int, context: Dict[str, Any]):
        """Seed the 7 core components with context-aware data."""
        # Generic seating (to be replaced by registry lookups in later steps)
        profile.set_component("job_role", {
            "title": profile.name,
            "level": context.get("experience_level", "Senior Specialist")
        })
        
        profile.set_component("skills", {
            "items": context.get("required_skills", ["Analysis", "Reporting", "Verification"]),
            "domain_focus": context.get("sector", "General")
        })
        
        # Axis specific specializations
        if axis == 10: # Regulatory
            profile.octopus_connections = context.get("reg_frameworks", ["Federal", "International"])
        elif axis == 11: # Compliance
            profile.spiderweb_connections = context.get("standards", ["ISO", "NIST"])

    def check_health(self) -> Dict[str, Any]:
        """System health check."""
        return {
            "healthy": True,
            "axis_coverage": list(self.axis_to_type.keys())
        }
