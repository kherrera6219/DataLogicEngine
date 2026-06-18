"""
Quad Persona library (UKG axes 8-11: knowledge, sector, regulatory, compliance).

Pure, dependency-free domain logic relocated from the former top-level
``quad_persona/`` package into ``core/`` (the domain/kernel layer).

Live / canonical components:
- ``models`` — ``PersonaProfile`` (7-component) + ``QueryState``;
- ``persona_scaling`` — sufficiency tooling and persona profiles;
- ``pod_models`` + ``pod_orchestrator`` — pod expansion/orchestration;
- ``mathematical_framework`` — the persona math system.

Demo / non-production:
- ``quad_engine`` — heuristic 4-persona engine used only by demo scripts and
  tests. The live query-time 7-component construction is
  ``core/system/persona_construction_service.py`` -> DSQP, not this engine.
- ``persona_loader`` — JSON persona-CRUD utility used only by the
  ``scripts/persona_manager.py`` CLI; no production importer.

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
