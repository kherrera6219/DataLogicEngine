"""Exercise SQL source eligibility using an isolated in-memory database."""

import hashlib
import hmac

import pytest
from sqlalchemy import JSON, Column, Integer, String, Text, create_engine
from sqlalchemy.orm import Session, declarative_base

import models
from backend.storage.semantic_sql_migration import SemanticMigrationError, _source

Base = declarative_base()


class Job(Base):
    __tablename__ = "job"
    id = Column(Integer, primary_key=True)
    status = Column(String)
    user_id = Column(Integer)
    tenant_id = Column(String)


class File(Base):
    __tablename__ = "file"
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer)
    status = Column(String)
    object_status = Column(String)
    normalized_object_status = Column(String)
    defense_result = Column(JSON)


class Chunk(Base):
    __tablename__ = "chunk"
    id = Column(Integer, primary_key=True)
    file_id = Column(Integer)
    job_id = Column(Integer)
    node_uid = Column(String)
    source_revision = Column(String)
    chunk_sha256 = Column(String)
    materialization_state = Column(String)
    chunk_index = Column(Integer)
    chunk_count = Column(Integer)


class Node(Base):
    __tablename__ = "node"
    id = Column(Integer, primary_key=True)
    uid = Column(String)
    node_id = Column(String)
    content = Column(Text)
    node_type = Column(String)
    title = Column(String)
    label = Column(String)
    node_metadata = Column(JSON)
    tenant_id = Column(String)


class Tombstone(Base):
    __tablename__ = "tombstone"
    deletion_id = Column(Integer, primary_key=True)
    subject_type = Column(String)
    subject_digest = Column(String)


@pytest.fixture
def authority(monkeypatch):
    for name, cls in [
        ("IngestionJob", Job),
        ("IngestionFile", File),
        ("IngestionChunk", Chunk),
        ("KnowledgeGraphNode", Node),
        ("DataDeletionTombstone", Tombstone),
    ]:
        monkeypatch.setattr(models, name, cls)
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all(
            [
                Job(id=1, status="completed", user_id=7, tenant_id="tenant"),
                File(
                    id=1,
                    job_id=1,
                    status="ready",
                    object_status="ready",
                    normalized_object_status="ready",
                    defense_result={
                        "policy_version": "content-defense.v1",
                        "safe_for_retrieval": True,
                    },
                ),
                Chunk(
                    id=1,
                    job_id=1,
                    file_id=1,
                    node_uid="ki_1",
                    source_revision="rev",
                    chunk_sha256=hashlib.sha256(b"evidence").hexdigest(),
                    materialization_state="ready",
                    chunk_index=0,
                    chunk_count=1,
                ),
                Node(
                    id=1,
                    uid="ki_1",
                    node_id="n",
                    content="evidence",
                    node_type="document",
                    tenant_id="tenant",
                    node_metadata={"source_revision": "rev", "user_id": 7},
                ),
            ]
        )
        session.commit()
        yield session
    engine.dispose()


def test_sql_source_uses_sql_content_and_authority(authority):
    result = _source(authority, "knowledge", 1, "key")
    assert result["text"] == "evidence"
    assert result["metadata"]["source_revision"] == "rev"
    assert result["metadata"]["user_id"] == 7


@pytest.mark.parametrize(
    "condition", ["hash", "revision", "owner", "object", "defense", "tombstone"]
)
def test_sql_authority_rejects_ineligible_or_deleted_source(authority, condition):
    if condition == "hash":
        authority.get(Node, 1).content = "tampered"
    elif condition == "revision":
        authority.get(Node, 1).node_metadata = {
            "source_revision": "stale",
            "user_id": 7,
        }
    elif condition == "owner":
        authority.get(Node, 1).node_metadata = {"source_revision": "rev", "user_id": 8}
    elif condition == "object":
        authority.get(File, 1).normalized_object_status = "pending"
    elif condition == "defense":
        authority.get(File, 1).defense_result = {
            "policy_version": "content-defense.v1",
            "safe_for_retrieval": False,
        }
    else:
        digest = hmac.new(b"key", b"user:7", hashlib.sha256).hexdigest()
        authority.add(
            Tombstone(deletion_id=1, subject_type="user", subject_digest=digest)
        )
    authority.commit()
    with pytest.raises(SemanticMigrationError):
        _source(authority, "knowledge", 1, "key")
