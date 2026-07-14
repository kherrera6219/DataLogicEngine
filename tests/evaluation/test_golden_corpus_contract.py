from backend.evaluation import load_golden_corpus


def test_golden_corpus_covers_required_semantic_and_policy_cases():
    corpus = load_golden_corpus()
    cases = corpus["cases"]
    categories = {item["category"] for item in cases}

    assert corpus["schema_version"] == "dle-golden-corpus.v1"
    assert corpus["license_review"]["status"] == "approved_repository_authored_synthetic_only"
    assert len({item["id"] for item in cases}) == len(cases)
    assert {
        "normal_chat", "local_retrieval", "graph_reasoning",
        "contradictory_evidence", "stale_evidence", "abstention",
        "prompt_injection", "knowledge_algorithm", "simulation",
        "provider_disabled",
    } <= categories
    for item in cases:
        expected = item["expected"]
        assert isinstance(expected["claim_outcomes"], list)
        assert isinstance(expected["required_evidence_ids"], list)
        assert isinstance(expected["forbidden_evidence_ids"], list)
        assert expected["acceptable_uncertainty"]
        assert expected["required_trace_stages"]
        assert expected["policy_outcome"]
        assert expected["terminal_action"] in {"finalize", "abstain", "block"}
        assert all(source["license"] == "repository-authored" for source in item["sources"])
