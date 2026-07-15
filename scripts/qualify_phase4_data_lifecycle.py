"""Run the populated Phase 4 backup, clean-root restore, and delete-parity drill."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any
import uuid

from sqlalchemy import text


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import create_app  # noqa: E402
from backend.runtime.podman_data_plane import APP_SERVICE_KEYS  # noqa: E402
from backend.security.windows_acl import verify_restricted_user_acl  # noqa: E402
from backend.storage.chroma_security import (  # noqa: E402
    safe_create_collection,
    safe_get_collection,
)
from backend.storage.data_at_rest import build_at_rest_report  # noqa: E402
from backend.storage.managed_backup import create_managed_backup  # noqa: E402
from backend.storage.managed_restore import restore_managed_backup_offline  # noqa: E402
from backend.storage.outbox import CrossStoreOutbox  # noqa: E402
from backend.storage.retention import DeletionSubject  # noqa: E402
from backend.storage.user_deletion import run_user_deletion  # noqa: E402
from extensions import db  # noqa: E402


DEFAULT_LOCK = ROOT / "deploy" / "internal-data-plane.candidate-lock.json"
DEFAULT_REPORT = (
    ROOT
    / "reports"
    / "production-readiness"
    / "2026"
    / "phase-04"
    / "phase04_data_lifecycle_qualification.json"
)
RECOVERY_SECRET = "phase4-owner-qualification-secret"


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _app(runtime_root: Path, lock_path: Path):
    return create_app(
        "testing",
        config_overrides={
            "APP_VERSION": "0.1.1",
            "DLE_RUNTIME_ROOT": str(runtime_root),
            "DLE_DATA_PLANE_DRIVER": "podman",
            "DLE_DATA_PLANE_PROFILE": "qualification",
            "DLE_DATA_PLANE_LOCK_PATH": str(lock_path),
            "DLE_REQUIRED_SERVICES": APP_SERVICE_KEYS,
            "DLE_START_MANAGED_SERVICES": True,
            "DLE_INITIALIZE_STORES": True,
            "DLE_START_BACKGROUND_WORKERS": False,
            "DLE_CONFIGURE_LOGGING": False,
            "DLE_SERVICE_START_TIMEOUT_SECONDS": 180,
        },
    )


def _populate(app, run_id: str) -> dict[str, Any]:
    manager = app.extensions["dle_data_plane_manager"]
    settings = manager.connection_settings()
    with app.app_context():
        user_id = int(
            db.session.execute(
                text(
                    "INSERT INTO users (username, email, active, failed_login_attempts) "
                    "VALUES (:username, :email, true, 0) RETURNING id"
                ),
                {
                    "username": f"phase4-{run_id[:12]}",
                    "email": f"phase4-{run_id[:12]}@qualification.local",
                },
            ).scalar_one()
        )
        CrossStoreOutbox(db.session).enqueue(
            entity_type="qualification_artifact",
            entity_id=str(user_id),
            destination="minio",
            operation="put_object",
            schema_version="qualification-artifact.v1",
            source_revision=f"qualification:{run_id}",
            payload={
                "bucket": "deliverables",
                "key": f"phase4/pending-{run_id}.json",
                "body": {"run_id": run_id, "user_id": user_id},
                "content_type": "application/json",
                "metadata": {"user_id": str(user_id), "run_id": run_id},
            },
            correlation_id=run_id,
        )
        db.session.commit()

        import redis
        from neo4j import GraphDatabase

        from backend.storage.chroma_http import ChromaHttpClient
        from backend.storage import get_object_store

        redis_client = redis.Redis.from_url(settings["redis_url"])
        neo4j_driver = GraphDatabase.driver(
            settings["neo4j_uri"],
            auth=(settings["neo4j_user"], settings["neo4j_password"]),
        )
        chroma_client = ChromaHttpClient(
            host=settings["chroma_host"],
            port=settings["chroma_port"],
        )
        try:
            redis_key = f"dle:user:{user_id}:phase4"
            redis_client.set(redis_key, f"durable-{run_id}")
            with neo4j_driver.session() as session:
                session.run(
                    "CREATE (n:Phase4Qualification {uid: $uid, user_id: $user_id, "
                    "tenant_id: $tenant_id, source_revision: $revision})",
                    uid=f"phase4-{run_id}",
                    user_id=str(user_id),
                    tenant_id="phase4-tenant",
                    revision=run_id,
                ).consume()
            collection = safe_create_collection(
                chroma_client,
                name=f"phase4_{run_id[:16]}",
                metadata={"schema_version": "qualification.v1"},
            )
            collection.add(
                ids=[f"phase4-{run_id}"],
                embeddings=[[0.1, 0.2, 0.3]],
                documents=["phase four recovery qualification"],
                metadatas=[
                    {
                        "user_id": str(user_id),
                        "tenant_id": "phase4-tenant",
                        "source_revision": run_id,
                    }
                ],
            )
            store = get_object_store()
            object_key = f"phase4/populated-{run_id}.json"
            object_body = json.dumps(
                {"run_id": run_id, "user_id": user_id},
                sort_keys=True,
            ).encode("utf-8")
            store.put(
                "deliverables",
                object_key,
                object_body,
                content_type="application/json",
                metadata={
                    "user_id": str(user_id),
                    "tenant_id": "phase4-tenant",
                    "source_revision": run_id,
                },
            )
        finally:
            redis_client.close()
            neo4j_driver.close()

    memory_path = runtime_root = app.extensions["dle_runtime"].runtime_root
    memory_path = runtime_root / "databases" / "memory" / "memory_graph.json"
    memory = json.loads(memory_path.read_text(encoding="utf-8"))
    memory["vertices"].append(
        {
            "vertex_id": f"phase4-{run_id}",
            "metadata": {
                "user_id": str(user_id),
                "tenant_id": "phase4-tenant",
            },
        }
    )
    memory_path.write_text(json.dumps(memory, sort_keys=True) + "\n", encoding="utf-8")
    log_path = runtime_root / "logs" / "phase4-qualification.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(f"qualification user {user_id} run {run_id}\n", encoding="utf-8")
    return {
        "user_id": user_id,
        "redis_key": redis_key,
        "collection": f"phase4_{run_id[:16]}",
        "node_uid": f"phase4-{run_id}",
        "object_key": object_key,
        "object_sha256": hashlib.sha256(object_body).hexdigest(),
    }


def _verify_restored(app, expected: dict[str, Any], run_id: str) -> dict[str, Any]:
    manager = app.extensions["dle_data_plane_manager"]
    settings = manager.connection_settings()
    import redis
    from neo4j import GraphDatabase

    from backend.storage.chroma_http import ChromaHttpClient
    from backend.storage import get_object_store

    with app.app_context():
        sql_count = int(
            db.session.execute(
                text("SELECT count(*) FROM users WHERE id = :user_id"),
                {"user_id": expected["user_id"]},
            ).scalar_one()
        )
        pending_count = int(
            db.session.execute(
                text(
                    "SELECT count(*) FROM cross_store_outbox_events "
                    "WHERE entity_id = :entity_id AND status = 'pending'"
                ),
                {"entity_id": str(expected["user_id"])},
            ).scalar_one()
        )
        redis_client = redis.Redis.from_url(settings["redis_url"])
        neo4j_driver = GraphDatabase.driver(
            settings["neo4j_uri"],
            auth=(settings["neo4j_user"], settings["neo4j_password"]),
        )
        chroma_client = ChromaHttpClient(
            host=settings["chroma_host"],
            port=settings["chroma_port"],
        )
        try:
            redis_value = redis_client.get(expected["redis_key"])
            with neo4j_driver.session() as session:
                neo4j_count = int(
                    session.run(
                        "MATCH (n:Phase4Qualification {uid: $uid}) RETURN count(n) AS count",
                        uid=expected["node_uid"],
                    ).single()["count"]
                )
            chroma_count = int(
                safe_get_collection(
                    chroma_client,
                    name=expected["collection"],
                ).count()
            )
            store = get_object_store()
            object_hash = hashlib.sha256(
                store.get("deliverables", expected["object_key"])
            ).hexdigest()
        finally:
            redis_client.close()
            neo4j_driver.close()
        memory_path = (
            app.extensions["dle_runtime"].runtime_root
            / "databases"
            / "memory"
            / "memory_graph.json"
        )
        memory = json.loads(memory_path.read_text(encoding="utf-8"))
        memory_count = sum(
            1
            for item in memory.get("vertices", [])
            if item.get("vertex_id") == expected["node_uid"]
        )
        values = {
            "postgresql_user": sql_count,
            "postgresql_pending_outbox": pending_count,
            "redis_durable_key": 1 if redis_value == f"durable-{run_id}".encode() else 0,
            "neo4j_node": neo4j_count,
            "chroma_record": chroma_count,
            "minio_object_hash": object_hash,
            "local_json_vertex": memory_count,
        }
        if any(value != 1 for key, value in values.items() if key != "minio_object_hash"):
            raise RuntimeError("restored_store_count_mismatch")
        if object_hash != expected["object_sha256"]:
            raise RuntimeError("restored_object_hash_mismatch")
        return values


def qualify(args: argparse.Namespace) -> dict[str, Any]:
    started = datetime.now(UTC)
    run_id = uuid.uuid4().hex
    workspace = Path(tempfile.mkdtemp(prefix="dle-phase4-qualification-"))
    source_root = workspace / "active-runtime"
    backup_root = workspace / "backups"
    source_app = _app(source_root, args.lock)
    source_runtime = source_app.extensions["dle_runtime"]
    source_manager = source_app.extensions["dle_data_plane_manager"]
    restored_app = None
    restored_manager = None
    checks: dict[str, Any] = {}
    try:
        source_runtime.start()
        checks["source_startup"] = source_runtime.readiness()[0]
        expected = _populate(source_app, run_id)
        backup = create_managed_backup(
            source_app,
            source_runtime,
            backup_root,
            RECOVERY_SECRET,
        )
        checks["backup"] = {
            key: value
            for key, value in backup.items()
            if key not in {"artifact_path", "manifest"}
        }
        checks["backup"]["artifact_sha256"] = backup["sha256"]
        source_runtime.shutdown()

        restore = restore_managed_backup_offline(
            backup["artifact_path"],
            source_root,
            recovery_secret=RECOVERY_SECRET,
            product_version="0.1.1",
            lock_path=args.lock,
            profile="qualification",
            runtime_binary=args.runtime,
            post_swap_validator=lambda root: (root / "installation.json").is_file(),
        )
        checks["restore"] = {
            "status": restore["status"],
            "cross_store": restore["cross_store"],
            "prior_root_preserved": bool(restore.get("prior_root")),
            "activation": restore["activation"],
        }

        restored_app = _app(source_root, args.lock)
        restored_runtime = restored_app.extensions["dle_runtime"]
        restored_manager = restored_app.extensions["dle_data_plane_manager"]
        restored_runtime.start()
        checks["restored_values"] = _verify_restored(restored_app, expected, run_id)
        with restored_app.app_context():
            tombstone = run_user_deletion(
                restored_app,
                DeletionSubject(
                    "user",
                    str(expected["user_id"]),
                    tenant_id="phase4-tenant",
                ),
            )
            checks["delete_parity"] = {
                "status": tombstone.status,
                "stores": tombstone.store_status,
                "subject_digest_length": len(tombstone.subject_digest),
            }
        if tombstone.status != "completed" or not all(
            item["status"] == "pass" for item in tombstone.store_status.values()
        ):
            raise RuntimeError("delete_parity_failed")
        checks["at_rest"] = build_at_rest_report(
            source_root,
            acl_probe=verify_restricted_user_acl,
        )
        restored_runtime.shutdown()
        return {
            "schema_version": "1.0.0",
            "captured_at": datetime.now(UTC).isoformat(),
            "started_at": started.isoformat(),
            "duration_seconds": round((datetime.now(UTC) - started).total_seconds(), 3),
            "status": "passed",
            "release_gate": "engineering_qualification_only",
            "production_authorized": False,
            "object_store_architecture": "minio",
            "seaweedfs_production_selected": False,
            "run_id_sha256": _sha256(run_id),
            "checks": checks,
            "deferred_release_gates": [
                "signed_installer_clean_machine_restore",
                "supported_0_1_1_retained_data_upgrade",
                "bitlocker_and_acl_supported_windows_matrix",
                "independent_backup_restore_review",
                "final_object_store_replacement_decision",
            ],
        }
    except Exception as exc:
        return {
            "schema_version": "1.0.0",
            "captured_at": datetime.now(UTC).isoformat(),
            "status": "failed",
            "safe_reason": str(exc)
            if str(exc).replace("_", "").replace(":", "").isalnum()
            else type(exc).__name__,
            "production_authorized": False,
            "seaweedfs_production_selected": False,
            "checks": checks,
        }
    finally:
        for app in (restored_app, source_app):
            if app is None:
                continue
            runtime = app.extensions.get("dle_runtime")
            if runtime is not None:
                runtime.shutdown()
        for manager in (restored_manager, source_manager):
            if manager is None:
                continue
            try:
                manager.stop_all()
                manager.remove_qualification_profile()
            except Exception:
                continue
        if not args.keep_workspace:
            shutil.rmtree(workspace, ignore_errors=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", default="podman")
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--keep-workspace", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = qualify(args)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
