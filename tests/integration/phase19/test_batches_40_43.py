"""CP19-K Batches 40-43 owner-path and effect-receipt proofs."""

from __future__ import annotations

import pytest

from backend.governed_execution.extended_subsystems import (
    ExtendedSubsystemCoordinator,
    ExtendedSubsystemError,
)
from tests.knowledge_algorithms.test_phase19_per_ka_semantics import (
    _batch_40_43_payloads,
)


def _effect_handlers() -> tuple[callable, callable, list[dict], list[dict]]:
    applied: list[dict] = []
    ledger: list[dict] = []

    def effect_call(proposal: dict) -> dict:
        applied.append(proposal)
        return {
            "status": "applied",
            "record_id": f"effect-record-{len(applied)}",
            "proposal_id": proposal["effect_id"],
        }

    def record_receipt(receipt: dict) -> str:
        ledger.append(receipt)
        return f"effect-ledger-{len(ledger)}"

    return effect_call, record_receipt, applied, ledger


def _execute_boundary(method_name: str) -> dict:
    effect_call, record_receipt, applied, ledger = _effect_handlers()
    result = getattr(ExtendedSubsystemCoordinator(), method_name)(
        request_id=f"batch-40-43-{method_name}",
        principal_id="operations-owner",
        ka_inputs=_batch_40_43_payloads(),
        effect_call=effect_call,
        record_receipt=record_receipt,
    )
    assert len(result["applied"]) == len(applied) == len(ledger)
    assert all(item["receipt"].status == "applied" for item in result["applied"])
    assert all(item["ledger_record_id"] for item in result["applied"])
    return result


@pytest.fixture(scope="module")
def health_recovery_result() -> dict:
    result = _execute_boundary("execute_health_recovery_boundary")
    assert len(result["applied"]) == 3
    return result


@pytest.fixture(scope="module")
def security_crypto_result() -> dict:
    result = _execute_boundary("execute_security_crypto_boundary")
    assert len(result["applied"]) == 2
    return result


@pytest.fixture(scope="module")
def simulation_resilience_result() -> dict:
    result = _execute_boundary("execute_simulation_resilience_boundary")
    assert len(result["applied"]) == 2
    return result


@pytest.fixture(scope="module")
def topology_evolution_result() -> dict:
    result = _execute_boundary("execute_topology_evolution_boundary")
    assert len(result["applied"]) == 4
    return result


def _receipt_for(result: dict, canonical_id: str) -> dict:
    matches = [
        item for item in result["applied"] if item["canonical_id"] == canonical_id
    ]
    assert len(matches) == 1
    return matches[0]


def test_ka_107_owning_path(health_recovery_result: dict):
    assert health_recovery_result["outputs"]["KA-107"]["recovery_started"] is False
    assert _receipt_for(health_recovery_result, "KA-107")["receipt"].ka_proposal_ids


def test_ka_108_owning_path(health_recovery_result: dict):
    assert health_recovery_result["outputs"]["KA-108"]["backup_created"] is False
    assert _receipt_for(health_recovery_result, "KA-108")["receipt"].ka_proposal_ids


def test_ka_109_owning_path(health_recovery_result: dict):
    output = health_recovery_result["outputs"]["KA-109"]
    assert output["components_polled"] == 0
    assert output["readiness_verified"] is True


def test_ka_1097_owning_path(health_recovery_result: dict):
    assert health_recovery_result["outputs"]["KA-1097"]["settings_applied"] == 0
    assert _receipt_for(health_recovery_result, "KA-1097")["receipt"].ka_proposal_ids


def test_ka_1098_owning_path(health_recovery_result: dict):
    assert health_recovery_result["outputs"]["KA-1098"]["benchmarks_executed"] is False


def test_ka_138_owning_path(health_recovery_result: dict):
    assert health_recovery_result["outputs"]["KA-138"]["actions_applied"] == 0


def test_ka_139_owning_path(security_crypto_result: dict):
    assert (
        security_crypto_result["outputs"]["KA-139"]["adversarial_actions_executed"] == 0
    )


def test_ka_180_owning_path(security_crypto_result: dict):
    assert security_crypto_result["outputs"]["KA-180"]["operations_applied"] == 0
    assert _receipt_for(security_crypto_result, "KA-180")["receipt"].ka_proposal_ids


def test_ka_181_owning_path(security_crypto_result: dict):
    assert security_crypto_result["outputs"]["KA-181"]["actions_applied"] == 0
    assert _receipt_for(security_crypto_result, "KA-181")["receipt"].ka_proposal_ids


def test_ka_183_owning_path(security_crypto_result: dict):
    assert security_crypto_result["outputs"]["KA-183"]["scans_executed"] == 0


def test_ka_1101_owning_path(simulation_resilience_result: dict):
    assert simulation_resilience_result["outputs"]["KA-1101"]["faults_injected"] == 0
    assert _receipt_for(simulation_resilience_result, "KA-1101")[
        "receipt"
    ].ka_proposal_ids


def test_ka_1103_owning_path(simulation_resilience_result: dict):
    assert (
        simulation_resilience_result["outputs"]["KA-1103"]["rollback_applied"] is False
    )
    assert _receipt_for(simulation_resilience_result, "KA-1103")[
        "receipt"
    ].ka_proposal_ids


def test_ka_101_owning_path(topology_evolution_result: dict):
    output = topology_evolution_result["outputs"]["KA-101"]
    assert output["environment_variables_read"] is False
    assert _receipt_for(topology_evolution_result, "KA-101")["receipt"].ka_proposal_ids


def test_ka_102_owning_path(topology_evolution_result: dict):
    assert topology_evolution_result["outputs"]["KA-102"]["injected_count"] == 0
    assert _receipt_for(topology_evolution_result, "KA-102")["receipt"].ka_proposal_ids


def test_ka_103_owning_path(topology_evolution_result: dict):
    assert topology_evolution_result["outputs"]["KA-103"]["mesh_active"] is False
    assert _receipt_for(topology_evolution_result, "KA-103")["receipt"].ka_proposal_ids


def test_ka_104_owning_path(topology_evolution_result: dict):
    assert topology_evolution_result["outputs"]["KA-104"]["routing_applied"] is False


def test_ka_105_owning_path(topology_evolution_result: dict):
    assert topology_evolution_result["outputs"]["KA-105"]["scaling_applied"] is False


def test_ka_1100_owning_path(topology_evolution_result: dict):
    assert topology_evolution_result["outputs"]["KA-1100"]["changes_applied"] == 0
    assert _receipt_for(topology_evolution_result, "KA-1100")["receipt"].ka_proposal_ids


@pytest.mark.parametrize(
    "method_name",
    [
        "execute_health_recovery_boundary",
        "execute_security_crypto_boundary",
        "execute_simulation_resilience_boundary",
        "execute_topology_evolution_boundary",
    ],
)
def test_owner_boundaries_fail_closed_without_durable_receipt(method_name: str):
    effect_call, _record_receipt, _applied, _ledger = _effect_handlers()
    with pytest.raises(
        ExtendedSubsystemError, match="receipt was not durably recorded"
    ):
        getattr(ExtendedSubsystemCoordinator(), method_name)(
            request_id=f"blocked-{method_name}",
            principal_id="operations-owner",
            ka_inputs=_batch_40_43_payloads(),
            effect_call=effect_call,
            record_receipt=lambda _receipt: "",
        )
