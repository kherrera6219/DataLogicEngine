"""Contract tests for POV policy decisions and normalized delta output."""

import pytest

from core.simulation.pov_delta import (
    DeltaType,
    EvidenceRef,
    Lane,
    POVDelta,
    POVDeltaCollection,
    POVRecommendations,
    POVResponse,
    POVTelemetry,
    Severity,
    create_delta_normalizer,
)
from core.simulation.pov_policy import (
    POVBudget,
    POVMode,
    POVPlan,
    ScoringSignals,
    ViewpointSelection,
    create_pov_policy_service,
)


def test_delta_models_round_trip_and_collection_queries():
    evidence = EvidenceRef(
        ref_id="ev-1",
        ref_type="node",
        uri="node://one",
        relevance=0.9,
        excerpt="x" * 250,
    )
    delta = POVDelta(
        delta_type=DeltaType.RISK,
        severity=Severity.HIGH,
        owner_lane=Lane.REGULATORY,
        description="Regulatory exposure must be reviewed",
        rationale="The control is mandatory",
        source_viewpoint="auditor",
        source_lane="compliance",
        tags=["control"],
    )
    original_hash = delta.content_hash
    delta.add_evidence(evidence)
    delta.mark_resolved("Control added", "automated")

    serialized = delta.to_dict()
    assert len(serialized["evidence_refs"][0]["excerpt"]) == 200
    assert delta.resolution_method == "automated"
    restored = POVDelta.from_dict(serialized)
    assert restored.delta_type is DeltaType.RISK
    assert restored.severity is Severity.HIGH
    assert restored.owner_lane is Lane.REGULATORY
    assert restored.content_hash == original_hash
    assert Severity.CRITICAL.priority == 1
    assert Severity.LOW.priority == 4

    collection = POVDeltaCollection()
    for delta_type in DeltaType:
        collection.add_delta(
            POVDelta(
                delta_type=delta_type,
                severity=Severity.CRITICAL if delta_type is DeltaType.CONSTRAINT else Severity.LOW,
                owner_lane=Lane.KNOWLEDGE,
                description=f"Valid {delta_type.value} description",
                source_viewpoint="test",
            )
        )
    assert collection.total_count == len(DeltaType)
    assert collection.critical_count == 1
    assert collection.unresolved_count == len(DeltaType)
    assert len(collection.get_by_lane(Lane.KNOWLEDGE)) == len(DeltaType)
    assert len(collection.get_by_severity(Severity.CRITICAL)) == 1
    assert collection.to_dict()["summary"]["total_count"] == len(DeltaType)


def test_response_support_models_serialize_complete_contract():
    recommendations = POVRecommendations(
        needs_more_retrieval=True,
        retrieval_hints=["policy"],
        needs_recursion=True,
        recursion_reason="low coverage",
        suggested_viewpoints=["auditor"],
    )
    telemetry = POVTelemetry(
        start_time="start",
        end_time="end",
        latency_ms=25,
        viewpoints_requested=2,
        viewpoints_run=1,
        viewpoints_failed=1,
        recursions=1,
        deltas_generated=3,
        evidence_bindings=2,
        budget_exceeded=True,
    )
    response = POVResponse(
        query_id="query-1",
        selected_viewpoints=["auditor"],
        evidence_bindings={"delta": ["ev-1"]},
        recommendations=recommendations,
        telemetry=telemetry,
        confidence=0.91,
    )

    payload = response.to_dict()
    assert payload["response_id"].startswith("pov_resp_")
    assert payload["recommendations"]["retrieval_hints"] == ["policy"]
    assert payload["telemetry"]["budget_exceeded"] is True
    assert payload["confidence"] == 0.91


