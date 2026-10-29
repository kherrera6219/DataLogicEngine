"""R-3 qualification: exercise actual RAG writes/search against SQL authority.

These characterize the activation blocker; rejection is the safe current
behavior, not acceptance of the semantic migration.
"""

from types import SimpleNamespace

import pytest

from backend.governed_execution.retrieval import retrieve_evidence
from extensions import db
from models import KnowledgeGraphNode
from tests.governed_execution.test_phase9_retrieval_authority import (
    _authority,
    _request,
)
from tests.unit.test_model_aware_rag_writes import _service


def _round_trip(app, tmp_path, monkeypatch, text):
    service, store = _service(tmp_path)
    job, source_file, chunk, item = _authority(app, text)
    chunk.chunk_index = 7
    chunk.chunk_count = 12
    db.session.add(KnowledgeGraphNode(uid=chunk.node_uid, content=text))
    db.session.commit()
    metadata = {
        **item["metadata"],
        "node_id": chunk.node_uid,
        "chunk_index": 7,
        "chunk_count": 12,
    }
    assert service.ingest_knowledge_node(chunk.node_uid, text, "policy", metadata)

    def search(*, collection, query_embedding, k, filters):
        return [
            SimpleNamespace(id=item_id, text=row[0], score=0.95, metadata=row[2])
            for (name, item_id), row in store.rows.items()
            if name == collection
        ][:k]

    monkeypatch.setattr(store, "search", search, raising=False)
    return service, store, job, source_file, chunk


def test_unsplit_model_knowledge_retains_sql_eligibility(app, tmp_path, monkeypatch):
    with app.app_context():
        service, _store, _job, _file, chunk = _round_trip(
            app, tmp_path, monkeypatch, "approved local evidence"
        )
        evidence, warnings = retrieve_evidence(
            _request(), "policy", rag_service=service
        )
        assert warnings == []
        assert len(evidence) == 1
        assert evidence[0].source_id == chunk.node_uid
        assert evidence[0].text == "approved local evidence"


def test_split_model_knowledge_is_not_yet_eligible(app, tmp_path, monkeypatch):
    with app.app_context():
        text = " ".join(f"unique{i}" for i in range(40))
        service, store, _job, _file, chunk = _round_trip(
            app, tmp_path, monkeypatch, text
        )
        assert len(store.rows) > 1
        # Replay the pre-repair model-vector format: it carried neither span
        # proof nor separate canonical and vector chunk indexes. Keep the
        # original failure expectations for this unsafe legacy representation.
        for index, (_, _, metadata) in enumerate(store.rows.values()):
            for field in (
                "source_span_start",
                "source_span_end",
                "source_span_sha256",
                "source_parent_sha256",
                "vector_chunk_index",
                "vector_chunk_count",
                "vector_parent_id",
            ):
                metadata.pop(field, None)
            metadata["chunk_index"] = index
            metadata["chunk_count"] = len(store.rows)
        request = _request()
        evidence, warnings = retrieve_evidence(request, "policy", rag_service=service)
        assert evidence == []
        assert (
            f"ingestion_source_rejected:{chunk.node_uid}:content_hash_mismatch"
            in warnings
        )
        assert (
            f"ingestion_source_rejected:{chunk.node_uid}:chunk:1:postgresql_revision_not_eligible"
            in warnings
        )
        assert all(
            d["disposition"] == "rejected"
            for d in request.metadata["_retrieval_decisions"]
        )
        hits = service.search_knowledge("policy")
        # Current vector locators overwrite canonical ingestion chunk positions.
        assert hits[0]["citation"]["locator"]["chunk_index"] == 0
        assert hits[0]["citation"]["locator"]["chunk_count"] != 12
        assert all("source_span_start" not in hit["metadata"] for hit in hits)


@pytest.mark.parametrize(
    "condition,reason",
    [
        ("pending_job", "postgresql_revision_not_eligible"),
        ("missing_original", "postgresql_revision_not_eligible"),
        ("missing_normalized", "postgresql_revision_not_eligible"),
        ("pending_chunk", "postgresql_revision_not_eligible"),
        ("unsafe_content", "content_defense_not_approved"),
        ("wrong_tenant", "tenant_permission_denied"),
    ],
)
def test_model_round_trip_preserves_authority_rejection(
    app, tmp_path, monkeypatch, condition, reason
):
    with app.app_context():
        service, _store, job, source_file, chunk = _round_trip(
            app, tmp_path, monkeypatch, "approved local evidence"
        )
        if condition == "pending_job":
            job.status = "materialization_pending"
        elif condition == "missing_original":
            source_file.object_status = "pending"
        elif condition == "missing_normalized":
            source_file.normalized_object_status = "pending"
        elif condition == "pending_chunk":
            chunk.materialization_state = "pending"
        elif condition == "unsafe_content":
            source_file.defense_result = {"safe_for_retrieval": False}
        elif condition == "wrong_tenant":
            job.tenant_id = "another-tenant"
        db.session.commit()
        evidence, warnings = retrieve_evidence(
            _request(), "policy", rag_service=service
        )
        assert evidence == []
        assert f"ingestion_source_rejected:{chunk.node_uid}:{reason}" in warnings
