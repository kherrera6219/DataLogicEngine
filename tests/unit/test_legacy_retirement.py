import json

from scripts.verify_legacy_retirement import inspect_retirement


def _repo(tmp_path, builder):
    files = {
        "config/legacy-retirement.json": json.dumps(
            {"schema_version": "dle.legacy-retirement.v1"}
        ),
        "frontend/electron-builder.yml": builder,
        "frontend/package.json": "{}",
        ".github/workflows/release-installer-signing.yml": "name: release",
    }
    for name, content in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def test_retired_scripts_cannot_be_bundled(tmp_path):
    _repo(
        tmp_path,
        'artifactName: "DataLogicEngine Setup ${version}.${ext}"\nfrom: ../scripts/windows\n',
    )

    findings = inspect_retirement(tmp_path)

    assert any(finding.level == "ERROR" and finding.check == "scripts/windows bundle" for finding in findings)


def test_versioned_nsis_only_policy_passes(tmp_path):
    _repo(tmp_path, 'artifactName: "DataLogicEngine Setup ${version}.${ext}"\n')

    findings = inspect_retirement(tmp_path)

    assert not any(finding.level == "ERROR" for finding in findings)
