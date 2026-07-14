from backend.governed_execution.contracts import (
    ClaimRecord,
    EvidenceRecord,
    SourceRecord,
    ValidatorRecord,
)
from backend.governed_execution.quality import calculate_confidence


def _evidence(*, quality: float | None = 0.8) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id="11111111-1111-5111-8111-111111111111",
        source_id="control-manual",
        citation_label="S1",
        text="The control requires encryption at rest.",
        source=SourceRecord(
            source_id="control-manual",
            source_type="document",
            origin="owner-upload",
            title="Control Manual",
            author_publisher="Security Team",
            captured_at="2026-07-01T00:00:00+00:00",
            effective_at="2026-07-01T00:00:00+00:00",
            permissions={"scope": "owner"},
            transformation_chain=[{"operation": "chunk", "version": "1"}],
            embedding_revision="embed-v1",
        ),
        quality_score=quality,
        freshness_score=0.5,
        provenance_completeness=1.0,
    )


def test_confidence_formula_uses_named_measured_components():
    evidence = _evidence()
    claim = ClaimRecord(
        claim_id="claim-1",
        text="The control requires encryption at rest [S1].",
        evidence_ids=[evidence.evidence_id],
        status="supported",
    )
    validator = ValidatorRecord(
        validator_id="validator-1",
        validator_type="claim_support",
        version="claim-support.v1",
        status="passed",
    )

    measurement = calculate_confidence([claim], [evidence], [validator])

    assert measurement.formula_version == "dle-confidence.v1"
    assert measurement.value == 0.91
    assert measurement.missing_components == []
    assert measurement.components == {
        "claim_support": 1.0,
        "claim_consistency": 1.0,
        "source_quality": 0.8,
        "provenance_completeness": 1.0,
        "freshness": 0.5,
        "validator_pass_rate": 1.0,
    }


def test_confidence_is_not_measured_when_required_component_is_missing():
    evidence = _evidence(quality=None)
    claim = ClaimRecord(
        claim_id="claim-1",
        text="The control requires encryption at rest [S1].",
        evidence_ids=[evidence.evidence_id],
        status="supported",
    )

    measurement = calculate_confidence([claim], [evidence], [])

    assert measurement.value is None
    assert "source_quality" in measurement.missing_components
    assert "validator_pass_rate" in measurement.missing_components
    assert measurement.status == "not_measured"
