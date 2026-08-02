"""CP19-G canonical 12-step refinement workflow integration proof."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from backend.governed_execution.contracts import EvidenceRecord
from backend.knowledge_algorithms.controller import get_ka_controller
from tests.governed_execution.test_orchestrator import (
    _RefinementGateway,
    _orchestrator,
    _request,
)

ROOT = Path(__file__).resolve().parents[2]


def _evidence() -> tuple[list[EvidenceRecord], list[str]]:
    return (
        [
            EvidenceRecord(
                source_id="source-alpha",
                citation_label="S1",
                text="alpha evidence",
            )
        ],
        [],
    )


def test_cp19g_manifest_owns_exactly_one_versioned_12_step_registry():
    manifest = get_ka_controller().manifest
    registry = manifest.authority["refinement_workflow"]
    steps = registry["steps"]

    assert manifest.status in {
        "cp19_g_refinement_authority",
        "cp19_h_truth_data_knowledge_authority",
        "cp19_i_extended_subsystem_authority",
        "cp19_j_product_workflow_authority",
    }
    assert manifest.manifest_version in {
        "2026.07.25-cp19g.1",
        "2026.07.25-cp19h.1",
        "2026.07.25-cp19i.1",
        "2026.07.25-cp19j.1",
    }
    assert registry["schema_version"] == "dle.refinement-workflow-registry.v1"
    assert registry["owner"] == "governed_execution_orchestrator"
    assert registry["entry_condition"] == "committed_l9_refine_decision"
    assert registry["max_provider_rewrites"] == 1
    assert registry["provider_subcalls_from_steps"] == 0
    assert registry["effect_application_authorized"] is False
    assert [step["step"] for step in steps] == list(range(1, 13))
    assert len({step["step_id"] for step in steps}) == 12
    assert len({step["name"] for step in steps}) == 12

    entries = list(manifest.entries.values())
    expected_enabled = {
        "cp19_g_refinement_authority": 29,
        "cp19_h_truth_data_knowledge_authority": 89,
        "cp19_i_extended_subsystem_authority": 149,
        "cp19_j_product_workflow_authority": 149,
    }
    assert sum(
        entry.admission.production_enabled for entry in entries
    ) == expected_enabled[manifest.status]
    assert sum(len(entry.contract.dependencies) for entry in entries) == (
        136
        if manifest.status
        in {
            "cp19_h_truth_data_knowledge_authority",
            "cp19_i_extended_subsystem_authority",
            "cp19_j_product_workflow_authority",
        }
        else 131
    )
    for canonical_id in ("KA-003", "KA-005", "KA-011", "KA-025"):
        definition = manifest.entries[canonical_id]
        assert definition.admission.production_enabled is True
        assert definition.admission.classification == "deterministic_heuristic"
        assert definition.contract.status == "cp19_g_production_qualified"


@pytest.mark.asyncio
async def test_cp19g_refinement_accounts_all_steps_and_revalidates_once(
    monkeypatch: pytest.MonkeyPatch,
):
    import backend.governed_execution.orchestrator as module

    monkeypatch.setattr(
        module, "retrieve_evidence", lambda *args, **kwargs: _evidence()
    )
    gateway = _RefinementGateway()
    result = await _orchestrator(gateway).execute(_request())

    assert result.ok is True
    assert result.status == "completed"
    assert result.convergence is not None
    assert result.convergence.action == "finalize"
    assert gateway.provider_calls == 2
    assert len(gateway.provider_messages) == 2
    assert "committed canonical 12-step refinement" in str(
        gateway.provider_messages[1][-1]["content"]
    )

    refinement = result.metadata["reasoning_state"]["refinement"]
    assert refinement["status"] == "completed"
    assert refinement["step_count"] == 12
    assert refinement["provider_subcalls_used"] == 0
    assert refinement["max_provider_rewrites"] == 1
    assert refinement["rewrite_authorized"] is True
    assert refinement["step_status_counts"] == {
        "executed": 10,
        "skipped": 2,
        "blocked": 0,
        "failed": 0,
    }
    assert [step["step"] for step in refinement["steps"]] == list(range(1, 13))
    by_id = {step["step_id"]: step for step in refinement["steps"]}
    assert by_id["structured_decomposition"]["reused_ka_ids"] == ["KA-001"]
    assert by_id["alternative_branches"]["status"] == "skipped"
    assert by_id["missing_information"]["executed_ka_ids"] == ["KA-003"]
    assert set(by_id["deep_causal_analytical_review"]["executed_ka_ids"]) == {
        "KA-011",
        "KA-025",
    }
    assert set(by_id["semantic_intent_alignment"]["executed_ka_ids"]) == {
        "KA-004",
        "KA-005",
    }
    assert by_id["authorized_external_validation"]["status"] == "skipped"
    proposal = by_id["memory_lifecycle_proposal"]["effects"][0]
    assert proposal["applied"] is False
    assert proposal["receipt"] is None

    post_candidate = [
        (layer["layer_id"], layer["iteration"])
        for layer in result.metadata["reasoning_state"]["layers"]
        if layer["layer_id"] in {"L6", "L7", "L8", "L9"}
    ]
    assert post_candidate == [
        ("L6", 0),
        ("L7", 0),
        ("L8", 0),
        ("L9", 0),
        ("L6", 1),
        ("L7", 1),
        ("L8", 1),
        ("L9", 1),
    ]
    stage = next(item for item in result.stages if item.name == "refinement_1")
    assert stage.metrics["provider_rewrites"] == 1
    assert stage.metrics["provider_subcalls_used"] == 0
    assert stage.metrics["step_count"] == 12


@pytest.mark.asyncio
async def test_cp19g_required_step_failure_blocks_before_rewrite(
    monkeypatch: pytest.MonkeyPatch,
):
    import backend.governed_execution.orchestrator as module

    monkeypatch.setattr(
        module, "retrieve_evidence", lambda *args, **kwargs: _evidence()
    )
    gateway = _RefinementGateway()
    orchestrator = _orchestrator(gateway)
    original_invoke = orchestrator.refinement_workflow.ka_controller._invoke

    def injected_failure(definition: Any, input_data: dict[str, Any]) -> Any:
        if definition.canonical_id == "KA-003":
            return {"success": False, "status": "injected_gap_failure"}
        return original_invoke(definition, input_data)

    monkeypatch.setattr(
        orchestrator.refinement_workflow.ka_controller,
        "_invoke",
        injected_failure,
    )
    result = await orchestrator.execute(_request())

    assert result.ok is False
    assert result.failure is not None
    assert result.failure.code == "REFINEMENT_WORKFLOW_BLOCKED"
    assert gateway.provider_calls == 1
    refinement = result.metadata["reasoning_state"]["refinement"]
    assert refinement["step_count"] == 12
    assert refinement["blocked_by_step"] == "missing_information"
    by_id = {step["step_id"]: step for step in refinement["steps"]}
    assert by_id["missing_information"]["status"] == "blocked"
    assert by_id["input_source_evidence_validation"]["status"] == "skipped"
    assert by_id["memory_lifecycle_proposal"]["effects"] == []


def test_cp19g_legacy_refinement_variants_are_not_product_entrypoints():
    variants = (
        "backend.truth_engine.truth_core.refinement_orchestrator",
        "core.system.refinement_orchestrator",
        "core.simulation.refinement_workflow",
        "core.simulation.refinement_orchestrator",
        "core.persona.quad.mathematical_framework.refinement",
    )
    for module_name in variants:
        module = __import__(module_name, fromlist=["PRODUCTION_ENTRYPOINT"])
        assert module.PRODUCTION_ENTRYPOINT is False
        assert module.WORKFLOW_DISPOSITION.endswith(
            ("reference", "demonstration_reference")
        )

    assembly_source = (
        ROOT / "backend" / "governed_execution" / "orchestrator.py"
    ).read_text(encoding="utf-8")
    assert "truth_core.refinement_orchestrator" not in assembly_source
    assert "core.simulation.refinement" not in assembly_source
    assert "core.system.refinement" not in assembly_source
