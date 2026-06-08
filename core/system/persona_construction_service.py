"""
Persona Construction Service (Axes 8-11)

This module provides the logic for dynamically generating persona profiles
based on the 17-axis coordinate system. It resolves specific expertise 
requirements into functional personas with canonical UKGIDs.
"""

import logging
import uuid
import json
import hashlib
import os
from typing import Dict, Any, Optional
from core.persona.quad.models import PersonaProfile

class PersonaConstructionService:
    """
    Persona Construction Service
    
    Responsibilities:
    1. Resolve Axes 8-11 into concrete expert profiles.
    2. Dynamically seed persona components (skills, training, etc.) from registries.
    3. Management of canonical UKGIDs for persona instances via UIDS.
    4. Integration with Axis 1 (Pillar) and Axis 2 (Sector) for deep role context.
    """
    
    def __init__(self, uids=None, uns=None, mapping=None, rag_service_getter=None):
        self.logger = logging.getLogger(__name__)
        self.uids = uids
        self.uns = uns
        self.mapping = mapping
        self._persona_cache: Dict[str, PersonaProfile] = {}
        # Optional RAG service accessor — injected for testability, lazy-fallback otherwise.
        self._rag_service_getter = rag_service_getter
        
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

        cache_key = self._cache_key(axis_number, coordinate_path, context)
        cached = self._persona_cache.get(cache_key)
        if cached:
            return cached

        cached = self._load_cached_persona(cache_key)
        if cached:
            self._persona_cache[cache_key] = cached
            return cached

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
        
        # 5. Seed components based on sourced meta-data or DSQP dynamic construction.
        if not self._seed_components_with_dsqp(profile, axis_number, coordinate_path, source_context, context):
            self._seed_components(profile, axis_number, source_context, context)
        profile.metadata["cache_key"] = cache_key
        self._persona_cache[cache_key] = profile
        self._store_cached_persona(cache_key, profile, axis_number, coordinate_path)
        
        self.logger.info(f"Constructed dynamic persona: {label} ({profile.persona_id}) sourced from Axis {source_axis}")
        return profile

    @staticmethod
    def _cache_key(axis_number: int, coordinate_path: str, context: Optional[Dict[str, Any]]) -> str:
        payload = {
            "axis_number": axis_number,
            "coordinate_path": coordinate_path,
            "context": context or {},
        }
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:24]
        return f"persona:{axis_number}:{digest}"

    # Collection name constant — avoids importing RAGService just for this value.
    _COLLECTION_PERSONA_PROFILES = "persona_profiles"

    def _load_cached_persona(self, cache_key: str) -> Optional[PersonaProfile]:
        try:
            if self._rag_service_getter is not None:
                get_rag_service = self._rag_service_getter
            else:
                from backend.services.rag_service import get_rag_service  # inversion:ok — injected or lazy optional RAG cache

            results = get_rag_service().search_collection(
                self._COLLECTION_PERSONA_PROFILES,
                cache_key,
                k=1,
                filters={"cache_key": cache_key},
            )
            if not results:
                return None
            payload = json.loads(results[0].get("text") or "{}")
            return PersonaProfile.from_dict(payload)
        except Exception as exc:
            self.logger.debug("Persona profile cache read skipped: %s", exc)
            return None

    def _store_cached_persona(
        self,
        cache_key: str,
        profile: PersonaProfile,
        axis_number: int,
        coordinate_path: str,
    ) -> None:
        try:
            if self._rag_service_getter is not None:
                get_rag_service = self._rag_service_getter
            else:
                from backend.services.rag_service import get_rag_service  # inversion:ok — injected or lazy optional RAG cache

            get_rag_service().ingest_text(
                self._COLLECTION_PERSONA_PROFILES,
                cache_key,
                json.dumps(profile.to_dict(), sort_keys=True, default=str),
                {
                    "cache_key": cache_key,
                    "axis_number": axis_number,
                    "coordinate_path": coordinate_path,
                    "persona_type": profile.persona_type,
                },
            )
        except Exception as exc:
            self.logger.debug("Persona profile cache write skipped: %s", exc)

    def _seed_components_with_dsqp(
        self,
        profile: PersonaProfile,
        axis: int,
        coordinate_path: str,
        source_context: Dict[str, Any],
        request_context: Dict[str, Any],
    ) -> bool:
        """Try DSQP dynamic persona construction, returning False for static fallback."""
        dsqp_requested = request_context.get("dsqp_mode")
        if dsqp_requested is None:
            dsqp_requested = os.environ.get("DSQP_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
        if not dsqp_requested:
            return False

        try:
            from backend.dsqp import DSQPChain, DSQPValidator  # inversion:ok — lazy optional DSQP chain

            query = str(
                request_context.get("query")
                or request_context.get("user_query")
                or request_context.get("input_message")
                or source_context.get("description")
                or coordinate_path
            )
            axis_vector = request_context.get("coordinate_vector") or request_context.get("axis_vector") or {}
            dsqp_context = {
                **request_context,
                "coordinate_path": coordinate_path,
                "source_context": source_context,
            }
            expanded = DSQPChain().construct(
                query,
                axis_vector,
                axis_number=axis,
                coordinate_path=coordinate_path,
                context=dsqp_context,
            )
            validation = DSQPValidator().validate(expanded)
            if not validation["valid"]:
                profile.metadata["dsqp_validation"] = validation
                return False
            payload = expanded.to_dict()
            for component_key, component_data in payload["components"].items():
                profile.set_component(component_key, component_data)
            profile.name = payload["name"]
            profile.description = payload["description"]
            profile.metadata.update({
                "dsqp_enabled": True,
                "dsqp_chain": payload["dsqp_chain"],
                "dsqp_coverage_score": validation["coverage_score"],
                "dsqp_persona_id": payload["persona_id"],
                "construction_mode": "dsqp",
            })
            if axis == 10:
                profile.octopus_connections = source_context.get("links", ["Federal Regulatory Hub"])
            elif axis == 11:
                profile.spiderweb_connections = source_context.get("crosswalks", ["Standard Harmonization Layer"])
            return True
        except Exception as exc:
            self.logger.debug("DSQP persona construction skipped: %s", exc)
            return False

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
