"""Expanded persona builder for pod orchestration."""

import logging
import uuid
from typing import Any, Dict, Optional

from core.persona.quad.persona_scaling.profiles import (
    COMPLIANCE_PROFILES,
    DEFENSE_SUBSYSTEM_PROFILES,
    REGULATORY_PROFILES,
    SECTOR_SUBSYSTEM_PROFILES,
)
from core.persona.quad.pod_models import ExpandedPersona, PodType

logger = logging.getLogger(__name__)


class PersonaBuilder:
    """Builds expanded personas based on subsystem profiles."""

    PROFILE_REGISTRIES = {
        PodType.KNOWLEDGE: DEFENSE_SUBSYSTEM_PROFILES,
        PodType.SECTOR: SECTOR_SUBSYSTEM_PROFILES,
        PodType.REGULATORY: REGULATORY_PROFILES,
        PodType.COMPLIANCE: COMPLIANCE_PROFILES,
    }

    @classmethod
    def build_persona(
        cls,
        pod_type: PodType,
        subsystem_id: str,
        context: Dict[str, Any] = None,
    ) -> Optional[ExpandedPersona]:
        """Build an expanded persona for a specific subsystem."""
        registry = cls.PROFILE_REGISTRIES.get(pod_type, {})

        profile = registry.get(subsystem_id)

        if not profile:
            for key, prof in registry.items():
                if prof.subsystem_id == subsystem_id:
                    profile = prof
                    break

        if not profile and subsystem_id.endswith("_sme"):
            base_key = subsystem_id.replace("_sme", "")
            profile = registry.get(base_key)

        if not profile:
            logger.warning(f"Subsystem profile not found: {subsystem_id} for {pod_type.value}")
            return None

        persona = ExpandedPersona(
            persona_id=f"{pod_type.value}_{subsystem_id}_{uuid.uuid4().hex[:8]}",
            pod_type=pod_type,
            name=profile.name,
            description=profile.specialization,
            subsystem_profile=profile,
        )

        persona.set_component("job_role", profile.job_role)
        persona.set_component("education", profile.education)
        persona.set_component("certifications", {
            "items": profile.required_certifications,
            "standards": profile.related_standards,
        })
        persona.set_component("skills", profile.skills)
        persona.set_component("training", {
            "domain": profile.domain,
            "specialization": profile.specialization,
        })
        persona.set_component("career_path", profile.career_path)
        persona.set_component("related_jobs", profile.related_jobs)

        if context:
            persona.metadata["query_context"] = {
                "domain": context.get("domain"),
                "sector": context.get("sector"),
                "location": context.get("location"),
            }

        logger.info(f"Built persona: {persona.name} ({persona.persona_id})")
        return persona

    @classmethod
    def build_default_persona(
        cls,
        pod_type: PodType,
        index: int,
        context: Dict[str, Any] = None,
    ) -> ExpandedPersona:
        """Build a default expanded persona when no specific subsystem is detected."""
        default_names = {
            PodType.KNOWLEDGE: [
                "Domain Expert",
                "Technical SME",
                "Research Analyst",
                "Systems Analyst",
                "Architecture Expert",
                "Integration Specialist",
            ],
            PodType.SECTOR: [
                "Industry Analyst",
                "Operations Expert",
                "Program Analyst",
                "Business Analyst",
                "Strategy Consultant",
                "Implementation Lead",
            ],
            PodType.REGULATORY: [
                "Regulatory Analyst",
                "Policy Expert",
                "Compliance Advisor",
            ],
            PodType.COMPLIANCE: [
                "Compliance Officer",
                "Audit Specialist",
                "Standards Expert",
            ],
        }

        names = default_names.get(pod_type, ["Expert"])
        name = names[index % len(names)]

        persona = ExpandedPersona(
            persona_id=f"{pod_type.value}_default_{index}_{uuid.uuid4().hex[:8]}",
            pod_type=pod_type,
            name=name,
            description=f"Expert in {pod_type.value} domain",
        )

        persona.set_component("job_role", {"title": name, "level": "Senior"})
        persona.set_component("education", {"degree": "Advanced Degree"})
        persona.set_component("skills", {"items": [f"{pod_type.value} expertise"]})

        return persona
