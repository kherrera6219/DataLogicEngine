import hashlib

from scripts.generate_release_content_inventory import inventory_tree


def test_inventory_tree_is_path_order_deterministic(tmp_path):
    (tmp_path / "z.txt").write_bytes(b"z")
    (tmp_path / "a.txt").write_bytes(b"a")

    first = inventory_tree("payload", tmp_path)
    second = inventory_tree("payload", tmp_path)

    assert [item["path"] for item in first["files"]] == ["a.txt", "z.txt"]
    assert first["normalized_sha256"] == second["normalized_sha256"]


def test_inventory_hashes_file_contents(tmp_path):
    artifact = tmp_path / "artifact.exe"
    artifact.write_bytes(b"artifact")

    inventory = inventory_tree("installer", artifact)

    assert inventory["files"][0]["sha256"] == hashlib.sha256(b"artifact").hexdigest()


def test_inventory_reports_missing_root(tmp_path):
    inventory = inventory_tree("missing", tmp_path / "absent")

    assert inventory["present"] is False
    assert inventory["normalized_sha256"] is None
