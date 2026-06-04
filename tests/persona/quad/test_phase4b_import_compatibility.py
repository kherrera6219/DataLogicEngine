"""Phase 4b import-compatibility tests for quad persona package splits."""

import importlib


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


def test_phase4b_direct_submodule_locations_importable():
    """New package-internal module locations should be importable directly."""
    module_names = [
        "core.persona.quad.mathematical_framework.weights",
        "core.persona.quad.mathematical_framework.memory_graph",
        "core.persona.quad.mathematical_framework.refinement",
        "core.persona.quad.mathematical_framework.integration",
        "core.persona.quad.persona_scaling.profiles",
        "core.persona.quad.persona_scaling.sufficiency",
        "core.persona.quad.pod_orchestrator.builder",
        "core.persona.quad.pod_orchestrator.synthesis",
        "core.persona.quad.pod_orchestrator.orchestrator",
    ]

    for module_name in module_names:
        module = importlib.import_module(module_name)
        assert module.__name__ == module_name


def test_phase4b_public_exports_point_to_new_locations():
    """Compatibility exports should resolve to classes in the new submodules."""
    from core.persona.quad.mathematical_framework import (
        DynamicWeightFunctions,
        QuadPersonaMathematicalSystem,
        StructuredMemoryGraph,
    )
    from core.persona.quad.persona_scaling import PersonaSufficiencyTool
    from core.persona.quad.pod_orchestrator import PersonaBuilder, PodOrchestrator

    assert DynamicWeightFunctions.__module__ == "core.persona.quad.mathematical_framework.weights"
    assert StructuredMemoryGraph.__module__ == "core.persona.quad.mathematical_framework.memory_graph"
    assert QuadPersonaMathematicalSystem.__module__ == "core.persona.quad.mathematical_framework.integration"
    assert PersonaSufficiencyTool.__module__ == "core.persona.quad.persona_scaling.sufficiency"
    assert PersonaBuilder.__module__ == "core.persona.quad.pod_orchestrator.builder"
    assert PodOrchestrator.__module__ == "core.persona.quad.pod_orchestrator.orchestrator"


def test_phase4b_sufficiency_to_orchestrator_wiring():
    """Light runtime wiring from sufficiency decision to pod orchestration still works."""
    from core.persona.quad.persona_scaling import create_sufficiency_tool
    from core.persona.quad.pod_orchestrator import create_pod_orchestrator

    tool = create_sufficiency_tool()
    decision = tool.evaluate(
        query=(
            "Plan an F-22 modernization with new radar modes, electronic warfare "
            "updates, mission computer integration, secure datalink changes, and "
            "airworthiness certification concerns."
        ),
        context={"query_id": "phase4b-smoke", "domain": "defense", "sector": "aerospace"},
        axis_vector={1: "PL16", 2: "336411", 8: True, 9: True, 10: True, 11: True},
        persona_results={
            "knowledge": {"response": "technical", "confidence": 0.65, "has_gaps": True},
            "sector": {"response": "sector", "confidence": 0.70, "has_gaps": True},
            "regulatory": {"response": "regulatory", "confidence": 0.85},
            "compliance": {"response": "compliance", "confidence": 0.80},
        },
    )

    assert decision.should_expand is True

    orchestrator = create_pod_orchestrator({"max_workers": 1})
    state = orchestrator.orchestrate(
        query="Plan an F-22 modernization with radar, EW, datalink, and airworthiness work.",
        context={"query_id": "phase4b-smoke", "domain": "defense", "sector": "aerospace"},
        scaling_decision=decision,
        base_persona_results=None,
    )

    assert state.status == "completed"
    assert state.pods
    assert state.final_synthesis
