"""CP19-E Layer 9/10 integration and adversarial safety regressions."""

from __future__ import annotations

from pathlib import Path

from backend.knowledge_algorithms.ka_master_controller import (
    KAMasterController,
)
from backend.knowledge_algorithms.manifest import load_manifest

REPO_ROOT = Path(__file__).resolve().parents[2]
L9_IDS = {f"L9-KA-{number:03d}" for number in range(1, 8)}
L10_IDS = {f"L10-KA-{number:03d}" for number in range(1, 8)}


def _output(controller, ka_id, payload):
    return controller.execute_typed(ka_id, payload).require_output()


def test_cp19e_manifest_admits_complete_l9_l10_suites_with_exact_dag():
    manifest = load_manifest()

    assert manifest.status == "cp19_i_extended_subsystem_authority"
    assert L9_IDS | L10_IDS <= set(manifest.authority["production_admission_ids"])
    for ka_id in L9_IDS | L10_IDS:
        definition = manifest.entries[ka_id]
        assert definition.admission.production_enabled is True
        assert definition.admission.deterministic is True
        assert definition.contract.status == ("cp19_e_production_qualified")
    assert manifest.entries["L9-KA-006"].contract.dependencies == [
        "L9-KA-001",
        "L9-KA-002",
        "L9-KA-003",
        "L9-KA-004",
    ]
    assert manifest.entries["L9-KA-005"].contract.dependencies == ["L9-KA-006"]
    assert manifest.entries["L9-KA-007"].contract.dependencies == [
        "L9-KA-005",
        "L9-KA-006",
    ]
    assert manifest.entries["L10-KA-007"].contract.dependencies == [
        "L10-KA-004",
        "L10-KA-006",
    ]
    assert set(manifest.entries["L10-KA-005"].contract.dependencies) == (
        L10_IDS - {"L10-KA-005"}
    )


def test_cp19e_retained_controllers_have_no_identity_drift_or_manual_trace():
    emergence_source = (
        REPO_ROOT
        / "backend"
        / "truth_engine"
        / "truth_core"
        / "emergence_controller.py"
    ).read_text(encoding="utf-8")

    assert '"KA-108"' not in emergence_source
    assert '"KA-109"' not in emergence_source
    assert '"KA-079"' not in emergence_source
    assert '"KA-058"' not in emergence_source
    assert '"KA-059"' not in emergence_source
    assert 'kas_invoked.append("L10-KA-006")' not in emergence_source
    assert '"KA-1108"' in emergence_source
    assert '"KA-1109"' in emergence_source
    assert '"KA-1079"' in emergence_source


def test_cp19e_pii_redaction_never_returns_clear_text_findings():
    controller = KAMasterController({})
    secret = "kevin@example.com"
    result = _output(
        controller,
        "L10-KA-003",
        {"content": f"Contact {secret} or 555-555-1212."},
    )

    assert result["redactions_found"] == 2
    assert secret not in str(result)
    assert result["sensitive_values_returned"] is False
    assert result["redactions"] == [
        {"type": "EMAIL", "count": 1},
        {"type": "PHONE", "count": 1},
    ]


def test_cp19e_low_confidence_and_containment_bypass_are_denied():
    controller = KAMasterController({})
    trust = _output(
        controller,
        "L10-KA-006",
        {"confidence": 0.70, "threshold": 0.95},
    )
    escalation = _output(
        controller,
        "L10-KA-007",
        {
            "request_id": "low-confidence",
            "risk_domain": "standard",
            "confidence": trust["decayed_confidence"],
        },
    )
    containment = _output(
        controller,
        "L10-KA-005",
        {
            "final_action": "finalize",
            "dependency_results": {
                "L10-KA-002": {"level": "none"},
                "L10-KA-003": {"redactions_found": 0},
                "L10-KA-004": {"violations": []},
                "L10-KA-006": trust,
                "L10-KA-007": escalation,
            },
        },
    )

    assert trust["passed"] is False
    assert escalation["escalation_required"] is True
    assert containment["release_authorized"] is False
    assert containment["decision"] == "ESCALATE"


def test_cp19e_recursion_exhaustion_never_force_finalizes():
    controller = KAMasterController({})
    result = _output(
        controller,
        "L9-KA-007",
        {
            "iteration": 2,
            "max_iterations": 2,
            "dependency_results": {"L9-KA-005": {"trigger_refinement": True}},
        },
    )

    assert result["continue"] is False
    assert result["exhausted"] is True
    assert result["terminal_policy"] == ("block_or_abstain_never_force_finalize")


def test_cp19e_unauthorized_promotion_and_false_receipts_are_impossible():
    controller = KAMasterController({})
    promotion = _output(
        controller,
        "KA-1079",
        {
            "knowledge_id": "candidate-1",
            "validation_status": "unvalidated",
            "confidence": 0.99,
            "evidence_count": 5,
            "citation_count": 5,
            "contradiction_count": 0,
            "provenance_complete": True,
            "risk_class": "medium",
        },
    )
    escalation = _output(
        controller,
        "L10-KA-007",
        {
            "request_id": "effect-check",
            "risk_domain": "legal",
            "confidence": 0.99,
            "consequential_decision": True,
        },
    )

    assert promotion["decision"] == "reject"
    assert promotion["promotion_applied"] is False
    assert escalation["escalation_required"] is True
    assert escalation["reviews_dispatched"] == 0
    assert escalation["review_proposal"]["applied"] is False
