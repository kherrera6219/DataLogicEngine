"""Risk-tier regressions for qualified Knowledge Algorithms."""

from backend.knowledge_algorithms.risk_classifier import RiskTier, classify


def test_ka090_quantization_proposal_is_read_only() -> None:
    profile = classify("KA-090")

    assert profile.tier is RiskTier.READ_ONLY
    assert profile.requires_confirmation is False
    assert profile.reason == "Returns analysis or recommendations only"
