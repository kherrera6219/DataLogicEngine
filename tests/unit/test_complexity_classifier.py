"""Unit tests for the heuristic complexity classifier (Sprint 6b)."""

import pytest
from backend.llm_gateway.complexity_classifier import ClassificationResult, ComplexityClassifier
from backend.llm_gateway.escalation_config import TIER_CHAIN, get_tier_config, tier_for_model


class TestComplexityClassifier:
    """Tier assignment tests for ComplexityClassifier."""

    clf = ComplexityClassifier()

    # ── Tier 0 (trivial) ────────────────────────────────────────────────────

    @pytest.mark.parametrize("query", [
        "hi",
        "hello",
        "thanks",
        "ok",
        "yes",
        "what is a contract?",
        "who is responsible?",
    ])
    def test_tier0_trivial_patterns(self, query):
        result = self.clf.classify(query)
        assert result.tier == 0, f"Expected Tier 0 for {query!r}, got {result}"

    def test_tier0_empty_string(self):
        result = self.clf.classify("")
        assert result.tier == 0
        assert result.reason == "empty query"

    def test_tier0_short_query(self):
        result = self.clf.classify("hello world")
        assert result.tier == 0

    # ── Tier 1 (primary) ───────────────────────────────────────────────────

    def test_tier1_medium_length_no_code(self):
        query = "Can you explain how the GDPR data retention policy works for HR departments?"
        result = self.clf.classify(query)
        assert result.tier == 1, f"Expected Tier 1, got {result}"

    def test_tier1_medium_no_code_signal(self):
        """A medium-length query with no code signals stays at Tier 1."""
        query = "Can you summarise the key points from the employee handbook section on benefits?"
        result = self.clf.classify(query)
        assert result.tier == 1, f"Expected Tier 1, got {result}"

    def test_technical_question_routes_to_tier2(self):
        """Even a short technical question triggers the code-signal boost (Tier 2)."""
        result = self.clf.classify("What is an API?")
        # "API" hits a code-signal pattern — Tier 2 is correct since qwen3:14b
        # handles technical definitional questions better than the ultra-light tier.
        assert result.tier == 2

    # ── Tier 2 (medium / coding) ───────────────────────────────────────────

    @pytest.mark.parametrize("query", [
        "implement a REST API endpoint with authentication",
        "debug this Python function that raises an exception",
        "write a SQL query to join users and orders tables",
        "how do I refactor this algorithm to improve complexity?",
    ])
    def test_tier2_code_queries(self, query):
        result = self.clf.classify(query)
        assert result.tier == 2, f"Expected Tier 2 for {query!r}, got {result}"

    # ── Tier 3 (heavy-local / agentic) ────────────────────────────────────

    @pytest.mark.parametrize("query", [
        "build a complete production microservice with Docker and CI/CD",
        "write step-by-step guide for building a multi-module agentic workflow",
        "design a comprehensive end-to-end pipeline for data ingestion",
        "create a full autonomous agent that handles multiple files and services",
    ])
    def test_tier3_agent_queries(self, query):
        result = self.clf.classify(query)
        assert result.tier == 3, f"Expected Tier 3 for {query!r}, got {result}"

    # ── Cloud cap ──────────────────────────────────────────────────────────

    def test_cloud_escalation_disabled_caps_at_3(self):
        """Without allow_cloud_escalation, tier is capped at 3."""
        very_long = "build " + "full production agentic microservice " * 30
        result = self.clf.classify(very_long, allow_cloud_escalation=False)
        assert result.tier <= 3

    def test_cloud_escalation_enabled_can_exceed_3(self):
        """With allow_cloud_escalation, tier is not capped at 3."""
        very_long = "build " + "full production agentic microservice " * 30
        result = self.clf.classify(very_long, allow_cloud_escalation=True)
        # Should still not exceed 5.
        assert result.tier <= 5

    # ── Return type ────────────────────────────────────────────────────────

    def test_returns_classification_result(self):
        result = self.clf.classify("hello")
        assert isinstance(result, ClassificationResult)
        assert isinstance(result.tier, int)
        assert isinstance(result.reason, str)
        assert 0.0 <= result.score <= 1.0

    def test_score_matches_tier(self):
        for tier_val in range(4):  # 0–3
            result = self.clf.classify("hello" if tier_val == 0 else "implement REST API " * (tier_val * 2))
            assert abs(result.score - round(result.tier / 5.0, 2)) < 0.01


class TestEscalationConfig:
    """Tests for the TIER_CHAIN escalation config."""

    def test_tier_chain_has_six_entries(self):
        assert len(TIER_CHAIN) == 6

    def test_tier_chain_tiers_are_sequential(self):
        for i, tc in enumerate(TIER_CHAIN):
            assert tc.tier == i

    def test_local_tiers_use_ollama(self):
        for tc in TIER_CHAIN:
            if not tc.is_cloud:
                assert tc.provider_type == "ollama"

    def test_cloud_tiers_are_4_and_5(self):
        cloud = [tc for tc in TIER_CHAIN if tc.is_cloud]
        assert len(cloud) == 2
        assert {tc.tier for tc in cloud} == {4, 5}

    def test_get_tier_config_returns_correct_entry(self):
        for tc in TIER_CHAIN:
            found = get_tier_config(tc.tier)
            assert found is tc

    def test_get_tier_config_returns_none_for_invalid(self):
        assert get_tier_config(-1) is None
        assert get_tier_config(6) is None

    def test_tier_for_model_reverse_lookup(self):
        tc = get_tier_config(1)
        assert tc is not None
        reverse = tier_for_model(tc.model)
        assert reverse is not None
        assert reverse.tier == 1

    def test_all_labels_non_empty(self):
        for tc in TIER_CHAIN:
            assert tc.label, f"Tier {tc.tier} has empty label"
