
import pytest
from unittest.mock import MagicMock, patch
from backend.services.rag_service import RAGService

class TestRAGService:
    
    @pytest.fixture
    def mock_vector_store(self):
        store = MagicMock()
        store.add_embeddings = MagicMock()
        store.search = MagicMock(return_value=[
            MagicMock(id="1", text="match", score=0.9, metadata={})
        ])
        return store
    
    @pytest.fixture
    def rag_service(self, mock_vector_store):
        # Inject mock vector store directly
        service = RAGService(vector_store=mock_vector_store)
        return service

    def test_init_lazy_load(self):
        # Test default init without injection
        with patch("backend.storage.get_vector_store") as mock_get:
            service = RAGService()
            assert service._vector_store is None
            store = service._get_vector_store()
            assert store == mock_get.return_value
            mock_get.assert_called_once()

    def test_default_embedding_layer1_openai(self, rag_service):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-fake"}), \
             patch("openai.OpenAI") as MockOpenAI:
            
            mock_client = MockOpenAI.return_value
            mock_client.embeddings.create.return_value.data = [MagicMock(embedding=[0.1, 0.2])]
            
            result = rag_service._default_embedding("test")
            assert result == [0.1, 0.2]
            MockOpenAI.assert_called()

    def test_default_embedding_layer2_google(self, rag_service):
        # Force OpenAI failure or missing key
        with patch.dict("os.environ", {"OPENAI_API_KEY": "", "GOOGLE_API_KEY": "google-fake"}), \
             patch("google.genai.Client") as MockGenAI:
            
            mock_client = MockGenAI.return_value
            mock_client.models.embed_content.return_value.embeddings = [MagicMock(values=[0.3, 0.4])]
            
            result = rag_service._default_embedding("test")
            assert result == [0.3, 0.4]
            MockGenAI.assert_called()

    def test_default_embedding_layer3_local(self, rag_service):
        # Force API keys missing
        with patch.dict("os.environ", {"OPENAI_API_KEY": "", "GOOGLE_API_KEY": ""}), \
             patch("sentence_transformers.SentenceTransformer") as MockST:
             
            mock_model = MockST.return_value
            # configure encode to return numpy array which calls tolist
            import numpy as np
            mock_model.encode.return_value = np.array([0.5, 0.6])
            
            result = rag_service._default_embedding("test")
            assert result == [0.5, 0.6]
            MockST.assert_called_with('all-MiniLM-L6-v2')

    def test_default_embedding_fallback_mock(self, rag_service):
        # Fail everything
        with patch.dict("os.environ", {"OPENAI_API_KEY": "", "GOOGLE_API_KEY": ""}), \
             patch("sentence_transformers.SentenceTransformer", side_effect=ImportError):
            
            result = rag_service._default_embedding("test")
            assert len(result) == 384 # Mock embedding length

    def test_chunk_text_basic(self, rag_service):
        # Force basic chunking by disabling LlamaIndex flag (mocking at class level tricky, 
        # but we can rely on _basic_chunk_text logic if LlamaIndex not present or failed)
        
        # Test basic splitter logic directly
        text = "Hello world. " * 50
        chunks = rag_service._basic_chunk_text(text, chunk_size=100, overlap=10)
        assert len(chunks) > 1
        assert len(chunks[0]) <= 100

    def test_ingest_document(self, rag_service, mock_vector_store):
        # Mock embedding provider to avoid complex logic
        rag_service.set_embedding_provider(lambda x: [0.1]*384)
        
        count = rag_service.ingest_document("doc1", "content " * 100, {"source": "test"})
        
        assert count > 0
        mock_vector_store.add_embeddings.assert_called_once()
        call_args = mock_vector_store.add_embeddings.call_args[1]
        assert call_args["collection"] == "documents"
        assert len(call_args["ids"]) == count

    def test_search_documents(self, rag_service, mock_vector_store):
        rag_service.set_embedding_provider(lambda x: [0.1]*384)
        
        results = rag_service.search_documents("query")
        
        assert len(results) == 1
        assert results[0]["id"] == "1"
        mock_vector_store.search.assert_called_once()

    def test_get_context_for_query(self, rag_service):
        # Mock search_documents
        rag_service.search_documents = MagicMock(return_value=[
            {"text": "Relevant info A", "metadata": {"filename": "a.txt"}},
            {"text": "Relevant info B", "metadata": {"filename": "b.txt"}}
        ])
        
        context = rag_service.get_context_for_query("help", include_sources=True)
        assert "Relevant info A" in context
        assert "[Source: a.txt]" in context
        assert "Relevant info B" in context

    def test_store_chat_message(self, rag_service, mock_vector_store):
        rag_service.set_embedding_provider(lambda x: [0.1]*384)
        
        success = rag_service.store_chat_message("sess_1", "msg_1", "user", "hello")
        
        assert success is True
        mock_vector_store.add_embeddings.assert_called()
        call_args = mock_vector_store.add_embeddings.call_args[1]
        assert call_args["collection"] == "chat_history"
        assert call_args["ids"] == ["msg_1"]
