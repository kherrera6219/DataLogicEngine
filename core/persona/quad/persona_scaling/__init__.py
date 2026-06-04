"""Compatibility exports for persona scaling.

This package replaces the former ``persona_scaling.py`` module while preserving
imports such as::

    from core.persona.quad.persona_scaling import PersonaSufficiencyTool
"""

from core.persona.quad.persona_scaling.profiles import (
    COMPLIANCE_PROFILES,
    DEFENSE_SUBSYSTEM_PROFILES,
    REGULATORY_PROFILES,
    SECTOR_SUBSYSTEM_PROFILES,
)
from core.persona.quad.persona_scaling.sufficiency import (
    HighAssuranceDetector,
    PersonaSufficiencyTool,
    SubsystemDetector,
    create_sufficiency_tool,
)

__all__ = [
    "DEFENSE_SUBSYSTEM_PROFILES",
    "SECTOR_SUBSYSTEM_PROFILES",
    "REGULATORY_PROFILES",
    "COMPLIANCE_PROFILES",
    "HighAssuranceDetector",
    "SubsystemDetector",
    "PersonaSufficiencyTool",
    "create_sufficiency_tool",
]
