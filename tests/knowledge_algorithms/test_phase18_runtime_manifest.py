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


def test_phase18_controller_blocks_unqualified_production_execution():
    result = CanonicalKAController().execute(
        {"ka_id": "KA-002", "mode": "production", "input": {}}
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
