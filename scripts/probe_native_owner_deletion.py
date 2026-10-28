"""Exercise owner deletion against three explicitly disposable empty services."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from time import monotonic, sleep

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    JSON,
    MetaData,
    String,
    Table,
    create_engine,
    inspect,
    select,
)
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.storage.chroma_http import ChromaHttpClient, ChromaHttpError
from backend.storage.chroma_security import safe_create_collection
from backend.storage.knowledge_ownership import build_knowledge_ownership_plan
from backend.storage.retention import (
    DeletionSubject,
    RetentionDeleteCoordinator,
    RetentionDeleteError,
)
from backend.storage.user_deletion import (
    PostgreSQLUserDeletionAdapter,
    ChromaUserDeletionAdapter,
    Neo4jUserDeletionAdapter,
)
from models import DataDeletionTombstone


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--postgres-port", type=int, required=True)
    parser.add_argument("--neo4j-port", type=int, required=True)
    parser.add_argument("--chroma-port", type=int, required=True)
    parser.add_argument("--test-password", required=True)
    parser.add_argument(
        "--disposable-empty-services", action="store_true", required=True
    )
    args = parser.parse_args()
    engine = create_engine(
        URL.create(
            "postgresql+psycopg2",
            username="probe",
            password=args.test_password,
            host="127.0.0.1",
            port=args.postgres_port,
            database="ownership_probe",
        )
    )
    graph = GraphDatabase.driver(
        f"bolt://127.0.0.1:{args.neo4j_port}", connection_timeout=5
    )
    chroma = ChromaHttpClient(host="127.0.0.1", port=args.chroma_port)
    try:
        deadline = monotonic() + 30
        while True:
            try:
                with engine.connect() as connection:
                    connection.exec_driver_sql("SELECT 1")
                graph.verify_connectivity()
                chroma.heartbeat()
                break
            except (SQLAlchemyError, ServiceUnavailable, ChromaHttpError):
                if monotonic() >= deadline:
                    raise
                sleep(0.5)
        if inspect(engine).get_table_names(schema="public") or chroma.list_collections(
            limit=1
        ):
            raise RuntimeError("disposable_empty_services_required")
        with graph.session() as connection:
            if connection.run("MATCH (n) RETURN count(n) AS count").single()["count"]:
                raise RuntimeError("disposable_empty_services_required")
        metadata = MetaData()
        users = Table("users", metadata, Column("id", Integer, primary_key=True))
        nodes = Table(
            "ukg_knowledge_nodes",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("uid", String),
            Column("node_metadata", JSON),
            Column("tenant_id", String),
            Column("content", String),
        )
        jobs = Table(
            "ingestion_jobs",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("user_id", Integer, ForeignKey("users.id")),
            Column("tenant_id", String),
        )
        files = Table(
            "ingestion_files",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("job_id", Integer, ForeignKey("ingestion_jobs.id")),
            Column("status", String),
        )
        chunks = Table(
            "ingestion_chunks",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("job_id", Integer, ForeignKey("ingestion_jobs.id")),
            Column("file_id", Integer, ForeignKey("ingestion_files.id")),
            Column("node_uid", String),
        )
        for name in ("cross_store_materialization_states", "cross_store_outbox_events"):
            Table(
                name,
                metadata,
                Column("id", Integer, primary_key=True),
                Column("entity_id", String),
            )
        DataDeletionTombstone.__table__.to_metadata(metadata)
        metadata.create_all(engine)
        collection = safe_create_collection(
            chroma, name="synthetic_owned", metadata={"dle_disposable_test_data": True}
        )
        ids = [
            "owned",
            "owned:chunk:1",
            *[f"nested-{i}" for i in range(600)],
            "retained",
        ]
        metas = [
            {"tenant_id": "same", "source": "legacy"},
            {"vector_parent_id": "owned"},
            *[
                {"permissions": json.dumps({"owner_user_id": 1}), "tenant_id": "same"}
                for _ in range(600)
            ],
            {"permissions": json.dumps({"owner_user_id": 2}), "tenant_id": "same"},
        ]
        collection.upsert(
            ids=ids,
            embeddings=[[1.0, 0.0] for _ in ids],
            documents=["synthetic content" for _ in ids],
            metadatas=metas,
        )
        with graph.session() as connection:
            rows = [
                {"uid": "owned", "tenant_id": "same"},
                *[
                    {
                        "uid": f"nested-{i}",
                        "tenant_id": "same",
                        "permissions": json.dumps({"owner_user_id": 1}),
                    }
                    for i in range(600)
                ],
                {"uid": "retained", "user_id": "2", "tenant_id": "same"},
            ]
            connection.run(
                "UNWIND $rows AS row CREATE (n:OwnershipProbe) SET n = row", rows=rows
            ).consume()
        with Session(engine) as session:
            session.execute(users.insert(), [{"id": 1}, {"id": 2}])
            session.execute(
                nodes.insert(),
                [
                    {
                        "id": 1,
                        "uid": "owned",
                        "node_metadata": {"permissions": {"owner_user_id": 1}},
                        "tenant_id": "same",
                        "content": "synthetic owner one",
                    },
                    {
                        "id": 2,
                        "uid": "retained",
                        "node_metadata": {"permissions": {"owner_user_id": 2}},
                        "tenant_id": "same",
                        "content": "synthetic owner two",
                    },
                ],
            )
            session.execute(
                jobs.insert(),
                [
                    {"id": 1, "user_id": 1, "tenant_id": "same"},
                    {"id": 2, "user_id": 2, "tenant_id": "same"},
                ],
            )
            session.execute(
                files.insert(),
                [
                    {"id": 1, "job_id": 1, "status": "ready"},
                    {"id": 2, "job_id": 2, "status": "ready"},
                ],
            )
            session.execute(
                chunks.insert(),
                [
                    {"id": 1, "job_id": 1, "file_id": 1, "node_uid": "owned"},
                    {"id": 2, "job_id": 2, "file_id": 2, "node_uid": "retained"},
                ],
            )
            session.commit()
            subject = DeletionSubject("user", "1", tenant_id="same")
            plan = build_knowledge_ownership_plan(session, metadata, subject)
            adapters = {
                "postgresql": PostgreSQLUserDeletionAdapter(session, metadata),
                "chroma": ChromaUserDeletionAdapter(chroma, knowledge_uids=plan.uids),
                "neo4j": Neo4jUserDeletionAdapter(graph, knowledge_uids=plan.uids),
            }
            lifecycle = SimpleNamespace(
                execute_operation_sync=lambda **kwargs: SimpleNamespace(
                    to_dict=lambda: {"synthetic_lifecycle": True}
                )
            )
            receipt = RetentionDeleteCoordinator(
                session=session,
                adapters=adapters,
                required_stores=tuple(adapters),
                digest_key="synthetic-installation-tombstone-key",
                knowledge_lifecycle=lifecycle,
            ).run(subject)
            assert receipt.status == "completed"
            assert all(
                item["retained_count"] == 0 and item["status"] == "pass"
                for item in receipt.store_status.values()
            )
            assert session.execute(select(nodes.c.uid)).scalars().all() == ["retained"]
            assert session.execute(select(users.c.id)).scalars().all() == [2]
            assert collection.get(include=["metadatas"])["ids"] == ["retained"]
            with graph.session() as connection:
                assert [
                    row["uid"]
                    for row in connection.run("MATCH (n) RETURN n.uid AS uid")
                ] == ["retained"]
            # An older shared UID must be held before any store is mutated.
            session.execute(users.insert(), [{"id": 3}, {"id": 4}])
            session.execute(
                nodes.insert(),
                {
                    "id": 3,
                    "uid": "shared",
                    "node_metadata": {"permissions": {"owner_user_id": 3}},
                    "tenant_id": "same",
                    "content": "synthetic shared content",
                },
            )
            session.execute(
                jobs.insert(),
                [
                    {"id": 3, "user_id": 3, "tenant_id": "same"},
                    {"id": 4, "user_id": 4, "tenant_id": "same"},
                ],
            )
            session.execute(
                files.insert(),
                [
                    {"id": 3, "job_id": 3, "status": "ready"},
                    {"id": 4, "job_id": 4, "status": "ready"},
                ],
            )
            session.execute(
                chunks.insert(),
                [
                    {"id": 3, "job_id": 3, "file_id": 3, "node_uid": "shared"},
                    {"id": 4, "job_id": 4, "file_id": 4, "node_uid": "shared"},
                ],
            )
            session.commit()
            try:
                build_knowledge_ownership_plan(
                    session, metadata, DeletionSubject("user", "3")
                )
            except RetentionDeleteError as error:
                assert "shared" in str(error)
            else:
                raise AssertionError("shared ownership must block deletion")
            assert (
                session.execute(select(nodes.c.uid).where(nodes.c.id == 3)).scalar_one()
                == "shared"
            )
            print(
                json.dumps(
                    {
                        "status": "pass",
                        "synthetic_only": True,
                        "native_stores": ["PostgreSQL", "Chroma", "Neo4j"],
                        "coordinator_receipt": "completed",
                        "store_results": receipt.store_status,
                        "other_owner_same_tenant_preserved": True,
                        "historical_uid_mapping_verified": True,
                        "nested_json_owner_verified": True,
                        "multi_batch_deletion_verified": True,
                        "shared_reference_blocked": True,
                        "lifecycle_effects": "synthetic stub; installed lifecycle not qualified",
                        "source_sha256": {
                            path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
                            for path in (
                                "backend/storage/user_deletion.py",
                                "backend/storage/knowledge_ownership.py",
                                "backend/storage/retention.py",
                            )
                        },
                    },
                    indent=2,
                )
            )
    finally:
        chroma.close()
        graph.close()
        engine.dispose()


if __name__ == "__main__":
    main()
