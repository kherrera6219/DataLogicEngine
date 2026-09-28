"""Shared confidence display states must not invent a numeric score."""

from backend.governed_execution.contracts import ConfidenceMeasurement, ValidatorRecord
from backend.governed_execution.quality import build_confidence_display


def _measurement(
    *,
    status: str,
    value: float | None,
    missing: list[str] | None = None,
) -> ConfidenceMeasurement:
    return ConfidenceMeasurement(
        formula_version="dle-confidence.v1",
        value=value,
        status=status,
        missing_components=missing or [],
        explanation="Fixture measurement explanation.",
    )


def test_measured_confidence_display_preserves_formula_value():
    display = build_confidence_display(
        _measurement(status="measured", value=0.82),
        validators=[],
        evidence_count=2,
    )

    assert display["status"] == "measured"
    assert display["value"] == 0.82
    assert display["formula_version"] == "dle-confidence.v1"


def test_unmeasured_confidence_display_explains_missing_component():
    display = build_confidence_display(
        _measurement(status="not_measured", value=None, missing=["freshness"]),
        validators=[],
        evidence_count=2,
    )

    assert display["status"] == "not_measured"
    assert display["value"] is None
    assert display["reason"] == "required_measurement_components_unavailable"
    assert display["missing_components"] == ["freshness"]


def test_no_evidence_has_a_distinct_insufficient_evidence_state():
    display = build_confidence_display(
        _measurement(
            status="not_measured",
            value=None,
            missing=["claim_support", "source_quality"],
        ),
        validators=[],
        evidence_count=0,
    )

    assert display["status"] == "insufficient_evidence"
    assert display["value"] is None
    assert display["reason"] == "no_governed_evidence_available"


def test_failed_validator_suppresses_numeric_confidence_display():
    display = build_confidence_display(
        _measurement(status="measured", value=0.91),
        validators=[
            ValidatorRecord(
                validator_id="validator-1",
                validator_type="evidence",
                version="1",
                status="failed",
            )
        ],
        evidence_count=3,
    )

    assert display["status"] == "validation_failed"
    assert display["value"] is None
    assert display["reason"] == "one_or_more_governed_validators_failed"
