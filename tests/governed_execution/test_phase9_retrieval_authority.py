from datetime import UTC, datetime
from hashlib import sha256

from backend.governed_execution.contracts import GovernedRequest
from backend.governed_execution.retrieval import retrieve_evidence
from backend.services.rag_service import RAGService
from extensions import db
from models import IngestionChunk, IngestionFile, IngestionJob


class IngestionRag:
    SUSPICIOUS_RETRIEVAL_MARKERS = ()

    def __init__(self, item):
        self.item = item

    def search_documents(self, query, k=5):
        return []

    def search_knowledge(self, query, k=5):
        return [self.item]

    def search_user_chat_history(self, **kwargs):
        return []


def test_failed_vector_search_is_distinct_from_empty_results():
    class FailedStore:
        def search(self, **kwargs):
            raise RuntimeError("private connection details")

    request = _request()
    service = RAGService(vector_store=FailedStore(), embedding_provider=lambda _text: [0.1])
    evidence, warnings = retrieve_evidence(request, "policy", rag_service=service)
    assert evidence == []
    assert any(item.startswith("document_retrieval_failed:") for item in warnings)
    assert any(item.startswith("knowledge_retrieval_failed:") for item in warnings)
    assert all("private connection details" not in item for item in warnings)


def test_empty_vector_search_has_no_failure_warning():
    class EmptyStore:
        def search(self, **kwargs):
            return []

    service = RAGService(vector_store=EmptyStore(), embedding_provider=lambda _text: [0.1])
    evidence, warnings = retrieve_evidence(_request(), "policy", rag_service=service)
    assert evidence == []
    assert warnings == []


def _request(**metadata):
    return GovernedRequest(
        messages=[{"role": "user", "content": "What does the policy say?"}],
        metadata=metadata,
    )


def _authority(app, text="approved local evidence"):
    digest = sha256(text.encode()).hexdigest()
    revision = f"sha256:{'a' * 64}:{digest}:{digest}"
    job = IngestionJob(
        status="completed",
        source_path="C:/approved/policy.txt",
        source_digest="b" * 64,
        recursive=False,
        chunk_size=1200,
        max_file_bytes=1024,
        max_total_bytes=4096,
        max_files=1,
        current_checkpoint="completed",
        completed_at=datetime.now(UTC),
    )
    db.session.add(job)
    db.session.flush()
    source_file = IngestionFile(
        job_id=job.id,
        relative_path="policy.txt",
        source_path=job.source_path,
        document_uid="kidoc_authorized",
        source_revision=f"sha256:{'a' * 64}",
        source_sha256="a" * 64,
        status="ready",
        object_bucket="knowledge-sources",
        object_key="sources/policy/original.txt",
        object_sha256="a" * 64,
        object_status="ready",
        normalized_object_bucket="knowledge-sources",
        normalized_object_key="sources/policy/normalized.txt",
        normalized_object_sha256=digest,
        normalized_object_status="ready",
        defense_result={
            "policy_version": "content-defense.v1",
            "disposition": "approved",
            "safe_for_retrieval": True,
            "categories": [],
        },
    )
    db.session.add(source_file)
    db.session.flush()
    chunk = IngestionChunk(
        job_id=job.id,
        file_id=source_file.id,
        node_uid="ki_authorized_source",
        chunk_index=0,
        chunk_count=1,
        content_sha256=digest,
        chunk_sha256=digest,
        source_revision=revision,
        materialization_state="ready",
    )
    db.session.add(chunk)
    db.session.commit()
    item = {
        "id": chunk.node_uid,
        "text": text,
        "score": 0.95,
        "metadata": {
            "source_revision": revision,
            "content_hash": digest,
            "source_path": source_file.source_path,
        },
        "citation": {
            "source_path": source_file.source_path,
            "source_title": "Policy",
            "content_hash": digest,
            "ingestion_id": str(job.id),
        },
    }
    return job, source_file, chunk, item


def test_completed_postgresql_revision_is_selected_and_decision_is_recorded(app):
    with app.app_context():
        _job, _source_file, chunk, item = _authority(app)
        request = _request()

        evidence, warnings = retrieve_evidence(
            request, "policy", rag_service=IngestionRag(item)
        )

        assert warnings == []
        assert [record.source_id for record in evidence] == [chunk.node_uid]
        assert evidence[0].metadata["source_revision"] == chunk.source_revision
        assert request.metadata["_retrieval_decisions"] == [
            {
                "source_id": chunk.node_uid,
                "source_kind": "knowledge",
                "score": 0.95,
                "disposition": "selected",
                "reason": "eligible",
            }
        ]


def test_pending_superseded_or_tampered_ingestion_vectors_fail_closed(app):
    with app.app_context():
        job, _source_file, chunk, item = _authority(app)
        job.status = "materialization_pending"
        db.session.commit()

        request = _request()
        evidence, warnings = retrieve_evidence(
            request, "policy", rag_service=IngestionRag(item)
        )
        assert evidence == []
        assert f"ingestion_source_rejected:{chunk.node_uid}:postgresql_revision_not_eligible" in warnings

        job.status = "completed"
        db.session.commit()
        item["text"] = "tampered vector payload"
        evidence, warnings = retrieve_evidence(
            _request(), "policy", rag_service=IngestionRag(item)
        )
        assert evidence == []
        assert f"ingestion_source_rejected:{chunk.node_uid}:content_hash_mismatch" in warnings


