"""Queued work must not restore knowledge after an ownership deletion."""

import hashlib
import hmac
from types import SimpleNamespace

import pytest

from backend.storage.materialization_dispatcher import CrossStoreMaterializationDispatcher
from backend.storage.outbox import CrossStoreOutbox
from extensions import db
from models import DataDeletionTombstone, KnowledgeGraphNode
from tests.conftest import create_test_user


@pytest.mark.parametrize("destination",["chroma","neo4j"])
@pytest.mark.parametrize("state",["retained","deleted","deletion_requested"])
def test_owned_queue_resolves_current_source_and_respects_deletion(app,monkeypatch,destination,state):
    calls=[]
    monkeypatch.setattr("backend.services.rag_service.get_rag_service",
        lambda:SimpleNamespace(ingest_knowledge_node=lambda *args:calls.append(args) or True))
    monkeypatch.setattr("backend.storage.get_graph_store",
        lambda:SimpleNamespace(connect=lambda:None, merge_knowledge_node=lambda properties:calls.append(properties) or True))
    with app.app_context():
        owner=create_test_user(username="owned-queue-user",email="owned-queue@example.com",password="SecureTest789$#@")
        node=KnowledgeGraphNode(uid="owned-uid",node_id="OWNED",node_type="ingested_document_chunk",
            content="current authoritative content",node_metadata={"permissions":{"owner_user_id":owner},"source_revision":"rev1"})
        db.session.add(node); db.session.commit()
        CrossStoreOutbox(db.session).enqueue(entity_type="knowledge_graph_node",entity_id="owned-uid",
            destination=destination,operation="upsert_knowledge_node" if destination=="chroma" else "merge_knowledge_node",
            schema_version="knowledge-node.v1",source_revision="rev1",correlation_id="synthetic",
            payload={"node_uid":"owned-uid","content":"stale queued content","properties":{"content":"stale queued content"}})
        db.session.commit()
        if state=="deleted":
            db.session.delete(node); db.session.commit()
        elif state=="deletion_requested":
            runtime=app.extensions["dle_runtime"]; identity=runtime.ownership.identity
            key=identity.installation_id if identity is not None else runtime.instance_id
            digest=hmac.new(str(key).encode(),f"user:{owner}".encode(),hashlib.sha256).hexdigest()
            db.session.add(DataDeletionTombstone(subject_type="user",subject_digest=digest,
                policy_version="test",status="partial_failure",store_status={}))
            db.session.commit()
        result=CrossStoreMaterializationDispatcher(db.session).run_once()
        if state=="retained":
            assert result["succeeded"]==1 and len(calls)==1
            if destination=="chroma":
                assert calls[0][1]=="current authoritative content"
                assert str(calls[0][3]["user_id"])==str(owner)
            else:
                assert calls[0]["content"]=="current authoritative content"
                assert str(calls[0]["user_id"])==str(owner)
        else:
            assert calls==[]
            assert result["failed"]==(1 if state=="deletion_requested" else 0)