@pytest.mark.parametrize(
    ("text", "expected_type", "expected_severity", "expected_lane"),
    [
        ("A critical safety blocker must stop release", DeltaType.CONSTRAINT, Severity.CRITICAL, Lane.CROSS_CUTTING),
        ("A major regulatory vulnerability creates risk", DeltaType.RISK, Severity.HIGH, Lane.REGULATORY),
        ("Please clarify this recommended policy question", DeltaType.QUESTION, Severity.MEDIUM, Lane.COMPLIANCE),
        ("The technical design has a missing requirement", DeltaType.REQUIREMENT, Severity.LOW, Lane.KNOWLEDGE),
        ("Operational teams can improve the workflow", DeltaType.RECOMMENDATION, Severity.LOW, Lane.SECTOR),
    ],
)
def test_normalizer_classifies_text(text, expected_type, expected_severity, expected_lane):
    normalizer = create_delta_normalizer()
    delta = normalizer._parse_text(text, "viewpoint", "cross_cutting")

    assert delta.delta_type is expected_type
    assert delta.severity is expected_severity
    assert delta.owner_lane is expected_lane


def test_normalizer_handles_invalid_values_duplicates_validation_and_evidence():
    normalizer = create_delta_normalizer({"strict": True})
    output = {
        "viewpoint_id": "auditor",
        "lane": "not-a-lane",
        "findings": [
            {
                "type": "not-a-type",
                "severity": "not-a-severity",
                "owner_lane": "not-a-lane",
                "description": "Mandatory architecture control requires evidence",
                "rationale": "qualification",
                "confidence": 0.95,
                "tags": ["architecture"],
            },
            {"description": "bad"},
        ],
        "perspective": {
            "key_points": [
                "Architecture control requires matching evidence",
                "short",
            ]
        },
        "constraints": ["Mandatory architecture control requires evidence"],
        "risks": [{"description": "Architecture evidence exposure is a risk"}],
        "requirements": ["Architecture evidence requirement is missing"],
        "questions": ["Clarify the architecture evidence question"],
    }
    graph = {
        "nodes": [
            {
                "node_id": "architecture-control",
                "content": "Architecture control requires strong evidence for qualification",
            }
        ]
    }

    collection = normalizer.normalize([output, output], graph)

    assert collection.total_count >= 5
    assert collection.total_count < 14
    assert any(delta.evidence_refs for delta in collection._all_deltas())
    assert normalizer._parse_text("tiny", "vp", "knowledge") is None
    assert normalizer._validate_delta(POVDelta(description="good", source_viewpoint="")) is False
    assert normalizer._classify_lane("unmatched content", "stakeholder") is Lane.STAKEHOLDER
    assert normalizer._classify_lane("unmatched content", "invalid") is Lane.CROSS_CUTTING


def test_policy_models_and_default_budget_round_trip():
    budget = POVBudget.from_dict({"max_ms": 123, "knowledge_max": 2})
    assert budget.max_ms == 123
    assert budget.max_viewpoints == 12
    assert budget.to_dict()["knowledge_max"] == 2

    signals = ScoringSignals(
        breadth_score=60,
        stakes_score=50,
        conflict_score=0.3,
        coverage_score=0.7,
        is_defense=True,
        pillars_activated=2,
        sectors_activated=1,
        subsystems_detected=3,
    )
    assert signals.overall_complexity() == pytest.approx(47.0)
    assert signals.to_dict()["overall_complexity"] == pytest.approx(47.0)

    viewpoint = ViewpointSelection("auditor", "Auditor", "compliance", reason="test")
    plan = POVPlan(viewpoints=[viewpoint], signals=signals, budget=budget)
    payload = plan.to_dict()
    assert plan.total_viewpoints == 1
    assert payload["viewpoints"][0]["viewpoint_id"] == "auditor"
    assert payload["signals"]["is_defense"] is True
    assert payload["budget"]["max_ms"] == 123

    default_plan = POVPlan(plan_id="fixed", created_at="fixed")
    assert default_plan.lane_counts == {
        "knowledge": 0,
        "sector": 0,
        "regulatory": 0,
        "compliance": 0,
        "stakeholder": 0,
    }


@pytest.mark.parametrize(
    ("score", "mode"),
    [(0, POVMode.BYPASS), (20, POVMode.LIGHT), (40, POVMode.STANDARD), (80, POVMode.COMMITTEE)],
)
def test_policy_selects_each_mode(score, mode):
    service = create_pov_policy_service()
    signals = ScoringSignals(breadth_score=score / 0.3, coverage_score=1.0)
    assert service._select_mode(signals, "standard") is mode


