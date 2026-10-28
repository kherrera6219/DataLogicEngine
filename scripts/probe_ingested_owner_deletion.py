"""Read-only-to-customer-data reproduction of nested ownership deletion gaps."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from sqlalchemy import (
    Column,
    Integer,
    JSON,
    MetaData,
    String,
    Table,
    create_engine,
    func,
    select,
)
from sqlalchemy.orm import Session

from backend.services.rag_service import RAGService
from backend.storage.retention import DeletionSubject
from backend.storage.user_deletion import (
    ChromaUserDeletionAdapter,
    PostgreSQLUserDeletionAdapter,
)


def main():
    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()
    users = Table("users", metadata, Column("id", Integer, primary_key=True))
    nodes = Table(
        "ukg_knowledge_nodes",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("node_metadata", JSON),
        Column("tenant_id", String),
        Column("content", String),
    )
    for name in ("cross_store_materialization_states", "cross_store_outbox_events"):
        Table(
            name,
            metadata,
            Column("id", Integer, primary_key=True),
            Column("entity_id", String),
        )
    metadata.create_all(engine)
    subject = DeletionSubject("user", "1")
    try:
        with Session(engine) as session:
            session.execute(users.insert(), {"id": 1})
            session.execute(
                nodes.insert(),
                {
                    "id": 1,
                    "node_metadata": {"permissions": {"owner_user_id": 1}},
                    "content": "synthetic owned content",
                },
            )
            session.commit()
            adapter = PostgreSQLUserDeletionAdapter(session, metadata)
            adapter.delete(subject)
            reported = adapter.remnant_count(subject)
            actual = session.scalar(select(func.count()).select_from(nodes))

        class Collection:
            def __init__(self):
                self.rows = {
                    "synthetic-node": RAGService._metadata_for_chroma(
                        {"permissions": {"owner_user_id": 1}}
                    )
                }

            def get(self, where=None, *, limit=500, offset=0, include=None):
                selected = list(self.rows.items())
                if where:
                    key, value = next(iter(where.items()))
                    selected = [
                        (item, meta)
                        for item, meta in selected
                        if meta.get(key) == value
                    ]
                selected = selected[offset : offset + limit]
                return {
                    "ids": [item for item, _ in selected],
                    "metadatas": [meta for _, meta in selected],
                }

            def delete(self, ids):
                for item in ids:
                    self.rows.pop(item, None)

        class Client:
            def __init__(self):
                self.collection = Collection()

            def list_collections(self, limit=100, offset=0):
                return [SimpleNamespace(name="knowledge_nodes")][
                    offset : offset + limit
                ]

            def get_collection(self, **kwargs):
                return self.collection

        client = Client()
        adapter = ChromaUserDeletionAdapter(client)
        adapter.delete(subject)
        vector_reported = adapter.remnant_count(subject)
        vector_actual = len(client.collection.rows)
        print(
            json.dumps(
                {
                    "status": "finding_reproduced"
                    if reported == 0
                    and actual
                    and vector_reported == 0
                    and vector_actual
                    else "finding_not_reproduced",
                    "synthetic_only": True,
                    "relational_probe": "PostgreSQL adapter logic on disposable SQLite",
                    "vector_probe": "Chroma adapter with synthetic collection transport",
                    "relational_reported_remnants": reported,
                    "relational_actual_remnants": actual,
                    "vector_reported_remnants": vector_reported,
                    "vector_actual_remnants": vector_actual,
                    "source_sha256": {
                        name: hashlib.sha256(Path(name).read_bytes()).hexdigest()
                        for name in (
                            "backend/storage/user_deletion.py",
                            "backend/services/rag_service.py",
                        )
                    },
                },
                indent=2,
            )
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
