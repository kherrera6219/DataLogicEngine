"""Contracts for Layer 2/3 expansion and Layer 5 typed envelopes."""

import pytest
from pydantic import ValidationError

from core.simulation.layer2_knowledge import Layer2KnowledgeEngine
from core.simulation.layer3_expert import Layer3ExpertEngine
from core.simulation.layer5_schemas import (
    AxisCoord,
    Budget,
    Claim,
    ClaimType,
    Consensus,
    Constraint,
    ConstraintType,
    ContextPack,
    ErrorResponse,
    EvidenceItem,
    Impact,
    Layer5RunRequest,
    Layer5RunResponse,
    Likelihood,
    PersonaEnvelope,
    PersonaScores,
    PersonaType,
    ProblemSpec,
    RiskItem,
    RiskProfile,
    SafetyClass,
    SelfCheck,
    Severity,
    TaskType,
    VetoLog,
)


class GraphManager:
    def __init__(self, fail=False):
        self.fail = fail

    def get_nodes_by_axis(self, axis, limit):
        if self.fail:
            raise RuntimeError("graph down")
        return [{"node_id": f"live-{axis}", "axis": axis}][:limit]


class MemoryGraph:
    def search(self, value, limit):
        return [{"uid": f"anchor-{value}", "title": value}]

    def neighborhood(self, uid, depth):
        return {
            "nodes": [
                {"uid": uid, "title": "anchor"},
                {"uid": f"related-{uid}", "title": "Related concept"},
            ]
        }


def test_layer2_expands_mock_and_honeycomb_context():
    engine = Layer2KnowledgeEngine({"relevance_threshold": 0.3})
    context = {
        "query": "technology acquisition",
        "axis_scores": {1: 0.2, 3: 0.8, 18: 0.5},
        "pillar_context": {
            "primary_pillar": "acquisition",
            "matched_pillars": [{"pillar": "technology"}, {"pillar": "finance"}],
            "confidence": 0.7,
        },
        "layer1_entry": {"knowledge_expansion": {"target_axes": [1]}},
    }
    result = engine.process(context)

    expanded = result["layer2_knowledge"]["expanded_axes"]
    assert set(expanded) == {1, 3, 18}
    assert expanded[18]["nodes"][0]["axis_name"] == "Axis 18"
    assert result["cross_domain_links"][0]["mapping_key"] == "acquisition_technology"
    assert result["enriched_knowledge"]["node_count"] >= 3
    assert result["layer2_knowledge"]["information_branches"]
    assert 0 <= result["layer2_knowledge"]["layer_confidence"] <= 0.95
    assert engine.get_stats()["expansions_performed"] == 1


def test_layer2_live_graph_retrieval_failure_and_live_memory_links():
    live = Layer2KnowledgeEngine(
        graph_manager=GraphManager(), memory_graph_getter=lambda: MemoryGraph()
    )
    nodes = live._expand_along_axes({2: 0.9}, {})
    assert nodes[2]["nodes"] == [{"node_id": "live-2", "axis": 2}]
    links = live._find_cross_domain_links(
        {"primary_pillar": "technology", "matched_pillars": [{"pillar": "technology"}]}, {}
    )
    assert links[0]["mapping_key"].startswith("uskd:")
    assert links[0]["concepts"] == ["Related concept"]

    failing = Layer2KnowledgeEngine(
        graph_manager=GraphManager(fail=True), memory_graph_getter=lambda: (_ for _ in ()).throw(RuntimeError("down"))
    )
    assert failing._retrieve_axis_nodes(1, 0.5) == []
    assert failing._find_live_graph_links("", []) == []
    assert failing._calculate_layer_confidence({}, []) == 0
    assert failing._broaden_context({}, [], {}) == []


class PersonaEngine:
    def __init__(self, fail=False):
        self.fail = fail

    def process_query(self, query):
        if self.fail:
            raise RuntimeError("persona down")
        return {
            "persona_responses": {
                "knowledge": {"confidence": 0.9, "recommendations": [f"Review {query}"]},
                "sector": {"recommendations": []},
            }
        }


