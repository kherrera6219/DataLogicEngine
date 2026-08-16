"""Phase 7 tooling and policy docs exist."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_ci_quality_and_csp_docs_exist():
    assert (ROOT / "docs" / "CI_QUALITY_POLICY.md").is_file()
    assert (ROOT / "docs" / "DESKTOP_CSP.md").is_file()


def test_packaging_resources_script_exists():
    script = ROOT / "scripts" / "windows" / "verify_packaging_resources.ps1"
    assert script.is_file()
    text = script.read_text(encoding="utf-8")
    assert "DataLogic_Backend.exe" in text
    assert "release-trust-policy.json" in text


def test_packaging_smoke_can_require_package_owned_backend_readiness():
    script = ROOT / "scripts" / "windows" / "run_packaging_smoke.ps1"
    text = script.read_text(encoding="utf-8")

    assert "[switch]$RequireBackendReady" in text
    assert 'BackendReadyUri = "http://127.0.0.1:5000/ready"' in text
    assert "Invoke-RestMethod" in text
    assert "backend_ready_owner_verified" in text
    assert "owner_verified_as_launch_descendant" in text
    assert "Portable readiness smoke failed" in text


def test_ci_workflow_has_phase7_guards():
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "scan_orphan_pyc.py --fail-on-orphan" in ci
    assert "verify_route_uniqueness.py" in ci
    assert "verify_packaging_resources.ps1" in ci
    assert "CI_QUALITY_POLICY" in ci or "continue-on-error: true" in ci
