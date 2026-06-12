"""KA-005 suggested_tier emission (A5-3 / A8).

KA-005 previously returned only a category, so TruthCore.determine_tier's
KA-005 branch (which reads `suggested_tier`) always fell through to the
heuristic. KA-005 now maps its category to a workflow tier.
"""

from backend.knowledge_algorithms.ka_05_query_classification import run


def _out(query: str) -> dict:
    r = run({"query": query})
    assert r["success"] is True
    return r["output"]


def test_regulatory_query_maps_to_high_stakes():
    out = _out("What are the GDPR compliance and audit regulation requirements?")
    assert out["category"] == "REGULATORY"
    assert out["suggested_tier"] == "high_stakes"
    assert out["tier"] == out["suggested_tier"]


def test_technical_query_maps_to_moderate():
    out = _out("How do I debug this database api error in my code?")
    assert out["category"] == "TECHNICAL"
    assert out["suggested_tier"] == "moderate"


def test_general_query_maps_to_trivial():
    out = _out("hello there")
    assert out["category"] == "GENERAL"
    assert out["suggested_tier"] == "trivial"


def test_tier_is_a_valid_truthcore_tier():
    valid = {"trivial", "moderate", "high_stakes", "extreme", "autonomous"}
    for q in ("analyze this trend", "policy compliance", "random text", ""):
        assert _out(q)["suggested_tier"] in valid
