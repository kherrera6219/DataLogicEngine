import json
from pathlib import Path

from scripts.verify_release_payload import REQUIRED_BACKEND_FILES, verify_payload


def _write_required_payload(root):
    for relative in REQUIRED_BACKEND_FILES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"runtime")


def test_runtime_only_payload_passes(tmp_path):
    backend = tmp_path / "backend"
    electron = tmp_path / "dist-electron"
    _write_required_payload(backend)
    electron.mkdir()
    (electron / "main.js").write_text("runtime", encoding="utf-8")

    result = verify_payload(backend, electron)

    assert result["status"] == "pass"
    assert result["summary"]["issue_count"] == 0


def test_source_tests_and_compiled_electron_tests_fail(tmp_path):
    backend = tmp_path / "backend"
    electron = tmp_path / "dist-electron"
    _write_required_payload(backend)
    leaked_source = backend / "_internal" / "backend" / "routes.py"
    leaked_source.parent.mkdir(parents=True, exist_ok=True)
    leaked_source.write_text("source", encoding="utf-8")
    leaked_test = backend / "_internal" / "chromadb" / "tests" / "test_api.py"
    leaked_test.parent.mkdir(parents=True, exist_ok=True)
    leaked_test.write_text("test", encoding="utf-8")
    electron.mkdir()
    (electron / "lifecycle.test.js").write_text("test", encoding="utf-8")

    result = verify_payload(backend, electron)

    assert result["status"] == "fail"
    assert {issue["check"] for issue in result["issues"]} == {
        "application_source",
        "development_tree",
        "electron_test_bundle",
    }


def test_release_workflow_separates_candidate_builds_from_production_signing():
    workflow = (Path(__file__).resolve().parents[2] / ".github" / "workflows" / "release-installer-signing.yml").read_text(
        encoding="utf-8"
    )

    assert "release_mode:" in workflow
    assert "python scripts/verify_release_payload.py" in workflow
    assert "if: needs.build-installer.outputs.release_mode == 'production'" in workflow
    assert "if ($env:DLE_RELEASE_MODE -eq 'production')" in workflow
    assert "config/release-channel.json" in workflow


def test_backend_spec_does_not_force_unused_local_ml_stack_into_payload():
    spec = (Path(__file__).resolve().parents[2] / "backend.spec").read_text(encoding="utf-8")

    assert "collect_dynamic_libs('onnxruntime')" not in spec
    assert "collect_submodules('tokenizers'" not in spec
    assert "'sentence_transformers'," in spec
    assert "'transformers'," in spec
    assert "'torch'," in spec
    assert "'onnxruntime'," in spec
    assert "'tokenizers'," in spec


def test_packaged_candidate_uses_only_the_qualification_data_plane_profile():
    root = Path(__file__).resolve().parents[2]
    policy = json.loads((root / "config" / "release-channel.json").read_text(encoding="utf-8"))
    builder = (root / "frontend" / "electron-builder.yml").read_text(encoding="utf-8")
    electron = (root / "frontend" / "electron" / "main.ts").read_text(encoding="utf-8")

    assert policy == {
        "schema_version": "dle.release-channel.v1",
        "channel": "candidate",
        "data_plane_profile": "qualification",
        "production_authorized": False,
    }
    assert "config/release-channel.json" in builder
    assert "DLE_DATA_PLANE_PROFILE: resolveDataPlaneProfile(isDev)" in electron
