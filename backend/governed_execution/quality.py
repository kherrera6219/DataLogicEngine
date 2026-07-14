"""Versioned Phase 6 evidence, confidence, and convergence policy."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from typing import Iterable

from backend.governed_execution.contracts import (
    ClaimRecord,
    ConfidenceMeasurement,
    ConvergenceDecision,
    EvidenceRecord,
    GovernedMode,
    ValidatorRecord,
)


CONFIDENCE_FORMULA_VERSION = "dle-confidence.v1"
CONVERGENCE_VERSION = "dle-convergence.v1"

CONFIDENCE_WEIGHTS = {
    "claim_support": 0.35,
    "claim_consistency": 0.10,
    "source_quality": 0.20,
    "provenance_completeness": 0.15,
    "freshness": 0.10,
    "validator_pass_rate": 0.10,
}


def calculate_confidence(
    claims: Iterable[ClaimRecord],
    evidence: Iterable[EvidenceRecord],
    validators: Iterable[ValidatorRecord],
) -> ConfidenceMeasurement:
    """Calculate evidence-support coverage, never a correctness probability.

    A numeric value is emitted only when every named component is measured.
    Missing data keeps the result explicitly ``not_measured``.
    """

    claim_rows = [item for item in claims if item.claim_type == "factual"]
    evidence_rows = list(evidence)
    validator_rows = list(validators)
    measured_validators = [
        item for item in validator_rows if item.status in {"passed", "failed"}
    ]
    components: dict[str, float | None] = {
        "claim_support": _ratio(
            sum(item.status == "supported" for item in claim_rows),
            len(claim_rows),
        ),
        "claim_consistency": _ratio(
            sum(item.status != "contradicted" for item in claim_rows),
            len(claim_rows),
        ),
        "source_quality": _average(item.quality_score for item in evidence_rows),
        "provenance_completeness": _average(
            item.provenance_completeness for item in evidence_rows
        ),
        "freshness": _average(item.freshness_score for item in evidence_rows),
        "validator_pass_rate": (
            None
            if not validator_rows
            or len(measured_validators) != len(validator_rows)
            else _ratio(
                sum(item.status == "passed" for item in measured_validators),
                len(measured_validators),
            )
        ),
    }
    missing = [name for name, value in components.items() if value is None]
    if missing:
        return ConfidenceMeasurement(
            formula_version=CONFIDENCE_FORMULA_VERSION,
            value=None,
            status="not_measured",
            components=components,
            weights=dict(CONFIDENCE_WEIGHTS),
            missing_components=missing,
            explanation=(
                "Evidence-support coverage was not measured because required "
                f"components are unavailable: {', '.join(missing)}."
            ),
        )

    value = round(
        sum(float(components[name]) * weight for name, weight in CONFIDENCE_WEIGHTS.items()),
        4,
    )
    return ConfidenceMeasurement(
        formula_version=CONFIDENCE_FORMULA_VERSION,
        value=value,
        status="measured",
        components=components,
        weights=dict(CONFIDENCE_WEIGHTS),
        missing_components=[],
        explanation=(
            "Versioned evidence-support coverage from claim support and consistency, explicit "
            "source quality, provenance completeness, freshness, and validator results. "
            "It is not a probability that the answer is correct."
        ),
    )


def decide_convergence(
    claims: Iterable[ClaimRecord],
    validators: Iterable[ValidatorRecord],
    confidence: ConfidenceMeasurement,
    *,
    mode: GovernedMode,
    tier: str | None,
    iteration: int,
    max_iterations: int,
    requires_evidence: bool,
) -> ConvergenceDecision:
    """Choose a bounded finalize/refine/abstain/block terminal policy."""

    mode = GovernedMode.normalize(mode)
    claim_rows = list(claims)
    validator_rows = list(validators)
    failed = [item.validator_id for item in validator_rows if item.status == "failed"]
    policy_failed = any(
        item.status == "failed" and item.validator_type == "policy"
        for item in validator_rows
    )
    contradicted = [
        item.claim_id
        for item in claim_rows
        if item.status in {"contradicted", "contested"}
    ]
    unsupported = [
        item.claim_id
        for item in claim_rows
        if item.status in {"unsupported", "insufficient"}
    ]
    can_refine = (
        mode is GovernedMode.ENHANCED
        and iteration < max_iterations
        and not policy_failed
    )

    if policy_failed:
        return _decision(
            "block", "policy_validator_failed", iteration, max_iterations,
            unsupported, contradicted, failed,
        )
    if contradicted or (requires_evidence and unsupported):
        if can_refine:
            return _decision(
                "refine", "claim_support_requires_refinement", iteration, max_iterations,
                unsupported, contradicted, failed,
            )
        return _decision(
            "abstain", "evidence_insufficient_or_contradicted", iteration, max_iterations,
            unsupported, contradicted, failed,
        )
    if failed:
        if can_refine:
            return _decision(
                "refine", "validator_failed", iteration, max_iterations,
                unsupported, contradicted, failed,
            )
        return _decision(
            "abstain", "validator_failed_at_limit", iteration, max_iterations,
            unsupported, contradicted, failed,
        )

    reason = "claims_supported"
    if unsupported:
        reason = "low_risk_finalize_with_explicit_unsupported_claims"
    elif confidence.value is None:
        reason = "finalize_with_not_measured_confidence"
    return _decision(
        "finalize", reason, iteration, max_iterations,
        unsupported, contradicted, failed,
    )


def measure_evidence(evidence: EvidenceRecord, *, now: datetime | None = None) -> None:
    """Populate only provenance/freshness values that can be observed."""

    source = evidence.source
    if source is None:
        evidence.provenance_completeness = 0.0
        evidence.freshness_score = None
        evidence.quality_score = None
        return

    provenance_fields = (
        source.origin,
        source.author_publisher,
        source.captured_at or source.effective_at,
        source.permissions or None,
        source.content_hash,
        evidence.locator or None,
        source.embedding_revision,
    )
    evidence.provenance_completeness = round(
        sum(value is not None for value in provenance_fields) / len(provenance_fields),
        4,
    )

    explicit_quality = evidence.metadata.get("source_quality_score")
    evidence.quality_score = _bounded_float(explicit_quality)

    observed = _parse_time(source.effective_at or source.captured_at)
    max_age = _bounded_float(evidence.metadata.get("freshness_max_age_days"))
    if observed is None or max_age is None or max_age <= 0:
        evidence.freshness_score = None
        return
    reference = now or datetime.now(UTC)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=UTC)
    age_days = max(0.0, (reference - observed).total_seconds() / 86400)
    evidence.freshness_score = round(max(0.0, min(1.0, 1.0 - age_days / max_age)), 4)


def _decision(
    action: str,
    reason: str,
    iteration: int,
    max_iterations: int,
    unsupported: list[str],
    contradicted: list[str],
    failed: list[str],
) -> ConvergenceDecision:
    return ConvergenceDecision(
        action=action,
        reason=reason,
        iteration=iteration,
        max_iterations=max_iterations,
        terminal=action != "refine",
        unsupported_claim_ids=unsupported,
        contradicted_claim_ids=contradicted,
        failed_validator_ids=failed,
        decision_version=CONVERGENCE_VERSION,
    )


def stable_validator_id(kind: str, claim_id: str | None = None) -> str:
    digest = sha256(f"{kind}:{claim_id or 'run'}".encode("utf-8")).hexdigest()[:16]
    return f"validator_{digest}"


def _average(values: Iterable[float | None]) -> float | None:
    rows = list(values)
    if not rows or any(value is None for value in rows):
        return None
    measured = [float(value) for value in rows if value is not None]
    return round(sum(measured) / len(measured), 4)


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 4)


def _bounded_float(value: object) -> float | None:
    try:
        if value is None:
            return None
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return None


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    except (TypeError, ValueError):
        return None
