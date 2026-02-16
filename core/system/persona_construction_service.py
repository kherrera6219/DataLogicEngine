"""
Persona Construction Service (Axes 8-11)

This module provides the logic for dynamically generating persona profiles
based on the 17-axis coordinate system. It resolves specific expertise 
requirements into functional personas with canonical UKGIDs.
"""

import logging
import uuid
from typing import Dict, Any, Optional
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
        
        Mapping:
        - Axis 8 (Knowledge) -> Axis 1 (Pillar) context
        - Axis 9 (Sector) -> Axis 2 (Sector) context
        - Axis 10 (Regulatory) -> Axis 6 (Octopus Crosswalk) context
        - Axis 11 (Compliance) -> Axis 7 (Spiderweb Crosswalk) context
        """
        if axis_number not in self.axis_to_type:
            raise ValueError(f"Axis {axis_number} is not a valid persona axis (8-11)")
            
        persona_type = self.axis_to_type[axis_number]
        context = context or {}
        
        # 1. Resolve human-readable labels from UNS
        label = f"{persona_type} Expert"
        source_context = {}
        
        if self.uns:
            full_path = self.uns.format_path(axis_number, coordinate_path.split("."))
            label = self.uns.resolve_label(full_path)
        
        # 2. Map Persona Axis to Data Source Axis for seeding
        source_axis_map = {8: 1, 9: 2, 10: 6, 11: 7}
        source_axis = source_axis_map.get(axis_number)
        
        if self.mapping and source_axis:
            # Query the mapping system for the specific source context
            source_context = self.mapping.get_coordinate_context(source_axis, coordinate_path)
            
        # 3. Register identity in UIDS
        ukgid = None
        if self.uids:
            ukgid = self.uids.register_entity(
                name=label,
                entity_type="persona",
                aliases={"coord": coordinate_path, "source_axis": str(source_axis)},
                metadata={"axis": axis_number, "type": persona_type, "source_context": source_context}
            )
            
        # 4. Create PersonaProfile
        profile = PersonaProfile(
            persona_id=ukgid or f"per_{uuid.uuid4().hex[:8]}",
            axis_number=axis_number,
            persona_type=persona_type,
            name=label,
            description=f"Dynamically generated expert for {label}"
        )
        
        # 5. Seed components based on sourced meta-data
        self._seed_components(profile, axis_number, source_context, context)
        
        self.logger.info(f"Constructed dynamic persona: {label} ({profile.persona_id}) sourced from Axis {source_axis}")
        return profile

    def _seed_components(self, profile: PersonaProfile, axis: int, source_context: Dict[str, Any], request_context: Dict[str, Any]):
        """Seed the 7 core components with context-aware data sourced from primary axes."""
        
        # 1. Job Role (Titles and Role Description from Source)
        title = source_context.get("label") or profile.name
        profile.set_component("job_role", {
            "title": f"Lead {title} Officer",
            "level": request_context.get("experience_level", "Senior Specialist"),
            "focus_area": source_context.get("description", "Domain expertise")
        })
        
        # 2. Education (Axis-specific degrees)
        edu_map = {8: "PhD in Applied Sciences", 9: "MBA in Industry Management", 10: "JD/LLM in Regulatory Law", 11: "Masters in Enterprise Compliance"}
        profile.set_component("education", {
            "degree": edu_map.get(axis, "Advanced Degree"),
            "focus": title
        })
        
        # 3. Certifications (System-grade credentials)
        cert_map = {8: ["UKG-Certified Scholar"], 9: ["Six Sigma Black Belt"], 10: ["Bar Association Member"], 11: ["CAMS Certified"]}
        profile.set_component("certifications", {
            "list": cert_map.get(axis, ["Standard Certification"])
        })
        
        # 4. Skills (Derived from source context)
        source_tags = source_context.get("meta_tags", [])
        profile.set_component("skills", {
            "items": list(set(source_tags + request_context.get("required_skills", ["Analysis", "Verification"]))),
            "domain_focus": source_context.get("pillar_name", "Global")
        })
        
        # 5. Training (Specialize training modules)
        profile.set_component("training", {
            "modules": ["Recursive Learning V5", "Refinement Protocols", f"{title} Advanced Seminar"]
        })
        
        # 6. Career Path (Simulation of professional history)
        profile.set_component("career_path", {
            "stages": ["Junior Analyst", "Subject Matter Expert", f"Lead {title} Officer"],
            "years_in_field": 15
        })
        
        # 7. Related Jobs (Cross-domain career mapping)
        profile.set_component("related_jobs", {
            "overlapping_roles": ["Chief Strategy Officer", "Risk Manager", "Technical Lead"]
        })
        
        # Axis specific specializations
        if axis == 10: # Regulatory (derived from Axis 6 Octopus)
            profile.octopus_connections = source_context.get("links", ["Federal Regulatory Hub"])
        elif axis == 11: # Compliance (derived from Axis 7 Spiderweb)
            profile.spiderweb_connections = source_context.get("crosswalks", ["Standard Harmonization Layer"])
        
    def check_health(self) -> Dict[str, Any]:
        """System health check."""
        return {
            "healthy": True,
            "axis_coverage": list(self.axis_to_type.keys())
        }
