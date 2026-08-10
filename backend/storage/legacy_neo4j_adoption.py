"""Verified import of a content-hashed legacy Neo4j recovery snapshot."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


SNAPSHOT_SCHEMA_VERSION = "dle.legacy-neo4j-snapshot.v1"
_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")


class LegacyNeo4jAdoptionError(RuntimeError):
    """Safely reportable legacy graph adoption failure."""


def _canonical_payload(payload: dict[str, Any]) -> bytes:
    unsigned = {key: value for key, value in payload.items() if key != "sha256"}
    return json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load_verified_legacy_neo4j_snapshot(path: str | Path) -> dict[str, Any] | None:
    source = Path(path).resolve()
    if not source.is_file():
        return None
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError) as exc:
        raise LegacyNeo4jAdoptionError("retained_neo4j_snapshot_unreadable") from exc
    if payload.get("schema_version") != SNAPSHOT_SCHEMA_VERSION:
        raise LegacyNeo4jAdoptionError("retained_neo4j_snapshot_schema_invalid")
    expected = hashlib.sha256(_canonical_payload(payload)).hexdigest()
    if payload.get("sha256") != expected:
        raise LegacyNeo4jAdoptionError("retained_neo4j_snapshot_hash_mismatch")
    nodes = payload.get("nodes")
    relationships = payload.get("relationships")
    if not isinstance(nodes, list) or not isinstance(relationships, list):
        raise LegacyNeo4jAdoptionError("retained_neo4j_snapshot_content_invalid")
    return payload


def _identifier(value: Any, kind: str) -> str:
    normalized = str(value or "")
    if not _IDENTIFIER.fullmatch(normalized):
        raise LegacyNeo4jAdoptionError(f"retained_neo4j_{kind}_invalid")
    return normalized


def import_legacy_neo4j_snapshot(path: str | Path, driver: Any) -> dict[str, Any]:
    """Idempotently import only nodes and relationships from a verified snapshot."""
    payload = load_verified_legacy_neo4j_snapshot(path)
    if payload is None:
        return {"node_count": 0, "relationship_count": 0, "sha256": None}
    nodes = payload["nodes"]
    relationships = payload["relationships"]
    node_ids = {str(item.get("source_id")) for item in nodes}
    if None in node_ids or "None" in node_ids or len(node_ids) != len(nodes):
        raise LegacyNeo4jAdoptionError("retained_neo4j_node_identity_invalid")

    with driver.session() as session:
        for item in nodes:
            labels = [_identifier(label, "label") for label in item.get("labels", [])]
            if not labels:
                raise LegacyNeo4jAdoptionError("retained_neo4j_label_missing")
            label_clause = "".join(f":`{label}`" for label in sorted(set(labels)))
            properties = item.get("properties")
            if not isinstance(properties, dict):
                raise LegacyNeo4jAdoptionError("retained_neo4j_properties_invalid")
            session.run(
                f"MERGE (n {{_dle_adoption_source_id: $source_id}}) "
                f"SET n{label_clause} SET n += $properties",
                source_id=str(item["source_id"]),
                properties=properties,
            ).consume()
        for item in relationships:
            relationship_type = _identifier(item.get("type"), "relationship_type")
            start_id = str(item.get("start_source_id"))
            end_id = str(item.get("end_source_id"))
            if start_id not in node_ids or end_id not in node_ids:
                raise LegacyNeo4jAdoptionError("retained_neo4j_relationship_endpoint_missing")
            properties = item.get("properties")
            if not isinstance(properties, dict):
                raise LegacyNeo4jAdoptionError("retained_neo4j_properties_invalid")
            session.run(
                "MATCH (s {_dle_adoption_source_id: $start_id}), "
                "(t {_dle_adoption_source_id: $end_id}) "
                f"MERGE (s)-[r:`{relationship_type}` "
                "{_dle_adoption_source_id: $source_id}]->(t) SET r += $properties",
                start_id=start_id,
                end_id=end_id,
                source_id=str(item.get("source_id")),
                properties=properties,
            ).consume()
        counts = session.run(
            "MATCH (n) WHERE n._dle_adoption_source_id IS NOT NULL "
            "WITH count(n) AS nodes "
            "OPTIONAL MATCH ()-[r]->() WHERE r._dle_adoption_source_id IS NOT NULL "
            "RETURN nodes, count(r) AS relationships"
        ).single()
    if counts is None or int(counts["nodes"]) != len(nodes):
        raise LegacyNeo4jAdoptionError("retained_neo4j_node_count_mismatch")
    if int(counts["relationships"]) != len(relationships):
        raise LegacyNeo4jAdoptionError("retained_neo4j_relationship_count_mismatch")
    return {
        "node_count": len(nodes),
        "relationship_count": len(relationships),
        "sha256": payload["sha256"],
    }
