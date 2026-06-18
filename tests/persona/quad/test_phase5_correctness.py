"""Phase 5 correctness regressions for quad-persona library behavior."""

from datetime import UTC

import numpy as np

from core.persona.quad.mathematical_framework import (
    MemoryVertex,
    QuadPersonaMathematicalSystem,
    RefinementWorkflow12Step,
    StructuredMemoryGraph,
)
from core.persona.quad.persona_scaling import PersonaSufficiencyTool
from core.persona.quad.pod_models import ExpandedPersona, PodType
from core.persona.quad.pod_orchestrator import PodOrchestrator


def test_memory_vertex_defaults_are_timezone_aware_and_decay_works():
    memory = MemoryVertex(
        vertex_id="memory-1",
        content="timezone aware memory",
        embedding=np.array([1.0, 0.0]),
    )

    assert memory.timestamp.tzinfo is UTC
    assert memory.last_accessed.tzinfo is UTC

    graph = StructuredMemoryGraph()
    importance = graph._temporal_importance(memory)

    assert 0 < importance <= 1.0


def test_quad_persona_embeddings_are_stable_across_instances():
    text = "stable embedding seed"

    first = QuadPersonaMathematicalSystem()._embed_query(text)
    second = QuadPersonaMathematicalSystem()._embed_query(text)
    different = QuadPersonaMathematicalSystem()._embed_query("different text")

    assert np.array_equal(first, second)
    assert not np.array_equal(first, different)


def test_persona_confidence_is_deterministic_for_same_inputs():
    persona = ExpandedPersona(
        persona_id="knowledge-1",
        pod_type=PodType.KNOWLEDGE,
        name="Knowledge SME",
        description="Knowledge subject matter expert",
    )
    orchestrator = PodOrchestrator()
    context = {"query_id": "deterministic-confidence"}

    first = orchestrator._calculate_persona_confidence(persona, "query", context)
    second = orchestrator._calculate_persona_confidence(persona, "query", context)

    assert first == second


def test_refinement_threshold_is_reachable_and_configurable():
    workflow = RefinementWorkflow12Step()
    _, confidence = workflow.apply_workflow({"query": "phase 5"})

    assert confidence >= workflow.confidence_threshold
    assert workflow.confidence_threshold_met(confidence) is True

    strict_workflow = RefinementWorkflow12Step(confidence_threshold=0.995)
    assert strict_workflow.confidence_threshold_met(confidence) is False


def test_sufficiency_config_does_not_mutate_class_level_defaults():
    custom = PersonaSufficiencyTool({
        "thresholds": {"standard": {"complexity": 10}},
        "pod_caps": {"knowledge_max": 1},
    })
    default = PersonaSufficiencyTool()

    assert custom.thresholds["standard"]["complexity"] == 10
    assert custom.pod_caps["knowledge_max"] == 1
    assert default.thresholds["standard"]["complexity"] == PersonaSufficiencyTool.THRESHOLDS["standard"]["complexity"]
    assert default.pod_caps["knowledge_max"] == PersonaSufficiencyTool.POD_CAPS["knowledge_max"]
    assert PersonaSufficiencyTool.THRESHOLDS["standard"]["complexity"] == 60
    assert PersonaSufficiencyTool.POD_CAPS["knowledge_max"] == 6
