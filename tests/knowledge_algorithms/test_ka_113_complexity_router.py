"""KA-113 complexity router — multi-signal scoring (A7-1).

Confirms the router uses the three config-declared signals (query_length,
semantic_ambiguity, domain_specificity) rather than the previous length-only
heuristic, and routes via config thresholds/routing_map.
"""

from backend.knowledge_algorithms.ka_113_complexity_router import run


def _score(query: str) -> dict:
    result = run({"query": query})
    assert result["success"] is True
    # The KA base class wraps _run_logic output under "output".
    return result["output"]


def test_signals_present_and_normalized():
    r = _score("What is the SOX compliance deadline?")
    assert set(r["signals"]) == {"query_length", "semantic_ambiguity", "domain_specificity"}
    for v in r["signals"].values():
        assert 0.0 <= v <= 1.0
    assert 0.0 <= r["complexity_score"] <= 1.0


def test_trivial_query_is_low_tier():
    r = _score("hi")
    assert r["complexity_tier"] == "low"
    assert r["target_pipeline"] == "standard_pipeline"


def test_domain_heavy_query_scores_higher_than_plain_length_match():
    # Two queries of similar length; the regulated/technical one must score higher
    # than a plain prose one — proving scoring is not length-only.
    plain = _score("Please tell me a little bit about your day and how it went overall.")
    domain = _score("Compare HIPAA versus GDPR regulatory compliance audit liability.")
    assert domain["complexity_score"] > plain["complexity_score"]
    assert domain["signals"]["domain_specificity"] > 0.0


def test_ambiguity_signal_fires_on_comparison_and_multi_question():
    r = _score("Should we use Postgres or MySQL? And what about scaling? However it depends.")
    assert r["signals"]["semantic_ambiguity"] > 0.0


def test_high_complexity_routes_to_deep_pipeline():
    q = (
        "Compare HIPAA versus GDPR compliance for a clinical diagnosis API, "
        "and analyze the regulatory liability, encryption, and audit trade-offs "
        "across jurisdictions — however the financial actuarial impact is unclear."
    )
    r = _score(q)
    assert r["complexity_tier"] == "high"
    assert r["target_pipeline"] == "deep_recursive_pipeline"


def test_empty_query_is_safe():
    r = _score("")
    assert r["complexity_tier"] == "low"
    assert r["complexity_score"] == 0.0
