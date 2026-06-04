"""Phase 4b import-compatibility tests for quad persona package splits."""


def test_mathematical_framework_compat_exports():
    """The former mathematical_framework.py import path must still export public names."""
    from core.persona.quad.mathematical_framework import (
        DeepRecursiveLearning,
        DynamicWeightFunctions,
        IntegrationFunction,
        KnowledgePoint,
        KnowledgeSpaceMapper,
        MemoryEdge,
        MemoryVertex,
        QuadPersonaMathematicalSystem,
        RefinementWorkflow12Step,
        StructuredMemoryGraph,
    )

    assert KnowledgePoint is not None
    assert MemoryVertex is not None
    assert MemoryEdge is not None
    assert DynamicWeightFunctions is not None
    assert KnowledgeSpaceMapper is not None
    assert StructuredMemoryGraph is not None
    assert DeepRecursiveLearning is not None
    assert IntegrationFunction is not None
    assert RefinementWorkflow12Step is not None
    assert QuadPersonaMathematicalSystem is not None


def test_persona_scaling_compat_exports():
    """The former persona_scaling.py import path must still export public names."""
    from core.persona.quad.persona_scaling import (
        COMPLIANCE_PROFILES,
        DEFENSE_SUBSYSTEM_PROFILES,
        REGULATORY_PROFILES,
        SECTOR_SUBSYSTEM_PROFILES,
        HighAssuranceDetector,
        PersonaSufficiencyTool,
        SubsystemDetector,
        create_sufficiency_tool,
    )

    assert DEFENSE_SUBSYSTEM_PROFILES
    assert SECTOR_SUBSYSTEM_PROFILES
    assert REGULATORY_PROFILES
    assert COMPLIANCE_PROFILES
    assert HighAssuranceDetector is not None
    assert SubsystemDetector is not None
    assert PersonaSufficiencyTool is not None
    assert create_sufficiency_tool is not None


def test_pod_orchestrator_compat_exports():
    """The former pod_orchestrator.py import path must still export public names."""
    from core.persona.quad.pod_orchestrator import (
        CrossPodDeconfliction,
        PersonaBuilder,
        PodOrchestrator,
        PodSynthesizer,
        create_pod_orchestrator,
    )

    assert PersonaBuilder is not None
    assert PodSynthesizer is not None
    assert CrossPodDeconfliction is not None
    assert PodOrchestrator is not None
    assert create_pod_orchestrator is not None


def test_phase4b_factories_still_construct():
    """Factory and system constructors remain available through compatibility exports."""
    from core.persona.quad.mathematical_framework import QuadPersonaMathematicalSystem
    from core.persona.quad.persona_scaling import create_sufficiency_tool
    from core.persona.quad.pod_orchestrator import create_pod_orchestrator

    assert create_sufficiency_tool() is not None
    assert create_pod_orchestrator() is not None
    assert QuadPersonaMathematicalSystem() is not None
