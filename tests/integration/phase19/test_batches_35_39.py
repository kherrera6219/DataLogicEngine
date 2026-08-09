"""CP19-K Batches 35-39 owner-path and effect-receipt proofs."""

from __future__ import annotations

import pytest

from backend.governed_execution.extended_subsystems import (
    ExtendedSubsystemCoordinator,
    ExtendedSubsystemError,
)
from backend.governed_execution.knowledge_lifecycle import KnowledgeLifecycleCoordinator
from tests.knowledge_algorithms.test_phase19_per_ka_semantics import (
    _batch_35_39_payloads,
)


_PURE_OWNER_OPERATION = {
    **{
        canonical_id: "inference_mapping"
        for canonical_id in ["KA-041", "KA-043", "KA-044", "KA-049"]
    },
    **{
        canonical_id: "signal_analysis"
        for canonical_id in ["KA-039", "KA-045", "KA-046", "KA-047", "KA-165", "KA-167"]
    },
    **{
        canonical_id: "language_identity_explanation"
        for canonical_id in [
            "KA-048",
            "KA-050",
            "KA-161",
            "KA-162",
            "KA-163",
            "KA-168",
            "KA-178",
        ]
    },
}


def _assert_pure_owner(canonical_id: str) -> dict:
    execution = KnowledgeLifecycleCoordinator(
        workflow_phase="cp19k"
    ).execute_operation_sync(
        owner="truthcore_l1_l5",
        operation=_PURE_OWNER_OPERATION[canonical_id],
        requested_ids=[canonical_id],
        ka_inputs=_batch_35_39_payloads(),
        request_id=f"batch-35-39-{canonical_id}",
        run_id=f"batch-35-39-run-{canonical_id}",
        max_effects=0,
        principal_id="truthcore-owner",
        service_capabilities={"governed_execution_service"},
    )
    result = execution.results[canonical_id]
    assert result["effects"] == []
    assert execution.report.status.value == "succeeded"
    return result["output"]


def _research_owner() -> dict:
    ledger: list[dict] = []
    coordinator = ExtendedSubsystemCoordinator()
    result = coordinator.execute_external_research(
        request_id="batch-38-research",
        principal_id="owner-1",
        sub_question="What evidence supports the control?",
        allowed_domains=["nist.gov"],
        maximum_sources=2,
        timebox_seconds=60,
        connector_id="research-provider",
        authentication_verified=True,
        policy_approved=True,
        rate_limit_allowed=True,
        connector_approved=True,
        human_approved=True,
        connector_call=lambda request: {
            "status": "completed",
            "request_id": request["connector_id"],
            "citations": [{"domain": "nist.gov", "reference": "NIST control evidence"}],
        },
        record_receipt=lambda receipt: ledger.append(receipt) or "research-ledger-1",
    )
    assert result["receipt"].status == "applied"
    assert result["ledger_record_id"] == "research-ledger-1"
    assert len(ledger) == 1
    return coordinator.execution_outputs(result["execution"])


def _delivery_owner() -> dict:
    applied: list[dict] = []
    ledger: list[dict] = []

    def deliver(proposal: dict) -> dict:
        applied.append(proposal)
        return {
            "status": "enqueued",
            "record_id": f"delivery-record-{len(applied)}",
            "proposal_id": proposal["effect_id"],
        }

    coordinator = ExtendedSubsystemCoordinator()
    result = coordinator.execute_delivery_boundary(
        request_id="batch-39-delivery",
        principal_id="owner-1",
        ka_inputs=_batch_35_39_payloads(),
        delivery_call=deliver,
        record_receipt=lambda receipt: (
            ledger.append(receipt) or f"ledger-{len(ledger)}"
        ),
    )
    assert len(result["applied"]) == 5
    assert len(applied) == len(ledger) == 5
    assert all(row["receipt"].status == "applied" for row in result["applied"])
    return coordinator.execution_outputs(result["execution"])


def test_ka_041_owning_path():
    assert _assert_pure_owner("KA-041")["candidate_only"] is True


def test_ka_043_owning_path():
    assert _assert_pure_owner("KA-043")["causal_claim_established"] is False


def test_ka_044_owning_path():
    assert _assert_pure_owner("KA-044")["transfer_applied"] is False


def test_ka_049_owning_path():
    assert _assert_pure_owner("KA-049")["relations_persisted"] is False


def test_ka_039_owning_path():
    assert _assert_pure_owner("KA-039")["measurement_status"] == "measured"


def test_ka_045_owning_path():
    assert _assert_pure_owner("KA-045")["pattern_count"] > 0


def test_ka_046_owning_path():
    assert _assert_pure_owner("KA-046")["trend"] == "upward"


def test_ka_047_owning_path():
    assert _assert_pure_owner("KA-047")["sentiment"] == "positive"


def test_ka_165_owning_path():
    assert _assert_pure_owner("KA-165")["method"] == "hinted_term_frequency"


def test_ka_167_owning_path():
    assert _assert_pure_owner("KA-167")["method"] == "tf_idf"


def test_ka_048_owning_path():
    assert _assert_pure_owner("KA-048")["entity_count"] == 2


def test_ka_050_owning_path():
    assert _assert_pure_owner("KA-050")["source_only"] is True


def test_ka_161_owning_path():
    assert _assert_pure_owner("KA-161")["provider_called"] is False


def test_ka_162_owning_path():
    assert _assert_pure_owner("KA-162")["provider_called"] is False


def test_ka_163_owning_path():
    assert _assert_pure_owner("KA-163")["content_generated"] is False


def test_ka_168_owning_path():
    assert _assert_pure_owner("KA-168")["factors_inferred"] == 0


def test_ka_178_owning_path():
    assert _assert_pure_owner("KA-178")["records_merged"] == 0


def test_ka_111_owning_path():
    assert _research_owner()["KA-111"]["forwarded"] is False


def test_ka_1114_owning_path():
    assert _research_owner()["KA-1114"]["network_accessed"] is False


def test_external_research_owner_fails_closed_on_unverified_authentication():
    connector_called = False

    def connector_call(_request: dict) -> dict:
        nonlocal connector_called
        connector_called = True
        return {}

    with pytest.raises(ExtendedSubsystemError, match="Gateway admission blocked"):
        ExtendedSubsystemCoordinator().execute_external_research(
            request_id="blocked-research",
            principal_id="owner-1",
            sub_question="Blocked request",
            allowed_domains=["nist.gov"],
            maximum_sources=1,
            timebox_seconds=30,
            connector_id="research-provider",
            authentication_verified=False,
            policy_approved=True,
            rate_limit_allowed=True,
            connector_approved=True,
            human_approved=True,
            connector_call=connector_call,
            record_receipt=lambda _receipt: "must-not-record",
        )

    assert connector_called is False


def test_ka_093_owning_path():
    assert _delivery_owner()["KA-093"]["delivered"] is False


def test_ka_110_owning_path():
    assert _delivery_owner()["KA-110"]["published"] is False


def test_ka_112_owning_path():
    assert _delivery_owner()["KA-112"]["queued"] is False


def test_ka_114_owning_path():
    assert _delivery_owner()["KA-114"]["claims_shared"] == 0


def test_ka_115_owning_path():
    assert _delivery_owner()["KA-115"]["ingested_count"] == 0
