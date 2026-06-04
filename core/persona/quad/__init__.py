"""
Quad Persona library (UKG axes 8-11: knowledge, sector, regulatory, compliance).

Pure, dependency-free domain logic relocated from the former top-level
``quad_persona/`` package into ``core/`` (the domain/kernel layer). Includes the
data models, the persona engine + expert hierarchy, pod scaling/orchestration,
the mathematical framework, the axis-role mapper, and the JSON persona loader.

The old ``quad_persona.*`` import paths remain available via a thin
re-export shim (deprecated) for one release.
"""

from core.persona.quad.models import PersonaProfile, QueryState
from core.persona.quad.quad_engine import (
    QuadPersona,
    KnowledgeExpert,
    SectorExpert,
    RegulatoryExpert,
    ComplianceExpert,
    QuadPersonaEngine,
    create_quad_persona_engine,
)

# Backwards-compatible alias (older callers referenced ``QuadEngine``).
QuadEngine = QuadPersonaEngine

__all__ = [
    "PersonaProfile",
    "QueryState",
    "QuadPersona",
    "KnowledgeExpert",
    "SectorExpert",
    "RegulatoryExpert",
    "ComplianceExpert",
    "QuadPersonaEngine",
    "QuadEngine",
    "create_quad_persona_engine",
]
