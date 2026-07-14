from backend.governed_execution.contracts import (
    ClaimRecord,
    ConfidenceMeasurement,
    GovernedMode,
    ValidatorRecord,
)
from backend.governed_execution.quality import decide_convergence


def _confidence(value: float | None = 0.9) -> ConfidenceMeasurement:
    return ConfidenceMeasurement(
        formula_version="dle-confidence.v1",
        value=value,
        status="measured" if value is not None else "not_measured",
    )


def test_supported_claims_finalize():
    decision = decide_convergence(
        [ClaimRecord(claim_id="c1", text="Supported", status="supported")],
        [ValidatorRecord("v1", "claim_support", "v1", "passed")],
        _confidence(),
        mode=GovernedMode.ENHANCED,
        tier="moderate",
        iteration=0,
        max_iterations=1,
        requires_evidence=True,
    )

    assert decision.action == "finalize"


def test_insufficient_claim_refines_once_then_abstains():
    claims = [ClaimRecord(claim_id="c1", text="Unsupported", status="insufficient")]
    first = decide_convergence(
        claims,
        [],
        _confidence(None),
        mode=GovernedMode.ENHANCED,
        tier="high_stakes",
        iteration=0,
        max_iterations=1,
        requires_evidence=True,
    )
    terminal = decide_convergence(
        claims,
        [],
        _confidence(None),
        mode=GovernedMode.ENHANCED,
        tier="high_stakes",
        iteration=1,
        max_iterations=1,
        requires_evidence=True,
    )

    assert first.action == "refine"
    assert terminal.action == "abstain"
    assert terminal.terminal is True


def test_policy_validator_blocks_and_contradiction_terminates():
    blocked = decide_convergence(
        [],
        [ValidatorRecord("v1", "policy", "v1", "failed")],
        _confidence(None),
        mode=GovernedMode.STANDARD,
        tier="moderate",
        iteration=0,
        max_iterations=0,
        requires_evidence=False,
    )
    contradicted = decide_convergence(
        [ClaimRecord(claim_id="c1", text="Contested", status="contradicted")],
        [],
        _confidence(None),
        mode=GovernedMode.ENHANCED,
        tier="high_stakes",
        iteration=2,
        max_iterations=2,
        requires_evidence=True,
    )

    assert blocked.action == "block"
    assert contradicted.action == "abstain"
