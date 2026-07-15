from scripts.compare_release_content_inventories import compare_inventories


def _inventory(digest):
    return {
        "inventories": [
            {"label": "backend", "normalized_sha256": digest, "file_count": 10}
        ]
    }


def test_identical_normalized_inventories_pass():
    result = compare_inventories(_inventory("a" * 64), _inventory("a" * 64))

    assert result["status"] == "pass"


def test_payload_drift_fails_reproducibility_gate():
    result = compare_inventories(_inventory("a" * 64), _inventory("b" * 64))

    assert result["status"] == "fail"
