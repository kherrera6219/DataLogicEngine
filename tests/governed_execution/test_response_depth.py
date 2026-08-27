"""Deterministic response-depth selection for complete governed answers."""

from backend.governed_execution.contracts import GovernedContext, GovernedRequest
from backend.governed_execution.prompt import (
    build_provider_messages,
    select_response_depth,
)


def _context(query: str, *, explicit: str | None = None) -> GovernedContext:
    constraints = {"response_depth": explicit} if explicit else {}
    context = GovernedContext(
        GovernedRequest(
            messages=[{"role": "user", "content": query}],
            constraints=constraints,
        )
    )
    context.query = query
    return context


def test_analysis_intent_selects_comprehensive_response_depth():
    context = _context("Give me a detailed review of the major Mars engine designs")

    profile = select_response_depth(context)
    messages = build_provider_messages(context)

    assert profile["profile"] == "comprehensive"
    assert profile["additional_provider_calls_authorized"] is False
    assert "Complete every requested section" in messages[0]["content"]
    assert context.request.metadata["response_depth"] == profile


def test_direct_fact_question_selects_concise_response_depth():
    profile = select_response_depth(_context("What is the capital of France?"))

    assert profile["profile"] == "concise"
    assert profile["selection_reason"] == "bounded_direct_question"


def test_explicit_bounded_profile_wins_over_heuristic():
    profile = select_response_depth(
        _context("Give me a detailed review", explicit="standard")
    )

    assert profile["profile"] == "standard"
    assert profile["selection_reason"] == "explicit_request_constraint"
