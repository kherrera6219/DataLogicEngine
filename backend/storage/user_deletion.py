"""Concrete user/tenant deletion adapters for every retained Phase 4 store."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
from typing import Any

from sqlalchemy import delete, or_, select, update

from backend.storage.chroma_security import safe_get_collection
from backend.storage.knowledge_ownership import build_knowledge_ownership_plan, ownership_matches

from backend.storage.retention import (
    DeleteResult,
    DeletionSubject,
    RetentionDeleteCoordinator,
    RetentionDeleteError,
    scoped_deletion_subject,
)


AUDIT_RETENTION_TABLES = {
    "audit_logs",
    "feature_flag_audit_events",
    "truth_audit_events",
    "data_deletion_tombstones",
}
REQUIRED_DELETE_STORES = (
    "postgresql",
    "neo4j",
    "chroma",
    "redis",
    "minio",
    "local_json",
    "logs",
)


class PostgreSQLUserDeletionAdapter:
    def __init__(self, session, metadata):
        self.session = session
        self.metadata = metadata

    @staticmethod
    def _primary_key(table):
        columns = list(table.primary_key.columns)
        return columns[0] if len(columns) == 1 else None

    def _targets(self, subject: DeletionSubject):
        subject = scoped_deletion_subject(subject)
        knowledge = build_knowledge_ownership_plan(self.session, self.metadata, subject)
        selected: dict[Any, set[Any]] = {}
        depth: dict[Any, int] = {}
        if knowledge.primary_ids:
            table = self.metadata.tables["ukg_knowledge_nodes"]
            selected[table] = set(knowledge.primary_ids)
            depth[table] = 0
        for table in self.metadata.tables.values():
            if table.name in AUDIT_RETENTION_TABLES:
                continue
            primary_key = self._primary_key(table)
            if primary_key is None:
                continue
            conditions = []
            if subject.subject_type == "user" and "user_id" in table.c:
                conditions.append(table.c.user_id == subject.subject_id)
            if subject.tenant_id and "tenant_id" in table.c:
                conditions.append(table.c.tenant_id == subject.tenant_id)
            if subject.subject_type == "user" and table.name == "users":
                conditions.append(primary_key == subject.subject_id)
            if not conditions:
                continue
            values = set(
                self.session.execute(select(primary_key).where(or_(*conditions))).scalars()
            )
            if values:
                selected.setdefault(table,set()).update(values)
                depth[table] = 0

        changed = True
        while changed:
            changed = False
            for child in self.metadata.tables.values():
                if child.name in AUDIT_RETENTION_TABLES:
                    continue
                child_pk = self._primary_key(child)
                if child_pk is None:
                    continue
                for foreign_key in child.foreign_keys:
                    parent = foreign_key.column.table
                    parent_ids = selected.get(parent)
                    parent_pk = self._primary_key(parent)
                    if not parent_ids or parent_pk is None:
                        continue
                    referenced_values = self.session.execute(
                        select(foreign_key.column).where(parent_pk.in_(parent_ids))
                    ).scalars()
                    referenced_values = {value for value in referenced_values if value is not None}
                    if not referenced_values:
                        continue
                    child_ids = set(
                        self.session.execute(
                            select(child_pk).where(foreign_key.parent.in_(referenced_values))
                        ).scalars()
                    )
                    existing = selected.setdefault(child, set())
                    before = len(existing)
                    existing.update(child_ids)
                    if len(existing) != before:
                        depth[child] = max(depth.get(child, 0), depth.get(parent, 0) + 1)
                        changed = True
        return selected, depth

    def delete(self, subject: DeletionSubject) -> DeleteResult:
        subject = scoped_deletion_subject(subject)
        selected, depth = self._targets(subject)
        deleted_count = 0

        # Audit records retain only their policy-approved content; detach any
        # nullable relational user pointer before deleting the identity row.
        for table in self.metadata.tables.values():
            if table.name not in AUDIT_RETENTION_TABLES or "user_id" not in table.c:
                continue
            if table.c.user_id.nullable:
                self.session.execute(
                    update(table)
                    .where(table.c.user_id == subject.subject_id)
                    .values(user_id=None)
                )

        # Break nullable cycles before deleting deepest dependent records.
        for table, ids in selected.items():
            primary_key = self._primary_key(table)
            nullable_foreign_keys = {
                foreign_key.parent.name: None
                for foreign_key in table.foreign_keys
                if foreign_key.parent.nullable and foreign_key.column.table in selected
            }
            if primary_key is not None and nullable_foreign_keys:
                self.session.execute(
                    update(table).where(primary_key.in_(ids)).values(**nullable_foreign_keys)
                )

        # Remove cross-store envelopes whose entity IDs refer to deleted rows.
        entity_ids: set[str] = set()
        for table, ids in selected.items():
            primary_key = self._primary_key(table)
            candidate_columns = [
                column
                for column in table.c
                if column.name == primary_key.name
                or column.name in {"uid", "session_id", "run_id", "event_id", "artifact_id"}
            ]
            if primary_key is None:
                continue
            for row in self.session.execute(
                select(*candidate_columns).where(primary_key.in_(ids))
            ):
                entity_ids.update(str(value) for value in row if value is not None)
        if entity_ids:
            for name in ("cross_store_materialization_states", "cross_store_outbox_events"):
                table = self.metadata.tables[name]
                result = self.session.execute(delete(table).where(table.c.entity_id.in_(entity_ids)))
                deleted_count += int(result.rowcount or 0)

        for table in sorted(selected, key=lambda item: depth.get(item, 0), reverse=True):
            primary_key = self._primary_key(table)
            result = self.session.execute(delete(table).where(primary_key.in_(selected[table])))
            deleted_count += int(result.rowcount or 0)
        return DeleteResult(deleted_count)

    def remnant_count(self, subject: DeletionSubject) -> int:
        selected, _depth = self._targets(subject)
        return sum(len(values) for values in selected.values())


class Neo4jUserDeletionAdapter:
    def __init__(self, driver, *, knowledge_uids=()):
        self.driver = driver
        self.knowledge_uids = frozenset(knowledge_uids)

    def _matching_ids(self, subject):
        subject = scoped_deletion_subject(subject)
        ids=[]
        with self.driver.session() as session:
            rows=session.run(
                "MATCH (n) RETURN elementId(n) AS element_id, "
                "{uid:n[$ownership_keys[0]],node_id:n[$ownership_keys[1]],user_id:n[$ownership_keys[2]],"
                "owner_user_id:n[$ownership_keys[3]],tenant_id:n[$ownership_keys[4]],permissions:n[$ownership_keys[5]],"
                "node_metadata:n[$ownership_keys[6]],metadata:n[$ownership_keys[7]]} AS properties",
                ownership_keys=["uid","node_id","user_id","owner_user_id","tenant_id","permissions","node_metadata","metadata"],
            )
            for row in rows:
                properties=row["properties"]
                if not isinstance(properties,dict) or not isinstance(row["element_id"],str):
                    raise RetentionDeleteError("neo4j_deletion_lookup_invalid")
                known=any(properties.get(key) in self.knowledge_uids for key in ("uid","node_id"))
                if ownership_matches(properties,subject,authoritative=known):
                    ids.append(row["element_id"])
        return ids

    def delete(self, subject):
        ids=self._matching_ids(subject)
        deleted=0
        with self.driver.session() as session:
            for start in range(0,len(ids),500):
                record=session.run(
                    "MATCH (n) WHERE elementId(n) IN $element_ids "
                    "WITH collect(n) AS nodes FOREACH (node IN nodes | DETACH DELETE node) "
                    "RETURN size(nodes) AS count",element_ids=ids[start:start+500],
                ).single()
                if record is None:
                    raise RetentionDeleteError("neo4j_deletion_unverified")
                deleted+=int(record["count"])
        return DeleteResult(deleted)

    def remnant_count(self, subject):
        return len(self._matching_ids(subject))


class ChromaUserDeletionAdapter:
    def __init__(self, client, *, knowledge_uids=()):
        self.client = client
        self.knowledge_uids = frozenset(knowledge_uids)

    def _matching_ids(self, subject):
        subject = scoped_deletion_subject(subject)
        matches: dict[str, set[str]] = {}
        try:
            offset=0; seen_collections=set()
            while True:
                collections=self.client.list_collections(limit=100,offset=offset)
                for listed in collections:
                    name=str(listed if isinstance(listed,str) else listed.name)
                    if name in seen_collections:
                        raise RetentionDeleteError("chroma_deletion_inventory_unstable")
                    seen_collections.add(name)
                    collection=safe_get_collection(self.client,name=name)
                    ids=set(); seen_ids=set(); row_offset=0
                    while True:
                        page=collection.get(limit=500,offset=row_offset,include=["metadatas"])
                        page_ids=page.get("ids"); metas=page.get("metadatas")
                        if not isinstance(page_ids,list) or not isinstance(metas,list) or len(page_ids)!=len(metas):
                            raise RetentionDeleteError("chroma_deletion_lookup_invalid")
                        for item_id,meta in zip(page_ids,metas):
                            if not isinstance(item_id,str) or item_id in seen_ids or not isinstance(meta,(dict,type(None))):
                                raise RetentionDeleteError("chroma_deletion_lookup_invalid")
                            seen_ids.add(item_id)
                            meta=meta or {}
                            known=item_id in self.knowledge_uids or any(meta.get(key) in self.knowledge_uids
                                for key in ("vector_parent_id","node_uid","node_id"))
                            if ownership_matches(meta,subject,authoritative=known):ids.add(item_id)
                        if len(page_ids)<500:break
                        row_offset+=500
                    if ids:matches[name]=ids
                if len(collections)<100:break
                offset+=100
        except RetentionDeleteError:
            raise
        except Exception as exc:
            raise RetentionDeleteError("chroma_deletion_lookup_failed") from exc
        return matches

    def delete(self, subject):
        matches = self._matching_ids(subject)
        for name, ids in matches.items():
            ordered=sorted(ids)
            for start in range(0,len(ordered),500):
                safe_get_collection(self.client, name=name).delete(ids=ordered[start:start+500])
        return DeleteResult(sum(len(ids) for ids in matches.values()))

    def remnant_count(self, subject):
        return sum(len(ids) for ids in self._matching_ids(subject).values())


class RedisUserDeletionAdapter:
    def __init__(self, client):
        self.client = client

    @staticmethod
    def _matches(key: bytes, subject: DeletionSubject) -> bool:
        decoded = key.decode("utf-8", errors="ignore")
        tokens = {token for token in re.split(r"[^A-Za-z0-9_.-]+", decoded) if token}
        return str(subject.subject_id) in tokens or bool(subject.tenant_id and subject.tenant_id in tokens)

    def _keys(self, subject):
        return [
            key if isinstance(key, bytes) else str(key).encode()
            for key in self.client.scan_iter(match="*")
            if self._matches(key if isinstance(key, bytes) else str(key).encode(), subject)
        ]

    def delete(self, subject):
        keys = self._keys(subject)
        deleted = int(self.client.delete(*keys)) if keys else 0
        return DeleteResult(deleted)

    def remnant_count(self, subject):
        return len(self._keys(subject))


class MinIOUserDeletionAdapter:
    def __init__(self, store, buckets):
        self.store = store
        self.buckets = tuple(buckets)

    def _objects(self, subject):
        found = []
        for bucket in self.buckets:
            for item in self.store.list(bucket):
                info = self.store.get_info(bucket, item.key) or item
                metadata = {str(key): str(value) for key, value in (info.metadata or {}).items()}
                if metadata.get("user_id") == str(subject.subject_id) or (
                    subject.tenant_id and metadata.get("tenant_id") == str(subject.tenant_id)
                ):
                    found.append((bucket, item.key))
        return found

    def delete(self, subject):
        found = self._objects(subject)
        deleted = sum(1 for bucket, key in found if self.store.delete(bucket, key))
        return DeleteResult(deleted)

    def remnant_count(self, subject):
        return len(self._objects(subject))


class LocalJsonUserDeletionAdapter:
    def __init__(self, path: Path):
        self.path = path

    def _load(self):
        if not self.path.is_file():
            return None
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else None

    @staticmethod
    def _matches(vertex, subject):
        metadata = vertex.get("metadata") if isinstance(vertex, dict) else {}
        metadata = metadata if isinstance(metadata, dict) else {}
        return str(metadata.get("user_id")) == str(subject.subject_id) or bool(
            subject.tenant_id and str(metadata.get("tenant_id")) == str(subject.tenant_id)
        )

    def delete(self, subject):
        payload = self._load()
        if payload is None:
            return DeleteResult(0)
        removed_ids = {
            str(vertex.get("vertex_id"))
            for vertex in payload.get("vertices", [])
            if self._matches(vertex, subject)
        }
        payload["vertices"] = [
            vertex
            for vertex in payload.get("vertices", [])
            if str(vertex.get("vertex_id")) not in removed_ids
        ]
        before_edges = len(payload.get("edges", []))
        payload["edges"] = [
            edge
            for edge in payload.get("edges", [])
            if str(edge.get("source_id")) not in removed_ids
            and str(edge.get("target_id")) not in removed_ids
        ]
        if removed_ids:
            temporary = self.path.with_suffix(self.path.suffix + ".tmp")
            try:
                with temporary.open("w", encoding="utf-8", newline="\n") as handle:
                    handle.write(json.dumps(payload, sort_keys=True, indent=2) + "\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, self.path)
            finally:
                temporary.unlink(missing_ok=True)
        return DeleteResult(len(removed_ids) + before_edges - len(payload["edges"]))

    def remnant_count(self, subject):
        payload = self._load() or {}
        return sum(1 for vertex in payload.get("vertices", []) if self._matches(vertex, subject))


class LogUserDeletionAdapter:
    def __init__(self, root: Path):
        self.root = root

    @staticmethod
    def _needles(subject):
        return [
            value.encode("utf-8")
            for value in (str(subject.subject_id), str(subject.tenant_id or ""))
            if value
        ]

    def delete(self, subject):
        deleted_lines = 0
        for path in self.root.rglob("*.log") if self.root.exists() else ():
            try:
                lines = path.read_bytes().splitlines(keepends=True)
            except OSError:
                continue
            needles = self._needles(subject)
            retained = [line for line in lines if not any(needle in line for needle in needles)]
            if len(retained) == len(lines):
                continue
            temporary = path.with_suffix(path.suffix + ".tmp")
            try:
                with temporary.open("wb") as handle:
                    handle.writelines(retained)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, path)
            finally:
                temporary.unlink(missing_ok=True)
            deleted_lines += len(lines) - len(retained)
        return DeleteResult(deleted_lines)

    def remnant_count(self, subject):
        needles = self._needles(subject)
        count = 0
        for path in self.root.rglob("*.log") if self.root.exists() else ():
            try:
                data = path.read_bytes()
            except OSError:
                continue
            count += sum(data.count(needle) for needle in needles)
        return count


class NoOpDeletionAdapter:
    def delete(self, _subject):
        return DeleteResult(0)

    def remnant_count(self, _subject):
        return 0


class DeletionResources:
    def __init__(self):
        self.resources = []

    def own(self, value):
        self.resources.append(value)
        return value

    def close(self):
        for value in reversed(self.resources):
            close = getattr(value, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:
                    continue


def run_user_deletion(app, subject: DeletionSubject):
    """Serialize profile deletion with chat indexing and session retention."""
    from backend.storage.chat_index_coordination import ChatIndexLockError, chat_index_guard

    runtime = app.extensions["dle_runtime"]
    subject = scoped_deletion_subject(subject)
    try:
        with chat_index_guard(runtime.runtime_root):
            return _run_user_deletion_locked(app, subject)
    except ChatIndexLockError as exc:
        raise RetentionDeleteError("chat_index_lock_unavailable") from exc


def _run_user_deletion_locked(app, subject: DeletionSubject):
    from extensions import db
    from backend.storage.connection_manager import get_connection_manager

    runtime = app.extensions["dle_runtime"]
    knowledge=build_knowledge_ownership_plan(db.session,db.metadata,subject)
    adapters = {
        "postgresql": PostgreSQLUserDeletionAdapter(db.session, db.metadata),
        "local_json": LocalJsonUserDeletionAdapter(
            runtime.runtime_root / "databases" / "memory" / "memory_graph.json"
        ),
        "logs": LogUserDeletionAdapter(runtime.runtime_root / "logs"),
    }
    resources = DeletionResources()
    try:
        if app.config.get("DLE_DATA_PLANE_DRIVER") == "podman":
            import redis
            from neo4j import GraphDatabase
            from backend.storage.chroma_http import ChromaHttpClient
            from backend.storage.object_store import get_object_store

            settings = app.extensions["dle_data_plane_manager"].connection_settings()
            adapters.update(
                {
                    "redis": RedisUserDeletionAdapter(
                        resources.own(redis.Redis.from_url(settings["redis_url"]))
                    ),
                    "neo4j": Neo4jUserDeletionAdapter(
                        resources.own(
                            GraphDatabase.driver(
                                settings["neo4j_uri"],
                                auth=(settings["neo4j_user"], settings["neo4j_password"]),
                            )
                        ), knowledge_uids=knowledge.uids,
                    ),
                    "chroma": ChromaUserDeletionAdapter(
                        resources.own(
                            ChromaHttpClient(
                                host=settings["chroma_host"],
                                port=settings["chroma_port"],
                            )
                        ), knowledge_uids=knowledge.uids,
                    ),
                    "minio": MinIOUserDeletionAdapter(
                        get_object_store(), settings["object_buckets"]
                    ),
                }
            )
        else:
            # Development/test profiles have no required external stores. The
            # filesystem object backend is not authoritative for user records.
            for store in ("redis", "neo4j", "chroma", "minio"):
                adapters[store] = NoOpDeletionAdapter()
            get_connection_manager()
        identity = runtime.ownership.identity
        digest_key = identity.installation_id if identity is not None else runtime.instance_id
        return RetentionDeleteCoordinator(
            session=db.session,
            adapters=adapters,
            required_stores=REQUIRED_DELETE_STORES,
            digest_key=digest_key,
        ).run(subject)
    finally:
        resources.close()
