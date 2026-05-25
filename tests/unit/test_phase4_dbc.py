from types import SimpleNamespace

from backend.services.rag_service import RAGService
from backend.storage.vector_store import SearchResult, VectorStore, get_collection_counts
from backend.truth_engine.truth_core.emergence_controller import EmergenceDetectionController
from backend.truth_engine.truth_core.engine import TruthCoreEngine
from backend.truth_engine.truth_core.meta_reasoning_controller import MetaReasoningController
from backend.truth_engine.truth_core.l10_schemas import L10Input
from backend.truth_engine.truth_gate.l8_schemas import L8Input
from backend.truth_engine.truth_gate.trust_validation_gateway import TrustValidationGateway
from scripts.index_knowledge_nodes import index_nodes


class RecordingStore:
    def __init__(self):
        self.add_calls = []
        self.search_calls = []

    def add_embeddings(self, **kwargs):
        self.add_calls.append(kwargs)
        return kwargs["ids"]

    def search(self, **kwargs):
        self.search_calls.append(kwargs)
        return [
            SearchResult(
                id="node-1",
                score=0.91,
                text="healthcare compliance evidence",
                metadata={"node_id": "KG-1", "node_type": "regulation"},
            )
        ]


def test_rag_uses_knowledge_nodes_collection_and_scalar_metadata():
    store = RecordingStore()
    service = RAGService(vector_store=store, embedding_provider=lambda _text: [0.1, 0.2])

    assert service.ingest_knowledge_node(
        "node-1",
        "healthcare compliance",
        "regulation",
        {"axis": 10, "nested": {"source": "unit"}},
    )
    assert store.add_calls[0]["collection"] == "knowledge_nodes"
    assert store.add_calls[0]["metadata"][0]["nested"] == '{"source": "unit"}'

    results = service.search_knowledge("healthcare compliance")
    assert results[0]["metadata"]["node_id"] == "KG-1"
    assert store.search_calls[0]["collection"] == "knowledge_nodes"


def test_index_knowledge_nodes_indexes_sql_node_like_objects():
    store = RecordingStore()
    service = RAGService(vector_store=store, embedding_provider=lambda _text: [0.1])
    nodes = [
        SimpleNamespace(
            id=1,
            uid="uid-1",
            node_id="KG-1",
            node_type="regulation",
            axis_number=10,
            tenant_id=None,
            title="HIPAA",
            label="HIPAA Rule",
            description="Healthcare privacy compliance",
            content="Protected health information controls",
        ),
        SimpleNamespace(
            id=2,
            uid=None,
            node_id=None,
            node_type=None,
            axis_number=None,
            tenant_id=None,
            title=None,
            label=None,
            description=None,
            content=None,
        ),
    ]

    result = index_nodes(nodes, rag_service=service)

    assert result.to_dict() == {"scanned": 2, "indexed": 1, "skipped": 1}
    assert store.add_calls[0]["ids"] == ["uid-1"]
    assert store.add_calls[0]["metadata"][0]["source"] == "ukg_knowledge_nodes"


def test_collection_counts_reads_required_collection_stats(monkeypatch):
    class Backend:
        def list_collection_stats(self):
            return {
                "knowledge_nodes": {"count": 7},
                "persona_profiles": {"count": 2},
                "citation_cache": {"total_count": 3},
                "audit_evidence": {},
            }

    import backend.storage.vector_store as vector_store_module

    monkeypatch.setattr(vector_store_module, "get_vector_store", lambda: VectorStore(backend=Backend()))

    assert get_collection_counts() == {
        "knowledge_nodes": 7,
        "persona_profiles": 2,
        "citation_cache": 3,
        "audit_evidence": 0,
    }


def test_truthcore_deep_research_uses_rag_evidence(monkeypatch):
    class FakeRag:
        def search_knowledge(self, query, k=8):
            return [{"id": "n1", "text": query, "metadata": {"node_id": "KG-1"}}]

    import backend.services.rag_service as rag_module

    monkeypatch.setattr(rag_module, "get_rag_service", lambda: FakeRag())
    engine = TruthCoreEngine()

    result = engine._execute_refinement_step("deep_research", "healthcare compliance", {})

    assert result["ka_id"] == "RAG-KNOWLEDGE-NODES"
    assert result["output"]["source_node_ids"] == ["KG-1"]


def test_l8_and_l9_search_dbc_collections(monkeypatch):
    calls = []

    class FakeRag:
        def search_collection(self, collection, query, k=5, filters=None):
            calls.append((collection, query, k, filters))
            return [{"id": "hit", "score": 0.9, "text": "prior evidence", "metadata": {}}]

    import backend.services.rag_service as rag_module

    monkeypatch.setattr(rag_module, "get_rag_service", lambda: FakeRag())

    citation_hits = TrustValidationGateway._search_citation_cache(
        L8Input(simulation_id="s1", query_text="claim", claims=[{"text": "claim detail"}])
    )
    audit_hits = MetaReasoningController._search_audit_evidence("original", "solution")

    assert citation_hits
    assert audit_hits
    assert calls[0][0] == RAGService.COLLECTION_CITATION_CACHE
    assert calls[1][0] == RAGService.COLLECTION_AUDIT_EVIDENCE


def test_l10_indexes_lane_b_trace_to_dbc_collections(monkeypatch):
    calls = []

    class FakeRag:
        def ingest_knowledge_node(self, item_id, text, node_type, metadata):
            calls.append(("knowledge", item_id, text, node_type, metadata))
            return True

        def ingest_text(self, collection, item_id, text, metadata=None):
            calls.append((collection, item_id, text, metadata))
            return True

    import backend.services.rag_service as rag_module

    monkeypatch.setattr(rag_module, "get_rag_service", lambda: FakeRag())
    input_data = L10Input(
        simulation_id="sim-1",
        l9_result={"epistemic_report": {"current_output": "approved answer"}},
        reasoning_trace={"steps": ["L1", "L10"]},
        problem_spec={"original_query": "query"},
        coordinate_vector={"axis_1": "PL01"},
    )
    properties = {
        "uid": "l10:abc",
        "node_type": "authorized_knowledge",
        "title": "approved answer",
        "content": "approved answer",
    }

    result = EmergenceDetectionController._index_lane_b_trace(input_data, properties)

    assert result["knowledge_nodes_indexed"] is True
    assert result["audit_evidence_indexed"] is True
    assert calls[0][0] == "knowledge"
    assert calls[1][0] == RAGService.COLLECTION_AUDIT_EVIDENCE
