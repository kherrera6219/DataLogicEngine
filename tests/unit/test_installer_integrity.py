import hashlib
import json

from scripts.verify_installer_integrity import verify_installers


def _write_authority(tmp_path, version="1.2.0"):
    authority = tmp_path / "config" / "product-versions.json"
    authority.parent.mkdir(parents=True)
    authority.write_text(json.dumps({"product": {"version": version}}), encoding="utf-8")


def _write_installer(tmp_path, name):
    artifact = tmp_path / name
    artifact.write_bytes(b"installer")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    (tmp_path / f"{name}.sha256").write_text(
        f"{digest}  {name}\n",
        encoding="ascii",
    )
    return artifact


def test_canonical_versioned_installer_passes_integrity(tmp_path):
    _write_authority(tmp_path)
    _write_installer(tmp_path, "DataLogicEngine Setup 1.2.0.exe")

    issues, report = verify_installers(tmp_path, require_artifacts=True)

    assert not any(issue.severity == "error" for issue in issues)
    assert report["expected_installer"] == "DataLogicEngine Setup 1.2.0.exe"


def test_latest_alias_is_rejected_as_stale_artifact(tmp_path):
    _write_authority(tmp_path)
    _write_installer(tmp_path, "DataLogicEngine Setup Latest.exe")

    issues, _ = verify_installers(tmp_path, require_artifacts=True)

    assert any(issue.check == "artifact_version" for issue in issues)
    assert any(issue.check == "canonical_artifact_presence" for issue in issues)


def test_missing_version_authority_fails_closed(tmp_path):
    issues, report = verify_installers(tmp_path, require_artifacts=False)

    assert any(issue.check == "version_authority" for issue in issues)
    assert report["expected_installer"] is None
