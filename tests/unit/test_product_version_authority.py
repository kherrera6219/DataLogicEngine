from __future__ import annotations

import json

import pytest

from backend.product_version import (
    CONTRACT_VERSIONS,
    PRODUCT_VERSION,
    VERSION_AUTHORITY_SCHEMA,
    load_version_authority,
)
from scripts import verify_product_versions


def test_checked_in_version_authority_is_valid_and_complete():
    payload = load_version_authority()

    assert payload["schema_version"] == VERSION_AUTHORITY_SCHEMA
    assert PRODUCT_VERSION == "4.4.2"
    assert CONTRACT_VERSIONS["data_plane_schema"] == "b2c3d4e5f6a7"
    assert payload["upgrade"]["supported_product_sources"] == [
        "0.1.1",
        "4.3.0",
        "4.4.0",
        "4.4.1",
    ]


def test_invalid_version_authority_fails_closed(tmp_path):
    authority = tmp_path / "product-versions.json"
    authority.write_text(json.dumps({"schema_version": VERSION_AUTHORITY_SCHEMA}), encoding="utf-8")

    with pytest.raises(RuntimeError, match="product_version_authority_incomplete"):
        load_version_authority(authority)


def test_release_facing_versions_match_authority():
    checks = verify_product_versions.collect_checks()

    assert checks
    assert all(check.passed for check in checks), [check for check in checks if not check.passed]