def test_policy_evaluate_forces_high_assurance_and_committee_roster():
    service = create_pov_policy_service(
        {"thresholds": {"bypass": 15, "light": 35, "standard": 60}}
    )
    query = (
        "Military safety critical classified ITAR GDPR system and architecture plus "
        "operations with combined controls including many subsystems"
    )
    quad_outputs = {
        "knowledge": {"confidence": 0.9},
        "sector": {"confidence": 0.2, "has_gaps": True},
        "regulatory": "ignored",
    }
    context = {"domain": "aerospace", "axis_vector": {1: True, 2: True, 3: True}}

    plan = service.evaluate(query, context, quad_outputs, policy_mode="unknown")

    assert plan.policy_mode == "high_assurance"
    assert plan.target_confidence == 0.995
    assert plan.mode is POVMode.COMMITTEE
    assert plan.signals.is_defense is True
    assert plan.signals.is_safety_critical is True
    assert plan.signals.is_export_controlled is True
    assert plan.signals.is_heavily_regulated is True
    assert plan.signals.conflict_score > 0.2
    assert plan.signals.coverage_score < 0.8
    assert plan.lane_counts["regulatory"] == 2
    assert {item.viewpoint_id for item in plan.viewpoints} >= {
        "auditor",
        "operator",
        "decision_maker",
        "administrator",
        "safety_advocate",
    }
    assert len(plan.decision_reasons) == 6


def test_policy_rosters_cover_bypass_light_standard_and_committee_branches():
    service = create_pov_policy_service()
    budget = POVBudget(knowledge_max=5, sector_max=1, regulatory_max=1, compliance_max=1, stakeholder_max=2)

    bypass, bypass_counts = service._select_viewpoints(ScoringSignals(), POVMode.BYPASS, {}, budget)
    light, light_counts = service._select_viewpoints(ScoringSignals(), POVMode.LIGHT, {}, budget)
    standard, standard_counts = service._select_viewpoints(
        ScoringSignals(is_heavily_regulated=True), POVMode.STANDARD, {}, budget
    )
    committee, committee_counts = service._select_viewpoints(
        ScoringSignals(subsystems_detected=0), POVMode.COMMITTEE, {}, budget
    )

    assert bypass == [] and sum(bypass_counts.values()) == 0
    assert [item.viewpoint_id for item in light] == ["auditor", "operator"]
    assert light_counts["stakeholder"] == 1
    assert [item.viewpoint_id for item in standard] == ["auditor", "operator", "external_validator"]
    assert standard_counts["regulatory"] == 1
    assert len(committee) == 3
    assert committee_counts["knowledge"] == 3
    assert committee_counts["sector"] == 1
    assert committee_counts["regulatory"] == 1
    assert committee_counts["compliance"] == 1
    assert committee_counts["stakeholder"] == 2


def test_policy_signal_edges_and_high_assurance_thresholds():
    service = create_pov_policy_service()
    long_query = " ".join(["combined"] * 55)
    signals = service._compute_signals(long_query, {"axis_vector": {1: True} }, {})
    assert signals.breadth_score == 33
    assert signals.coverage_score == 0.5

    assert service._should_force_high_assurance(ScoringSignals(stakes_score=60)) is True
    assert service._should_force_high_assurance(ScoringSignals()) is False
    assert service._select_mode(ScoringSignals(coverage_score=1), "high_assurance") is POVMode.LIGHT

    high_breadth_reasons = service._generate_decision_reasons(
        ScoringSignals(breadth_score=51, coverage_score=1), POVMode.STANDARD
    )
    assert high_breadth_reasons[0] == "High complexity (breadth=51)"

    no_regulatory, counts = service._select_viewpoints(
        ScoringSignals(subsystems_detected=4),
        POVMode.COMMITTEE,
        {},
        POVBudget(knowledge_max=3),
    )
    assert counts["knowledge"] == 3
    assert counts["regulatory"] == 1
    assert no_regulatory[0].viewpoint_id == "auditor"
