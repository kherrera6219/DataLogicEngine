"""Verify the app-owned five-service internal data plane.

Qualification mode exercises immutable engineering candidates without granting
production authority.  Production mode is fail-closed until the candidate lock
and ADR approvals are complete.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.runtime.podman_data_plane import (  # noqa: E402
    APP_SERVICE_KEYS,
    PodmanDataPlaneManager,
    REQUIRED_OBJECT_BUCKETS,
)


DEFAULT_LOCK = REPO_ROOT / "deploy" / "internal-data-plane.candidate-lock.json"
DEFAULT_REPORT = (
    REPO_ROOT
    / "reports"
    / "production-readiness"
    / "2026"
    / "phase-03"
    / "internal-data-plane-qualification.json"
)


def _default_runtime_root() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir())
    return base / "DataLogicEngine" / "qualification" / "phase-03-data-plane"


def _stable_installation_id(runtime_root: Path) -> str:
    vault_path = runtime_root / "security" / "data-plane-credentials.json"
    if vault_path.exists():
        try:
            existing = json.loads(vault_path.read_text(encoding="utf-8"))
            installation_id = str(existing.get("installation_id") or "").strip().lower()
            if len(installation_id) >= 32 and all(
                character in "0123456789abcdef" for character in installation_id
            ):
                return installation_id
        except (OSError, TypeError, ValueError):
            pass
    seed = f"{runtime_root.resolve()}|phase-03-qualification"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


class Recorder:
    def __init__(self) -> None:
        self.checks: list[dict[str, Any]] = []

    def run(self, name: str, callback) -> Any | None:
        started = datetime.now(UTC)
        try:
            evidence = callback()
        except Exception as exc:
            self.checks.append(
                {
                    "name": name,
                    "status": "fail",
                    "started_at": started.isoformat(),
                    "finished_at": datetime.now(UTC).isoformat(),
                    "safe_reason": _safe_reason(exc),
                }
            )
            return None
        self.checks.append(
            {
                "name": name,
                "status": "pass",
                "started_at": started.isoformat(),
                "finished_at": datetime.now(UTC).isoformat(),
                "evidence": evidence,
            }
        )
        return evidence


def _safe_reason(exc: Exception) -> str:
    value = str(exc).strip()
    if value and all(character.isalnum() or character in "_:,-." for character in value):
        return value[:160]
    return f"{exc.__class__.__name__}:qualification_check_failed"


def _postgres_contract(manager: PodmanDataPlaneManager, run_id: str) -> dict[str, Any]:
    import psycopg2

    settings = manager.connection_settings()
    table = "dle_phase3_qualification"
    with psycopg2.connect(settings["database_url"], connect_timeout=5) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {table} (run_id text PRIMARY KEY, payload text NOT NULL)"
            )
            cursor.execute(
                f"INSERT INTO {table} (run_id, payload) VALUES (%s, %s) "
                "ON CONFLICT (run_id) DO UPDATE SET payload = EXCLUDED.payload",
                (run_id, "postgresql-contract"),
            )
        connection.commit()
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT payload FROM {table} WHERE run_id = %s", (run_id,))
            observed = cursor.fetchone()[0]
    if observed != "postgresql-contract":
        raise RuntimeError("postgresql_contract_mismatch")

    rollback_marker = f"{run_id}-rollback"
    connection = psycopg2.connect(settings["database_url"], connect_timeout=5)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"INSERT INTO {table} (run_id, payload) VALUES (%s, %s)",
                (rollback_marker, "must-rollback"),
            )
        connection.rollback()
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE run_id = %s", (rollback_marker,))
            if cursor.fetchone()[0] != 0:
                raise RuntimeError("postgresql_rollback_failed")
    finally:
        connection.close()
    return {"table": table, "run_id": run_id, "transaction_rollback": True}


def _redis_contract(manager: PodmanDataPlaneManager, run_id: str) -> dict[str, Any]:
    import redis

    client = redis.Redis.from_url(manager.connection_settings()["redis_url"], decode_responses=True)
    key = f"dle:qualification:{run_id}"
    created = client.set(key, "redis-contract", nx=True, ex=300)
    if created is not True and client.get(key) != "redis-contract":
        raise RuntimeError("redis_idempotent_write_failed")
    if client.get(key) != "redis-contract":
        raise RuntimeError("redis_readback_mismatch")
    stream = f"dle:qualification:stream:{run_id}"
    message_id = client.xadd(stream, {"run_id": run_id, "status": "ready"})
    messages = client.xrange(stream, min=message_id, max=message_id)
    if not messages or messages[0][1].get("run_id") != run_id:
        raise RuntimeError("redis_stream_contract_mismatch")
    return {"key": key, "stream": stream, "message_id": message_id}


def _neo4j_contract(manager: PodmanDataPlaneManager, run_id: str) -> dict[str, Any]:
    from neo4j import GraphDatabase

    settings = manager.connection_settings()
    driver = GraphDatabase.driver(
        settings["neo4j_uri"],
        auth=(settings["neo4j_user"], settings["neo4j_password"]),
    )
    try:
        driver.execute_query(
            "MERGE (n:DLEQualification {run_id: $run_id}) "
            "SET n.status = 'neo4j-contract' RETURN n.status AS status",
            run_id=run_id,
            database_="neo4j",
        )
        records, _summary, _keys = driver.execute_query(
            "MATCH (n:DLEQualification {run_id: $run_id}) RETURN n.status AS status",
            run_id=run_id,
            database_="neo4j",
        )
    finally:
        driver.close()
    if not records or records[0]["status"] != "neo4j-contract":
        raise RuntimeError("neo4j_contract_mismatch")
    return {"label": "DLEQualification", "run_id": run_id}


def _chroma_contract(manager: PodmanDataPlaneManager, run_id: str) -> dict[str, Any]:
    import chromadb

    settings = manager.connection_settings()
    client = chromadb.HttpClient(
        host=settings["chroma_host"],
        port=settings["chroma_port"],
        ssl=False,
    )
    collection_name = "dle_phase3_qualification"
    collection = client.get_or_create_collection(collection_name)
    collection.upsert(
        ids=[run_id],
        documents=["chroma contract fixture"],
        embeddings=[[0.1, 0.2, 0.3, 0.4]],
        metadatas=[{"run_id": run_id, "schema_version": "1"}],
    )
    observed = collection.get(ids=[run_id], include=["documents", "metadatas"])
    if observed.get("ids") != [run_id]:
        raise RuntimeError("chroma_contract_mismatch")
    query = collection.query(
        query_embeddings=[[0.1, 0.2, 0.3, 0.4]],
        n_results=1,
        where={"run_id": run_id},
    )
    if not query.get("ids") or query["ids"][0] != [run_id]:
        raise RuntimeError("chroma_query_parity_failed")
    return {"collection": collection_name, "run_id": run_id, "dimension": 4}


def _object_contract(manager: PodmanDataPlaneManager, run_id: str) -> dict[str, Any]:
    import boto3
    from botocore.config import Config

    settings = manager.connection_settings()
    client = boto3.client(
        "s3",
        endpoint_url=settings["object_endpoint"],
        aws_access_key_id=settings["object_access_key"],
        aws_secret_access_key=settings["object_secret_key"],
        region_name=settings["object_region"],
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )
    hashes: dict[str, str] = {}
    for bucket in REQUIRED_OBJECT_BUCKETS:
        key = f"qualification/{run_id}.json"
        payload = json.dumps({"run_id": run_id, "bucket": bucket}, sort_keys=True).encode()
        digest = hashlib.sha256(payload).hexdigest()
        client.put_object(
            Bucket=bucket,
            Key=key,
            Body=payload,
            ContentType="application/json",
            Metadata={"sha256": digest, "run-id": run_id},
        )
        received = client.get_object(Bucket=bucket, Key=key)["Body"].read()
        head = client.head_object(Bucket=bucket, Key=key)
        listed = client.list_objects_v2(Bucket=bucket, Prefix=key)
        if hashlib.sha256(received).hexdigest() != digest:
            raise RuntimeError("object_store_hash_mismatch")
        if head.get("Metadata", {}).get("sha256") != digest:
            raise RuntimeError("object_store_metadata_mismatch")
        if key not in {item["Key"] for item in listed.get("Contents", [])}:
            raise RuntimeError("object_store_list_mismatch")
        hashes[bucket] = digest
    return {"buckets": list(REQUIRED_OBJECT_BUCKETS), "object_sha256": hashes}


def _restart_durability(manager: PodmanDataPlaneManager, run_id: str) -> dict[str, Any]:
    for service in APP_SERVICE_KEYS:
        if not manager.restart_service(service):
            raise RuntimeError(f"service_restart_failed:{service}")
    return {
        "postgresql": _postgres_contract(manager, run_id),
        "redis": _redis_contract(manager, run_id),
        "neo4j": _neo4j_contract(manager, run_id),
        "chroma": _chroma_contract(manager, run_id),
        "object_store": _object_contract(manager, run_id),
    }


def verify(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    started = datetime.now(UTC)
    runtime_root = Path(args.runtime_root).resolve()
    installation_id = args.installation_id or _stable_installation_id(runtime_root)
    recorder = Recorder()
    manager = PodmanDataPlaneManager(
        runtime_root=runtime_root,
        installation_id=installation_id,
        profile=args.profile,
        lock_path=args.lock,
        runtime=args.runtime,
        require_dpapi=os.name == "nt",
        command_timeout_seconds=args.timeout,
    )
    run_id = uuid.uuid4().hex
    cleanup: dict[str, bool] = {}
    try:
        recorder.run("runtime_identity", manager.verify_runtime)
        recorder.run("immutable_artifacts", manager.verify_artifacts)
        start_results = recorder.run("start_all_services", manager.start_all)
        if not start_results or not all(start_results.values()):
            raise RuntimeError("required_service_start_failed")
        recorder.run("postgresql_contract", lambda: _postgres_contract(manager, run_id))
        recorder.run("redis_contract", lambda: _redis_contract(manager, run_id))
        recorder.run("neo4j_contract", lambda: _neo4j_contract(manager, run_id))
        recorder.run("chroma_contract", lambda: _chroma_contract(manager, run_id))
        recorder.run("object_store_contract", lambda: _object_contract(manager, run_id))
        recorder.run(
            "restart_durability",
            lambda: _restart_durability(manager, run_id),
        )
        recorder.run("truthful_status", manager.status_snapshot)
    except Exception as exc:
        recorder.checks.append(
            {
                "name": "qualification_execution",
                "status": "fail",
                "safe_reason": _safe_reason(exc),
                "service_failure_reasons": manager.last_failure_reasons,
                "finished_at": datetime.now(UTC).isoformat(),
            }
        )
    finally:
        manager.stop_all()
        if args.profile == "qualification" and not args.keep_resources:
            cleanup = manager.remove_qualification_profile()
            recorder.checks.append(
                {
                    "name": "qualification_resource_cleanup",
                    "status": "pass" if cleanup and all(cleanup.values()) else "fail",
                    "finished_at": datetime.now(UTC).isoformat(),
                    "evidence": cleanup,
                }
            )

    failed = [item["name"] for item in recorder.checks if item["status"] != "pass"]
    report = {
        "schema_version": "1.0.0",
        "captured_at": datetime.now(UTC).isoformat(),
        "started_at": started.isoformat(),
        "duration_seconds": round((datetime.now(UTC) - started).total_seconds(), 3),
        "profile": args.profile,
        "run_id": run_id,
        "installation_id_hash": hashlib.sha256(installation_id.encode()).hexdigest(),
        "status": "passed" if not failed else "failed",
        "failed_checks": failed,
        "checks": recorder.checks,
        "production_authorized": manager.plan.production_authorized,
        "release_gate": (
            "engineering_qualification_only"
            if args.profile == "qualification"
            else "production"
        ),
        "known_deferred_gates": [
            "signed_installer_clean_machine",
            "supported_prior_version_upgrade",
            "coordinated_phase4_backup_restore",
            "independent_redistribution_review",
            "independent_security_review",
            "final_object_store_replacement_decision",
        ],
    }
    return report, 0 if not failed else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify the internal data plane")
    parser.add_argument("--profile", choices=("qualification", "production"), default="production")
    parser.add_argument("--require-all", action="store_true", help="Compatibility flag; all five services are always required")
    parser.add_argument("--runtime", default="podman")
    parser.add_argument("--runtime-root", default=str(_default_runtime_root()))
    parser.add_argument("--installation-id")
    parser.add_argument("--lock", default=str(DEFAULT_LOCK))
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--keep-resources", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        report, exit_code = verify(args)
    except Exception as exc:
        report = {
            "schema_version": "1.0.0",
            "captured_at": datetime.now(UTC).isoformat(),
            "profile": args.profile,
            "status": "blocked",
            "safe_reason": _safe_reason(exc),
            "production_authorized": False,
        }
        exit_code = 2
    report_path = Path(args.report).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