def test_approved_graph_context_is_bounded_and_recorded(app, monkeypatch):
    class GraphStore:
        def connect(self):
            return True

        def get_knowledge_relationships(self, source_id, limit=12):
            assert source_id == "ki_authorized_source"
            assert limit == 12
            return [
                {
                    "relationship_type": "RELATED_TO",
                    "neighbor_uid": "policy-parent",
                    "neighbor_title": "Parent policy",
                    "neighbor_labels": ["KnowledgeNode"],
                }
            ]

    monkeypatch.setattr("backend.storage.get_graph_store", lambda: GraphStore())
    with app.app_context():
        _job, _source_file, _chunk, item = _authority(app)
        request = _request()
        request.constraints["use_graph_context"] = True

        evidence, warnings = retrieve_evidence(
            request, "policy", rag_service=IngestionRag(item)
        )

        assert warnings == []
        assert evidence[0].metadata["graph_context"][0]["neighbor_uid"] == "policy-parent"
        assert request.metadata["_graph_context_status"] == "relationships_included"


def test_graph_status_distinguishes_disabled_missing_and_failed(monkeypatch):
    import backend.governed_execution.retrieval as module

    monkeypatch.setattr(module, "_validate_ingestion_authority", lambda *args: ({}, None))
    item = {"id": "ki_source", "text": "approved evidence", "score": 0.9}
    service = IngestionRag(item)
    disabled = _request()
    retrieve_evidence(disabled, "evidence", rag_service=service)
    assert disabled.metadata["_graph_context_status"] == "not_enabled"

    failed = _request()
    failed.constraints["use_graph_context"] = True
    monkeypatch.setattr(module, "_load_graph_context", lambda _source: ([], "Unavailable"))
    _evidence, warnings = retrieve_evidence(failed, "evidence", rag_service=service)
    assert failed.metadata["_graph_context_status"] == "unavailable"
    assert any(item.startswith("graph_context_unavailable:") for item in warnings)

    missing = _request()
    missing.constraints["use_graph_context"] = True
    retrieve_evidence(missing, "evidence", rag_service=IngestionRag({"id": "other", "text": "evidence", "score": 0.9}))
    assert missing.metadata["_graph_context_status"] == "no_eligible_source"

    empty = _request()
    empty.constraints["use_graph_context"] = True
    monkeypatch.setattr(module, "_load_graph_context", lambda _source: ([], None))
    retrieve_evidence(empty, "evidence", rag_service=service)
    assert empty.metadata["_graph_context_status"] == "no_selected_relationships"

    retrieval_off = _request(use_rag=False)
    retrieval_off.constraints["use_graph_context"] = True
    retrieve_evidence(retrieval_off, "evidence", rag_service=service)
    assert retrieval_off.metadata["_graph_context_status"] == "retrieval_disabled"

    class FailingKnowledge(IngestionRag):
        def search_knowledge(self, query, k=5):
            raise RuntimeError("unavailable")

    unavailable = _request()
    unavailable.constraints["use_graph_context"] = True
    retrieve_evidence(unavailable, "evidence", rag_service=FailingKnowledge(item))
    assert unavailable.metadata["_graph_context_status"] == "retrieval_unavailable"


def test_graph_status_reports_partial_relationships_when_another_lookup_fails(monkeypatch):
    import backend.governed_execution.retrieval as module

    class TwoSources(IngestionRag):
        def search_knowledge(self, query, k=5):
            return [
                {"id": "ki_ok", "text": "first", "score": 0.9},
                {"id": "ki_error", "text": "second", "score": 0.8},
            ]

    monkeypatch.setattr(module, "_validate_ingestion_authority", lambda *args: ({}, None))
    monkeypatch.setattr(module, "_load_graph_context", lambda source: ([{"neighbor_uid": "x"}], None) if source == "ki_ok" else ([], "Unavailable"))
    request = _request()
    request.constraints["use_graph_context"] = True
    evidence, _warnings = retrieve_evidence(request, "evidence", rag_service=TwoSources(None))
    assert any(item.metadata.get("graph_context") for item in evidence)
    assert request.metadata["_graph_context_status"] == "partial"


def test_retrieval_applies_character_and_source_diversity_budgets():
    class MultiRag(IngestionRag):
        def __init__(self):
            self.items = [
                {"id": f"source-{index}", "text": "x" * 1500, "score": 0.9 - index / 100}
                for index in range(3)
            ]

        def search_knowledge(self, query, k=5):
            return self.items

    request = _request()
    request.constraints.update(
        {
            "max_evidence_items": 3,
            "max_evidence_chars": 1000,
            "max_evidence_per_source_kind": 1,
        }
    )

    evidence, _warnings = retrieve_evidence(request, "policy", rag_service=MultiRag())

    assert len(evidence) == 1
    assert len(evidence[0].text) == 1000
    assert [
        decision["reason"]
        for decision in request.metadata["_retrieval_decisions"]
        if decision["disposition"] == "rejected"
    ] == ["source_diversity_limit", "source_diversity_limit"]
