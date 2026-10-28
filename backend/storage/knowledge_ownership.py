"""Resolve historical ingested ownership without guessing across principals."""

from __future__ import annotations

from dataclasses import dataclass
import json

from sqlalchemy import select

from backend.storage.retention import (
    DeletionSubject,
    RetentionDeleteError,
    scoped_deletion_subject,
)


def _mapping(value):
    if value is None:
        return {}
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError) as exc:
            raise RetentionDeleteError("knowledge_ownership_metadata_invalid") from exc
    if not isinstance(value, dict):
        raise RetentionDeleteError("knowledge_ownership_metadata_invalid")
    return value


def _identity(value):
    if value is None or value == "":
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise RetentionDeleteError("knowledge_ownership_identity_invalid")
    return str(value)


def ownership_ids(metadata):
    """Read scalar and historical JSON ownership; never parse executable data."""
    root = _mapping(metadata)
    sources = [root]
    for key in ("node_metadata", "metadata"):
        if key in root:
            sources.append(_mapping(root[key]))
    owners = set()
    tenants = set()
    for source in list(sources):
        if "permissions" in source:
            sources.append(_mapping(source["permissions"]))
    for source in sources:
        for key in ("user_id", "owner_user_id"):
            value = _identity(source.get(key))
            if value is not None:
                owners.add(value)
        value = _identity(source.get("tenant_id"))
        if value is not None:
            tenants.add(value)
    return owners, tenants


def ownership_matches(metadata, subject: DeletionSubject, *, authoritative=False):
    subject = scoped_deletion_subject(subject)
    owners, tenants = ownership_ids(metadata)
    values = owners if subject.subject_type == "user" else tenants
    matches = subject.subject_id in values
    if (matches and len(values) > 1) or (
        authoritative and values and values != {subject.subject_id}
    ):
        raise RetentionDeleteError("knowledge_ownership_conflict")
    return matches or authoritative


@dataclass(frozen=True)
class KnowledgeOwnershipPlan:
    primary_ids: frozenset
    uids: frozenset[str]


def build_knowledge_ownership_plan(session, metadata, subject):
    """Preflight selected nodes and reject cross-owner shared references."""
    subject = scoped_deletion_subject(subject)
    nodes = metadata.tables.get("ukg_knowledge_nodes")
    if nodes is None:
        return KnowledgeOwnershipPlan(frozenset(), frozenset())
    keys = list(nodes.primary_key.columns)
    if len(keys) != 1 or "node_metadata" not in nodes.c:
        raise RetentionDeleteError("knowledge_ownership_schema_invalid")
    references = {}
    chunks = metadata.tables.get("ingestion_chunks")
    jobs = metadata.tables.get("ingestion_jobs")
    if chunks is not None and jobs is not None:
        if not {"node_uid", "job_id"}.issubset(chunks.c.keys()) or not {
            "id",
            "user_id",
            "tenant_id",
        }.issubset(jobs.c.keys()):
            raise RetentionDeleteError("knowledge_ownership_schema_invalid")
        rows = session.execute(
            select(chunks.c.node_uid, jobs.c.user_id, jobs.c.tenant_id).join(
                jobs, chunks.c.job_id == jobs.c.id
            )
        ).yield_per(500)
        try:
            for uid, owner, tenant in rows:
                reference = references.setdefault(str(uid), (set(), set()))
                reference[0].add(_identity(owner))
                reference[1].add(_identity(tenant))
        finally:
            rows.close()
    columns = [keys[0], nodes.c.node_metadata]
    for name in ("uid", "node_id", "tenant_id"):
        if name in nodes.c:
            columns.append(nodes.c[name])
    rows = session.execute(select(*columns)).yield_per(500)
    primary_ids = set()
    uids = set()
    try:
        for row in rows.mappings():
            uid = _identity(row.get("uid"))
            reference = references.get(uid, (set(), set()))
            scopes = reference[0] if subject.subject_type == "user" else reference[1]
            referenced = subject.subject_id in scopes
            selected = ownership_matches(
                {
                    "node_metadata": row["node_metadata"],
                    "tenant_id": row.get("tenant_id"),
                },
                subject,
                authoritative=referenced,
            )
            if not selected:
                continue
            if any(value != subject.subject_id for value in scopes):
                raise RetentionDeleteError("knowledge_ownership_shared_reference")
            primary_ids.add(row[keys[0].name])
            for name in ("uid", "node_id"):
                value = _identity(row.get(name))
                if value is not None:
                    uids.add(value)
    finally:
        rows.close()
    return KnowledgeOwnershipPlan(frozenset(primary_ids), frozenset(uids))
