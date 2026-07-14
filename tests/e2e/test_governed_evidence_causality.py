from backend.governed_execution.contracts import EvidenceRecord, SourceRecord
from backend.governed_execution.validation import validate_output


class _Governance:
    @staticmethod
    def apply_output_controls(answer: str):
        return answer, "public", []


def _evidence(*, relationship: str | None = None) -> EvidenceRecord:
    return EvidenceRecord(
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
            permissions={"scope": "owner"},
            transformation_chain=[],
        ),
        metadata={"claim_relationship": relationship} if relationship else {},
    )


def test_claim_citation_resolves_to_trace_bound_persistable_evidence():
    evidence = _evidence()
    evidence.bind_to_trace("00000000-0000-4000-8000-000000000001")

    result = validate_output(
        "The control requires encryption at rest [S1].",
        [evidence],
        mode="enhanced",
        governance_engine=_Governance(),
    )

    claim = result["claims"][0]
    citation = result["citations"][0]
    assert claim.status == "supported"
    assert claim.answer_span_start == 0
    assert claim.answer_span_end == len(result["answer"])
    assert claim.evidence_ids == [evidence.evidence_id]
    assert citation.evidence_id == evidence.evidence_id
    assert citation.source_id == evidence.source_id


def test_unknown_or_contradicting_evidence_never_becomes_supported():
    evidence = _evidence(relationship="contradicts")
    evidence.bind_to_trace("00000000-0000-4000-8000-000000000002")

    contradicted = validate_output(
        "The control requires encryption at rest [S1].",
        [evidence],
        mode="enhanced",
        governance_engine=_Governance(),
    )
    unknown = validate_output(
        "The control requires encryption at rest [S9].",
        [evidence],
        mode="enhanced",
        governance_engine=_Governance(),
    )

    assert contradicted["claims"][0].status == "contradicted"
    assert unknown["ok"] is False
    assert unknown["claims"][0].status == "insufficient"
