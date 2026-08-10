from __future__ import annotations

import hashlib
import json

import pytest

from backend.storage.legacy_neo4j_adoption import (
    LegacyNeo4jAdoptionError,
    SNAPSHOT_SCHEMA_VERSION,
    import_legacy_neo4j_snapshot,
    load_verified_legacy_neo4j_snapshot,
)


def _snapshot(path):
    payload = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "source": "test",
        "nodes": [
            {"source_id": "n1", "labels": ["Pillar"], "properties": {"uid": "P1"}},
            {"source_id": "n2", "labels": ["Pillar"], "properties": {"uid": "P2"}},
        ],
        "relationships": [
            {
                "source_id": "r1",
                "start_source_id": "n1",
                "end_source_id": "n2",
                "type": "HONEYCOMB_BRIDGE",
                "properties": {"weight": 1.0},
            }
        ],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    payload["sha256"] = hashlib.sha256(canonical).hexdigest()
    path.write_text(json.dumps(payload), encoding="utf-8")
    return payload


def test_snapshot_hash_is_required(tmp_path):
    path = tmp_path / "graph.json"
    payload = _snapshot(path)

    assert load_verified_legacy_neo4j_snapshot(path) == payload
    payload["nodes"][0]["properties"]["uid"] = "tampered"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(LegacyNeo4jAdoptionError, match="snapshot_hash_mismatch"):
        load_verified_legacy_neo4j_snapshot(path)


def test_snapshot_import_is_bounded_and_count_verified(tmp_path):
    path = tmp_path / "graph.json"
    payload = _snapshot(path)

    class Result:
        def __init__(self, counts=None):
            self.counts = counts

        def consume(self):
            return None

        def single(self):
            return self.counts

    class Session:
        def __init__(self):
            self.calls = []

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def run(self, query, **parameters):
            self.calls.append((query, parameters))
            if "RETURN nodes" in query:
                return Result({"nodes": 2, "relationships": 1})
            return Result()

    class Driver:
        def __init__(self):
            self.active = Session()

        def session(self):
            return self.active

    driver = Driver()
    result = import_legacy_neo4j_snapshot(path, driver)

    assert result == {
        "node_count": 2,
        "relationship_count": 1,
        "sha256": payload["sha256"],
    }
    assert len(driver.active.calls) == 4
    assert all("DELETE" not in query.upper() for query, _ in driver.active.calls)
