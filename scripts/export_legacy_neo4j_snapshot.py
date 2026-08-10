"""Export the expected legacy DataLogicEngine Neo4j container for adoption."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import dotenv_values  # noqa: E402
from neo4j import GraphDatabase  # noqa: E402

from backend.security.windows_acl import ensure_restricted_user_acl  # noqa: E402
from backend.storage.legacy_neo4j_adoption import SNAPSHOT_SCHEMA_VERSION  # noqa: E402


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--container", default="ukg-neo4j")
    return parser.parse_args()


def _verify_legacy_container(name: str) -> None:
    result = subprocess.run(
        ["docker", "inspect", name],
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    if result.returncode != 0:
        raise RuntimeError("legacy_neo4j_container_missing")
    payload = json.loads(result.stdout)[0]
    labels = payload.get("Config", {}).get("Labels") or {}
    if labels.get("com.docker.compose.project") != "datalogicengine":
        raise RuntimeError("legacy_neo4j_container_identity_mismatch")
    if labels.get("com.docker.compose.service") != "neo4j":
        raise RuntimeError("legacy_neo4j_container_identity_mismatch")


def main() -> int:
    args = _parse_args()
    _verify_legacy_container(args.container)
    values = {
        str(key or "").lstrip("\ufeff"): value
        for key, value in dotenv_values(args.env_file).items()
    }
    password = values.get("NEO4J_PASSWORD")
    if not password:
        raise RuntimeError("legacy_neo4j_credential_missing")
    port = values.get("NEO4J_LOCAL_PORT") or "7690"
    driver = GraphDatabase.driver(
        f"bolt://127.0.0.1:{port}",
        auth=(values.get("NEO4J_USER") or "neo4j", password),
        connection_timeout=5,
    )
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            nodes = session.run(
                "MATCH (n) RETURN elementId(n) AS source_id, labels(n) AS labels, "
                "properties(n) AS properties ORDER BY source_id"
            ).data()
            relationships = session.run(
                "MATCH (s)-[r]->(t) RETURN elementId(r) AS source_id, "
                "elementId(s) AS start_source_id, elementId(t) AS end_source_id, "
                "type(r) AS type, properties(r) AS properties ORDER BY source_id"
            ).data()
    finally:
        driver.close()
    payload = json.loads(json.dumps({
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "source": "released-datalogicengine-docker-neo4j",
        "created_at": datetime.now(UTC).isoformat(),
        "nodes": nodes,
        "relationships": relationships,
    }, default=str))
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["sha256"] = hashlib.sha256(canonical).hexdigest()
    destination = (
        args.runtime_root.resolve()
        / "recovery"
        / "retained-data"
        / "legacy-neo4j.snapshot.json"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, destination)
    ensure_restricted_user_acl(destination, required=os.name == "nt")
    print(
        json.dumps(
            {
                "status": "verified",
                "node_count": len(nodes),
                "relationship_count": len(relationships),
                "snapshot_sha256": payload["sha256"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
