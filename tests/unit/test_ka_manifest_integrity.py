"""KA manifest integrity helper for client/server parity."""

from __future__ import annotations

import hashlib

from backend.knowledge_algorithms.manifest import load_manifest
from scripts.build_ka_runtime_manifest import DEFAULT_OUTPUT_PATH, SDK_OUTPUT_PATH


def test_manifest_integrity_shape():
    from backend.routes import ka_routes

    # Use private helper; exercises live controller when available.
    data = ka_routes._manifest_integrity()
    manifest = load_manifest()
    expected_sha256 = hashlib.sha256(DEFAULT_OUTPUT_PATH.read_bytes()).hexdigest()

    assert data == {
        "manifest_version": manifest.manifest_version,
        "sha256": expected_sha256,
        "source": DEFAULT_OUTPUT_PATH.name,
        "capability_count": 213,
    }
    assert SDK_OUTPUT_PATH.read_bytes() == DEFAULT_OUTPUT_PATH.read_bytes()