def test_layer3_expert_full_analysis_and_conflict_edges():
    engine = Layer3ExpertEngine(persona_engine=PersonaEngine())
    query = "Federal defense procurement DFARS GDPR privacy audit documentation access control"
    result = engine.process(
        {"query": query, "pillar_context": {"primary_pillar": "defense"}, "expert_roles": []}
    )

    assert set(result["layer3_expert"]["experts_activated"]) == {"knowledge", "sector"}
    assert {item["framework_id"] for item in result["regulatory_constraints"]} >= {"DFARS", "GDPR"}
    assert result["compliance_requirements"]
    assert result["expert_analysis"]["recommendations"]
    assert 0.3 <= result["layer3_expert"]["layer_confidence"] <= 0.95
    assert engine.get_stats()["regulatory_checks"] == 1

    integrated = {
        "confidence_scores": {"low": 0.4, "high": 0.95},
        "recommendations": [
            {"source": "regulatory", "recommendation": "must"},
            {"source": "other", "recommendation": "do"},
        ],
    }
    conflicts = engine._detect_conflicts(integrated)
    assert conflicts[0]["conflict_type"] == "confidence_divergence"
    assert engine._detect_conflicts({}) == []
    assert engine._calculate_layer_confidence({}, {}, {}, conflicts) >= 0.3


def test_layer3_persona_fallback_and_default_compliance():
    engine = Layer3ExpertEngine(persona_engine=PersonaEngine(fail=True))
    primary = engine._activate_primary_personas("query", {}, [])
    assert set(primary["activated"]) == {"knowledge_expert", "sector_expert"}
    assert engine._perform_regulatory_analysis("unmatched", {})["confidence"] == 0.5
    compliance = engine._perform_compliance_analysis("unmatched", {})
    assert compliance["applicable_standards"][0]["standard_id"] == "general_compliance"

    integrated = engine._integrate_analyses(
        {
            "responses": {"knowledge": {"recommendations": ["one"]}},
            "confidence_scores": {},
        },
        {"constraints": [], "confidence": 0.5},
        {"requirements": [], "confidence": 0.5},
    )
    assert integrated["recommendations"] == [{"source": "knowledge", "recommendation": "one"}]
    assert integrated["average_confidence"] == 0.5


def test_layer5_schema_complete_request_response_round_trip_and_validation():
    budget = Budget(time_ms=1000, tokens=500, max_iterations=2)
    spec = ProblemSpec(
        task_type=TaskType.evaluate,
        success_criteria=["qualified"],
        risk_profile=RiskProfile(domain_risk="high", safety_class=SafetyClass.internal),
    )
    coord = AxisCoord(a1="time", a17="learning", custom_axis="allowed")
    evidence = EvidenceItem(evidence_id="ev-1", kind="doc", title="Evidence")
    request = Layer5RunRequest(
        run_id="run-1",
        trace_id="trace-1",
        problem_spec=spec,
        coord=coord,
        context_pack=ContextPack(evidence=[evidence], budgets=budget),
    )
    assert request.coord.model_dump()["custom_axis"] == "allowed"

    envelope = PersonaEnvelope(
        persona_type=PersonaType.KNOWLEDGE,
        persona_id="knowledge",
        claims=[
            Claim(
                claim_id="claim-1",
                text="Qualified",
                claim_type=ClaimType.fact,
                confidence=0.9,
            )
        ],
        constraints=[
            Constraint(
                constraint_id="constraint-1",
                text="Must qualify",
                severity=Severity.block,
                type=ConstraintType.evidence,
            )
        ],
        risks=[
            RiskItem(
                risk_id="risk-1",
                text="Missing proof",
                impact=Impact.high,
                likelihood=Likelihood.med,
            )
        ],
        self_check=SelfCheck(contradictions_found=False, hallucination_risk=0.1),
        scores=PersonaScores(
            confidence_overall=0.9,
            coverage=0.8,
            evidence_quality=0.9,
            policy_alignment=1,
        ),
    )
    response = Layer5RunResponse(
        run_id=request.run_id,
        trace_id=request.trace_id,
        personas_spawned=[PersonaType.KNOWLEDGE],
        persona_outputs=[envelope],
        veto_log=VetoLog(vetoed=False),
        consensus=Consensus(status="FINALIZE", confidence_sys=0.9),
    )
    assert response.model_dump(mode="json")["consensus"]["release_threshold"] == 0.92
    assert ErrorResponse(error="bad", message="failed", trace_id="trace").error == "bad"

    with pytest.raises(ValidationError):
        Budget(time_ms=0, tokens=1, max_iterations=1)
    with pytest.raises(ValidationError):
        Claim(claim_id="bad", text="bad", claim_type=ClaimType.fact, confidence=2)
