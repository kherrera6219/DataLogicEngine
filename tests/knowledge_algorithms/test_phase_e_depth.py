from datetime import UTC, datetime, timedelta

from backend.knowledge_algorithms.ka_02_tree_of_thought import (
    KA002Input,
    KA002TreeOfThought,
)
from backend.knowledge_algorithms.ka_14_confidence_scoring import (
    KA014ConfidenceScoring,
    KA014Input,
)
from backend.knowledge_algorithms.ka_22_risk_assessment import (
    KA022Input,
    KA022RiskAssessment,
)
from backend.knowledge_algorithms.ka_23_belief_decay import KA023BeliefDecay, KA023Input


def test_ka014_domain_calibration_varies_with_domain_scores():
    ka = KA014ConfidenceScoring({})
    low = ka.run(
        KA014Input(
            domain_scores={"evidence": 0.2, "risk": 0.3}, risk_domain="high_risk"
        )
    )["output"]["calibrated_confidence"]
    high = ka.run(
        KA014Input(
            domain_scores={"evidence": 0.9, "risk": 0.85}, risk_domain="standard"
        )
    )["output"]["calibrated_confidence"]

    assert high > low
    assert high != 0.9


def test_ka023_domain_specific_lambdas_decay_healthcare_faster_than_general():
    reference_time = datetime(2026, 7, 25, tzinfo=UTC)
    old_timestamp = (reference_time - timedelta(days=30)).isoformat()

    ka = KA023BeliefDecay({})
    healthcare = ka.run(
        KA023Input(
            reference_time=reference_time,
            knowledge_items=[
                {
                    "knowledge_id": "healthcare-1",
                    "observed_at": old_timestamp,
                    "current_confidence": 1.0,
                    "domain": "healthcare",
                }
            ],
        )
    )["output"]["proposals"][0]
    general = ka.run(
        KA023Input(
            reference_time=reference_time,
            knowledge_items=[
                {
                    "knowledge_id": "general-1",
                    "observed_at": old_timestamp,
                    "current_confidence": 1.0,
                    "domain": "general",
                }
            ],
        )
    )["output"]["proposals"][0]

    assert healthcare["decay_rate"] == 0.05
    assert general["decay_rate"] == 0.001
    assert healthcare["proposed_confidence"] < general["proposed_confidence"]


def test_ka002_returns_three_deterministic_sub_goals():
    result = KA002TreeOfThought({}).run(
        KA002Input(goal="validate DSQP release readiness")
    )["output"]

    assert len(result["sub_goals"]) == 3
    assert [goal["branch"] for goal in result["sub_goals"]] == [
        "evidence",
        "risk",
        "synthesis",
    ]
    assert result["best_path"]


def test_ka022_returns_axis15_six_dimension_risk_schema():
    result = KA022RiskAssessment({}).run(
        KA022Input(
            recommendation="Fix compliance audit breach before public deadline to protect reputation",
            impact_scores={"security": 0.8},
        )
    )["output"]

    assert set(result["axis15_dimensions"]) == {
        "technical",
        "security",
        "compliance",
        "financial",
        "schedule",
        "reputational",
    }
    assert result["dominant_dimension"] in result["axis15_dimensions"]
    assert result["overall_risk_score"] > 0
