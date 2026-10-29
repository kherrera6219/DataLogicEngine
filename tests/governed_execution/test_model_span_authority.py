"""R-3: selected model spans must be backed by SQL and cite exact source text."""

from hashlib import sha256

import pytest

from backend.governed_execution.retrieval import retrieve_evidence
from extensions import db
from models import KnowledgeGraphNode, User
from tests.governed_execution.test_model_split_ingestion_authority import _round_trip
from tests.governed_execution.test_phase9_retrieval_authority import _request


def _setup(app, tmp_path, monkeypatch):
    text = "  " + " ".join(f"word{i} café" for i in range(30)) + "  "
    service, store, job, source_file, chunk = _round_trip(
        app, tmp_path, monkeypatch, text
    )
    return text, service, store, job, source_file, chunk


def test_selected_model_spans_cite_exact_sql_parent_and_canonical_locator(
    app, tmp_path, monkeypatch
):
    with app.app_context():
        text, service, store, _job, _file, chunk = _setup(app, tmp_path, monkeypatch)
        assert len(store.rows) > 1
        evidence, warnings = retrieve_evidence(
            _request(), "policy", rag_service=service
        )
        assert warnings == []
        assert len(evidence) > 1
        for result in evidence:
            locator = result.locator
            assert locator["parent_source_id"] == chunk.node_uid
            assert locator["chunk_index"] == 7
            assert locator["chunk_count"] == 12
            assert (
                text[locator["source_span_start"] : locator["source_span_end"]]
                == result.text
            )
            assert result.metadata["source_revision"] == chunk.source_revision


def test_graph_lookup_uses_verified_parent_for_child_span(app, tmp_path, monkeypatch):
    with app.app_context():
        _text, service, store, _job, _file, chunk = _setup(app, tmp_path, monkeypatch)
        key = list(store.rows)[1]
        store.rows = {key: store.rows[key]}
        calls = []

        def lookup(parent):
            calls.append(parent)
            return [], None

        monkeypatch.setattr(
            "backend.governed_execution.retrieval._load_graph_context", lookup
        )
        request = _request()
        request.constraints["use_graph_context"] = True
        evidence, warnings = retrieve_evidence(request, "policy", rag_service=service)
        assert len(evidence) == 1
        assert warnings == []
        assert calls == [chunk.node_uid]


def test_spoofed_citation_fields_do_not_override_sql(app, tmp_path, monkeypatch):
    with app.app_context():
        _text, service, store, job, source_file, chunk = _setup(
            app, tmp_path, monkeypatch
        )
        node = KnowledgeGraphNode.query.filter_by(uid=chunk.node_uid).one()
        node.node_id = "KI-SQL"
        node.title = "SQL Title"
        db.session.commit()
        for _, _, metadata in store.rows.values():
            metadata.update(
                node_id="spoofed",
                uid="ki_spoofed",
                title="spoofed",
                source_path="spoofed",
                content_hash="0" * 64,
                ingestion_id="spoofed",
            )
        evidence, warnings = retrieve_evidence(
            _request(), "policy", rag_service=service
        )
        assert warnings == []
        assert evidence
        for result in evidence:
            assert result.content_hash == chunk.content_sha256
            assert result.locator["node_id"] == "KI-SQL"
            assert result.locator["uid"] == chunk.node_uid
            assert result.title == "SQL Title"
            assert result.metadata["source_path"] == source_file.relative_path
            assert result.metadata["ingestion_id"] == str(job.id)


@pytest.mark.parametrize(
    "tamper",
    [
        "text",
        "start",
        "end",
        "span_hash",
        "parent_hash",
        "parent_id",
        "index",
        "revision",
        "parent_sql",
        "id_without_prefix",
        "missing_span_proof",
    ],
)
def test_tampered_model_span_never_becomes_evidence(app, tmp_path, monkeypatch, tamper):
    with app.app_context():
        _text, service, store, _job, _file, chunk = _setup(app, tmp_path, monkeypatch)
        key = next(iter(store.rows))
        row_text, vector, metadata = store.rows[key]
        # Limit retrieval to the modified row so another valid span cannot mask rejection.
        store.rows = {key: (row_text, vector, dict(metadata))}
        metadata = store.rows[key][2]
        if tamper == "text":
            store.rows[key] = (row_text + " injected", vector, metadata)
            metadata["source_span_sha256"] = sha256(
                (row_text + " injected").encode()
            ).hexdigest()
        elif tamper == "start":
            metadata["source_span_start"] += 1
        elif tamper == "end":
            metadata["source_span_end"] += 1
        elif tamper == "span_hash":
            metadata["source_span_sha256"] = "0" * 64
        elif tamper == "parent_hash":
            metadata["source_parent_sha256"] = "0" * 64
        elif tamper == "parent_id":
            metadata["vector_parent_id"] = "ki_other"
        elif tamper == "index":
            metadata["vector_chunk_index"] = 9
        elif tamper == "revision":
            metadata["source_revision"] = "stale"
        elif tamper == "parent_sql":
            KnowledgeGraphNode.query.filter_by(
                uid=chunk.node_uid
            ).one().content += " changed"
            db.session.commit()
        elif tamper == "id_without_prefix":
            store.rows = {(key[0], "forged_id"): store.rows[key]}
        elif tamper == "missing_span_proof":
            metadata.pop("source_span_sha256")
        evidence, warnings = retrieve_evidence(
            _request(), "policy", rag_service=service
        )
        assert evidence == []
        assert any(w.startswith("ingestion_source_rejected:") for w in warnings)


@pytest.mark.parametrize(
    "condition",
    ["job", "file", "original", "normalized", "chunk", "defense", "tenant", "owner"],
)
def test_split_spans_keep_existing_eligibility_checks(
    app, tmp_path, monkeypatch, condition
):
    with app.app_context():
        _text, service, _store, job, source_file, chunk = _setup(
            app, tmp_path, monkeypatch
        )
        if condition == "job":
            job.status = "materialization_pending"
        elif condition == "file":
            source_file.status = "pending"
        elif condition == "original":
            source_file.object_status = "pending"
        elif condition == "normalized":
            source_file.normalized_object_status = "pending"
        elif condition == "chunk":
            chunk.materialization_state = "pending"
        elif condition == "defense":
            source_file.defense_result = {
                "policy_version": "content-defense.v1",
                "safe_for_retrieval": False,
            }
        elif condition == "tenant":
            job.tenant_id = "other"
        elif condition == "owner":
            owner = User(username="span-owner", _email="span-owner@example.test")
            db.session.add(owner)
            db.session.flush()
            job.user_id = owner.id
        db.session.commit()
        evidence, warnings = retrieve_evidence(
            _request(), "policy", rag_service=service
        )
        assert evidence == []
        assert any(w.startswith("ingestion_source_rejected:") for w in warnings)
        if condition == "owner":
            assert any(w.endswith(":owner_permission_denied") for w in warnings)
