#!/usr/bin/env python3
"""Hash the current Phase 0 machine-readable evidence artifacts."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PHASE = ROOT / "reports/production-readiness/2026/phase-00"
OUTPUT = PHASE / "artifacts.json"
ARTIFACTS = [
    PHASE / "owner-approval-2026-07-13.md",
    PHASE / "runtime/product-manifest.json",
    PHASE / "runtime/runtime-surfaces.json",
    PHASE / "runtime/ui-controls.json",
    PHASE / "runtime/service-consumers.json",
    PHASE / "runtime/installed-baseline.json",
    PHASE / "runtime/podman-five-service-baseline.json",
    PHASE / "runtime/baseline-metrics.json",
    PHASE / "requirements-traceability.json",
    PHASE / "feature-disposition.json",
    PHASE / "responsibility-approval.json",
    PHASE / "windows-support-matrix.json",
    PHASE / "legal-distribution-authority.json",
    PHASE / "test-results/runtime-precheck.json",
    PHASE / "test-results/lockfiles.json",
    PHASE / "test-results/environment-parity.json",
    PHASE / "test-results/runtime-precheck-python311.json",
    PHASE / "test-results/lockfiles-python311.json",
    PHASE / "test-results/environment-parity-python311.json",
    PHASE / "test-results/secret-scan.json",
]


def main() -> int:
    artifacts = []
    for path in ARTIFACTS:
        if not path.exists():
            raise FileNotFoundError(path)
        data = path.read_bytes()
        artifacts.append(
            {
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    payload = {
        "schema_version": "1.0.0",
        "captured_at": datetime.now(UTC).isoformat(),
        "artifacts": artifacts,
        "installer_artifact": "See runtime/installed-baseline.json; current installer is captured but not signed or production-qualified.",
        "note": "Current-host baseline is captured. Full approved-runtime installed acceptance remains open.",
    }
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} with {len(artifacts)} artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
