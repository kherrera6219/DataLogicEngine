import hashlib
import json

from scripts.generate_installer_sbom import compose_installer_sbom
from scripts.generate_service_asset_sbom import build_service_sbom


def test_service_sbom_preserves_candidate_authorization_boundary():
    lock = {
        "status": "engineering_candidates_not_production_approved",
        "production_provisioning_authorized": False,
        "architecture_change_authorized": False,
        "runtime": {
            "name": "podman",
            "version": "5.8.2",
            "windows_x64_msi_sha256": "a" * 64,
            "license": "Apache-2.0",
        },
        "services": {
            "object_store_candidate": {
                "product": "seaweedfs",
                "version": "4.29",
                "image": f"docker.io/chrislusf/seaweedfs@sha256:{'b' * 64}",
                "linux_amd64_digest": f"sha256:{'c' * 64}",
                "license": "Apache-2.0",
                "production_approved": False,
            }
        },
    }

    sbom = build_service_sbom(lock, "1.2.0")

    properties = sbom["components"][1]["properties"]
    assert {item["name"]: item["value"] for item in properties}["dle.productionApproved"] == "false"


def test_installer_sbom_binds_child_sbom_hashes(tmp_path):
    installer = tmp_path / "DataLogicEngine Setup 1.2.0.exe"
    installer.write_bytes(b"installer")
    child = tmp_path / "backend.json"
    child.write_text(json.dumps({"version": 1, "components": [{"name": "a"}]}), encoding="utf-8")

    sbom = compose_installer_sbom(installer, "1.2.0", [("backend", child, json.loads(child.read_text()))])

    assert sbom["metadata"]["component"]["hashes"][0]["content"] == hashlib.sha256(b"installer").hexdigest()
    assert sbom["compositions"][0]["aggregate"] == "complete"
