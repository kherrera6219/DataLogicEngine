from __future__ import annotations

from datetime import UTC, datetime, timedelta

from backend.knowledge_algorithms.contracts import (
    KAExecutionMode,
    KAExecutionRequest,
    KAExecutionState,
    KAFailureCode,
)
from backend.knowledge_algorithms.controller import CanonicalKAController
from backend.knowledge_algorithms.manifest import load_manifest
from scripts.build_ka_runtime_manifest import (
    DEFAULT_OUTPUT_PATH,
    SDK_OUTPUT_PATH,
    TYPESCRIPT_OUTPUT_PATH,
    build_manifest,
    json_text,
    typescript_text,
)


def controller_with_unavailable_implementation(
    ka_id: str = "KA-1039",
) -> CanonicalKAController:
    manifest = load_manifest().model_copy(deep=True)
    definition = manifest.entries[ka_id]
    definition.implementation = definition.implementation.model_copy(
        update={
            "status": "implementation_required",
            "source": None,
            "entrypoint": None,
        }
    )
    return CanonicalKAController(manifest)


def test_phase18_runtime_manifest_is_current_and_deduplicated():
    manifest = load_manifest()

    assert manifest.capability_count == 213
    assert len(manifest.entries) == 213
    assert DEFAULT_OUTPUT_PATH.read_text(encoding="utf-8") == json_text(
        build_manifest()
    )
    assert SDK_OUTPUT_PATH.read_text(encoding="utf-8") == json_text(build_manifest())
    assert TYPESCRIPT_OUTPUT_PATH.read_text(encoding="utf-8") == typescript_text(
        build_manifest()
    )
    assert "KA-133" not in manifest.entries
    assert (
        manifest.resolve_id("generated-v1:KA-133", allow_scoped_alias=True) == "KA-1101"
    )


def test_runtime_manifest_has_complete_production_contract_metadata():
    manifest = load_manifest()
    production_entries = [
        definition
        for definition in manifest.entries.values()
        if definition.admission.production_enabled
    ]

    assert len(production_entries) == 211
    for definition in production_entries:
        assert definition.purpose, definition.canonical_id
        assert definition.contract.categories, definition.canonical_id
        assert definition.contract.risk_classes, definition.canonical_id
        assert definition.contract.subsystems, definition.canonical_id
        assert definition.contract.layers, definition.canonical_id


def test_al10_metadata_uses_approved_contract_authorities():
    manifest = load_manifest()

    complexity = manifest.entries["KA-036"]
    assert complexity.purpose == (
        "bounded complexity estimation from supplied request signals."
    )
    assert complexity.contract.categories == ["Routing"]
    assert complexity.contract.risk_classes == ["Low"]
    assert complexity.contract.subsystems == ["governed_request_dmrf"]
    assert complexity.contract.layers == ["L1"]

    ingestion = manifest.entries["KA-071"]
    assert ingestion.contract.categories == ["Lifecycle"]
    assert ingestion.contract.risk_classes == ["High"]
    assert ingestion.contract.subsystems == ["ingestion"]
    assert ingestion.contract.layers == ["ingestion"]

    policy = manifest.entries["KA-177"]
    assert policy.contract.categories == ["General"]
    assert policy.contract.risk_classes == ["Critical"]
    assert policy.contract.subsystems == ["truthgate"]
    assert policy.contract.layers == ["L8"]

    assert manifest.entries["KA-025"].contract.performance_budget_ms == 1_000

    assert manifest.authority["contract_metadata_policy"] == {
        "checkpoint": "AL-10",
        "purpose_source": "implementation_module_docstring",
        "category_source": "cp19_a_primary_owner",
        "risk_source": "declared_effect_class_and_cp19_a_primary_owner",
        "subsystem_source": "cp19_a_primary_owner",
        "layer_source": "cp19_a_primary_owner_stage_scope",
    }


def test_phase18_manifest_normalizes_all_supported_id_families():
    manifest = load_manifest()

    assert manifest.resolve_id("1") == "KA-001"
    assert manifest.resolve_id("ka-1") == "KA-001"
    assert manifest.resolve_id("L9-KA-1") == "L9-KA-001"
    assert manifest.resolve_id("l10-ka-6") == "L10-KA-006"
    assert manifest.resolve_id("ka-master") == "KA-Master"


def test_phase18_controller_executes_existing_module_through_typed_contract():
    controller = CanonicalKAController()
    request = KAExecutionRequest(
        ka_id="KA-004",
        input={"query": "  verify me  "},
        mode=KAExecutionMode.PRODUCTION,
    )

    result = controller.execute(request)

    assert result.success is True
    assert result.state == KAExecutionState.SUCCEEDED
    assert result.canonical_id == "KA-004"
    assert result.manifest_version == controller.manifest.manifest_version
    assert result.request_id == request.context.request_id
    assert result.run_id == request.context.run_id
    assert result.trace_id
    assert result.duration_ms >= 0
    assert result.output["is_valid"] is True


def test_phase18_controller_executes_layer9_class_adapter():
    result = CanonicalKAController().execute(
        {
            "ka_id": "L9-KA-001",
            "mode": "evaluation",
            "input": {"trace": {}, "layers": []},
        }
    )

    assert result.success is True
    assert result.canonical_id == "L9-KA-001"
    assert result.implementation_adapter == "class_execute"
    assert result.output["layers_analyzed"] == 0


def test_phase18_controller_blocks_disabled_production_execution():
    result = CanonicalKAController().execute(
        {"ka_id": "KA-033", "mode": "production", "input": {}}
    )

    assert result.success is False
    assert result.state == KAExecutionState.BLOCKED
    assert result.error is not None
    assert result.error.code == KAFailureCode.NOT_PRODUCTION_QUALIFIED


def test_phase18_controller_reports_missing_implementation_without_false_success():
    result = controller_with_unavailable_implementation().execute(
        {"ka_id": "KA-1039", "mode": "evaluation", "input": {}}
    )

    assert result.success is False
    assert result.state == KAExecutionState.UNAVAILABLE
    assert result.error is not None
    assert result.error.code == KAFailureCode.IMPLEMENTATION_UNAVAILABLE


def test_phase18_controller_honors_cancellation_and_deadline():
    controller = CanonicalKAController()
    cancelled = controller.execute(
        {
            "ka_id": "KA-004",
            "mode": "production",
            "input": {"query": "hello"},
            "context": {"cancellation_requested": True},
        }
    )
    expired = controller.execute(
        {
            "ka_id": "KA-004",
            "mode": "production",
            "input": {"query": "hello"},
            "context": {
                "deadline_at": (datetime.now(UTC) - timedelta(seconds=1)).isoformat()
            },
        }
    )

    assert cancelled.state == KAExecutionState.CANCELLED
    assert cancelled.error is not None
    assert cancelled.error.code == KAFailureCode.CANCELLED
    assert expired.state == KAExecutionState.TIMED_OUT
    assert expired.error is not None
    assert expired.error.code == KAFailureCode.DEADLINE_EXCEEDED
