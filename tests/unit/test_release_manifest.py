import hashlib

from scripts.generate_release_manifest import (
    _artifact_inventory,
    _json,
    _node_runtime_matches,
    _python_lock_versions,
    _python_runtime_matches,
)


def test_artifact_inventory_marks_only_canonical_installer(tmp_path):
    canonical = tmp_path / "DataLogicEngine Setup 1.2.0.exe"
    stale = tmp_path / "DataLogicEngine Setup Latest.exe"
    canonical.write_bytes(b"canonical")
    stale.write_bytes(b"stale")

    inventory = _artifact_inventory(tmp_path, canonical.name)

    assert [row["canonical_version"] for row in inventory["installers"]] == [True, False]
    assert inventory["installers"][0]["sha256"] == hashlib.sha256(b"canonical").hexdigest()


def test_python_lock_versions_extracts_exact_components(tmp_path):
    lock = tmp_path / "requirements.lock"
    lock.write_text(
        "pyinstaller==6.18.0 \\\n+    --hash=sha256:abc\nredis==7.3.0 \\\n+    --hash=sha256:def\n",
        encoding="utf-8",
    )

    versions = _python_lock_versions(lock)

    assert versions["pyinstaller"] == "6.18.0"
    assert versions["redis"] == "7.3.0"




def test_release_runtime_matching_is_exact_to_required_line():
    assert _python_runtime_matches("3.11", "3.11.9")
    assert not _python_runtime_matches("3.11", "3.12.0")
    assert _node_runtime_matches(24, "v24.14.0")
    assert not _node_runtime_matches(24, "v22.22.0")
    assert not _node_runtime_matches(24, None)
def test_json_accepts_windows_powershell_utf8_bom(tmp_path):
    report = tmp_path / "report.json"
    report.write_bytes(b"\xef\xbb\xbf{\"status\": \"pass\"}")

    assert _json(report)["status"] == "pass"
