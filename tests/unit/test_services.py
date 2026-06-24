# ruff: noqa: E402

import pytest
from unittest.mock import MagicMock, patch
import sys
import os
import logging

from backend.services.analytics_service import AnalyticsService
from backend.services.document_processor import DocumentProcessor
from backend.services.rag_service import RAGService
from backend.services.video_service import VideoService

# --- Analytics Service Tests ---

@patch('backend.services.analytics_service.db')
@patch('backend.services.analytics_service.KAExecution')
@patch('backend.services.analytics_service.Node')
@patch('backend.services.analytics_service.Edge')
def test_analytics_service_dashboard(mock_edge, mock_node, mock_ka, mock_db, caplog):
    # Setup mocks
    # Handle SQLAlchemy operator overloading for mocks
    mock_ka.created_at.__ge__.return_value = MagicMock()
    
    # Configure query chain to support multiple .filter() calls
    mock_query = mock_db.session.query.return_value
    mock_query.filter.return_value = mock_query
    
    # Set return values for sequential .count() calls:
    # 1. request_count (50)
    # 2. node_count (100)
    # 3. edge_count (200)
    mock_query.count.side_effect = [50, 100, 200]
    
    with caplog.at_level(logging.ERROR):
        summary = AnalyticsService.get_dashboard_overview(tenant_id="tenant1")
        
    if summary is None:
        print(f"Analytics Error Logs: {caplog.text}")
        
    assert summary is not None
    assert summary['api_requests_24h'] == 50
    assert summary['kg_nodes'] == 100
    assert summary['kg_edges'] == 200


# --- Document Processor Tests ---

def test_document_processor_process_text():
    dp = DocumentProcessor()
    content = b"Hello World"
    result = dp.process_file(content, "test.txt", "text/plain")
    assert result['text'] == "Hello World"
    assert result['metadata']['type'] == "text"

def test_document_processor_unsupported():
    dp = DocumentProcessor()
    with pytest.raises(ValueError, match="Unsupported file type"):
        dp.process_file(b"data", "test.exe", "application/octet-stream")

def test_document_processor_empty():
    dp = DocumentProcessor()
    with pytest.raises(ValueError, match="empty"):
        dp.process_file(b"", "test.txt", "text/plain")

def test_document_processor_pdf_mock():
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "PDF Content"
    mock_pdf.PdfReader.return_value.pages = [mock_page]
    mock_pdf.PdfReader.return_value.is_encrypted = False
    mock_pdf.PdfReader.return_value.metadata = {}

    with patch.dict(sys.modules, {'pypdf': mock_pdf}):
        dp = DocumentProcessor()
        result = dp.process_file(b"fake_pdf", "test.pdf", "application/pdf")
        assert result['text'] == "PDF Content"

@patch('backend.services.document_processor.io.BytesIO')
def test_document_processor_image_mock(mock_bytes_io):
    mock_pil = MagicMock()
    mock_tesseract = MagicMock()
    mock_tesseract.image_to_string.return_value = "OCR Text"
    
    with patch.dict(sys.modules, {'PIL': mock_pil, 'PIL.Image': mock_pil, 'pytesseract': mock_tesseract}):
        dp = DocumentProcessor()
        result = dp.process_file(b"fake_img", "test.png", "image/png")
        assert result['text'] == "OCR Text"

@patch('backend.services.document_processor.io.BytesIO')
def test_document_processor_docx_mock(mock_bytes_io):
    mock_docx = MagicMock()
    mock_doc = MagicMock()
    mock_para = MagicMock()
    mock_para.text = "Docx Para"
    mock_doc.paragraphs = [mock_para]
    mock_docx.Document.return_value = mock_doc
    
    with patch.dict(sys.modules, {'docx': mock_docx}):
        dp = DocumentProcessor()
        result = dp.process_file(b"fake_docx", "test.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        assert result['text'] == "Docx Para"


# --- RAG Service Tests ---

def test_rag_service_flow():
    mock_store = MagicMock()
    mock_store.search.return_value = []
    mock_embed = MagicMock(return_value=[0.1, 0.2, 0.3])
    
    service = RAGService(vector_store=mock_store, embedding_provider=mock_embed)
    
    results = service.search_documents("query")
    assert results == []
    mock_store.search.assert_called()

def test_rag_basic_chunking():
    service = RAGService()
    text = "Hello. " * 100 # Long text
    chunks = service._basic_chunk_text(text, chunk_size=50, overlap=10)
    assert len(chunks) > 1
    assert "Hello" in chunks[0]

@patch('backend.services.rag_service.LLAMAINDEX_AVAILABLE', False)
def test_rag_chunk_text_fallback():
    service = RAGService()
    text = "Detailed text content here."
    # With LlamaIndex disabled, should hit basic chunker
    with patch.object(service, '_basic_chunk_text') as mock_basic:
        service.chunk_text(text)
        mock_basic.assert_called_with(text, 512, 50)

def test_rag_default_embedding_failover():
    # Test Layer 3 (Local/HF) if others fail
    service = RAGService()
    
    # Mock imports failure for OpenAI and Google, but success for sentence_transformers
    mock_st_module = MagicMock()
    mock_model = MagicMock()
    mock_model.encode.return_value.tolist.return_value = [0.1, 0.2]
    mock_st_module.SentenceTransformer.return_value = mock_model
    
    with patch.dict(sys.modules, {
        'openai': None, 
        'google': None, 
        'google.genai': None,
        'sentence_transformers': mock_st_module
    }):
        emb = service._default_embedding("test")
        assert emb == [0.1, 0.2]

def test_rag_embedding_total_failover():
    # Test Layer 4 (Mock fallback). The service fails closed in production and
    # only falls back to a mock embedding when explicitly permitted
    # (ALLOW_MOCK_EMBEDDINGS=true or a development/testing FLASK_ENV), so enable
    # that flag here to exercise the development/testing fallback path.
    service = RAGService()
    with patch.dict(sys.modules, {'openai': None, 'google': None, 'sentence_transformers': None}), \
         patch.dict('os.environ', {'ALLOW_MOCK_EMBEDDINGS': 'true'}):
        emb = service._default_embedding("test")
        assert len(emb) == 384 # Mock embedding size

def test_rag_ingest_document():
    mock_store = MagicMock()
    service = RAGService(vector_store=mock_store)
    
    # Use mock embedding to avoid overhead
    service.set_embedding_provider(lambda x: [0.1] * 10)
    
    count = service.ingest_document("doc1", "content " * 50, {}, chunk_size=20)
    assert count > 0
    mock_store.add_embeddings.assert_called()

def test_get_context_for_query():
    mock_store = MagicMock()
    # Mock search results
    mock_result = MagicMock()
    mock_result.text = "Relevant info"
    mock_result.score = 0.9
    # Mimic dict-like interface if that's what context builder expects, 
    # but the code says: text = r.get("text", "") -> implying results are Dicts
    # Wait, search_documents returns List[Dict]. The code snippet above mocks search returning objects.
    # Let me double check search_documents implementation.
    # It returns [{"id":..., "text":...}]
    
    mock_store.search.return_value = [MagicMock(text="Relevant info", score=0.9, metadata={})] 
    # Oh wait, search_documents wrapper converts it to Dict. 
    # So if I mock store.search, I should assume store.search returns objects, and service.search_documents converts them.
    # The current test_rag_service_flow mocks it returning [] so no conversion logic runs.
    
    # Let's verify the code:
    # results = store.search(...)
    # return [{ "id": r.id ... } for r in results]
    
    # So the mock return value MUST act like an object with attributes .id, .text etc.
    mock_obj = MagicMock()
    mock_obj.id = "1"
    mock_obj.text = "Relevant info"
    mock_obj.score = 0.9
    mock_obj.metadata = {}
    mock_store.search.return_value = [mock_obj]
    
    service = RAGService(vector_store=mock_store)
    service.set_embedding_provider(lambda x: [0.1])
    
    context = service.get_context_for_query("Ask", k=1)
    assert "Relevant info" in context

def test_rag_chat_history():
    mock_store = MagicMock()
    service = RAGService(vector_store=mock_store)
    service.set_embedding_provider(lambda x: [0.1])
    
    success = service.store_chat_message("sess1", "msg1", "user", "Hello")
    assert success is True
    mock_store.add_embeddings.assert_called_with(
        collection=service.COLLECTION_CHAT_HISTORY,
        ids=["msg1"],
        texts=["Hello"],
        embeddings=[[0.1]],
        metadata=[{"session_id": "sess1", "role": "user", "user_id": ""}]
    )
    
    # Test Search
    mock_store.search.return_value = []
    service.search_chat_history("sess1", "query")
    mock_store.search.assert_called()

def test_rag_knowledge_node():
    mock_store = MagicMock()
    service = RAGService(vector_store=mock_store)
    service.set_embedding_provider(lambda x: [0.1])
    
    success = service.ingest_knowledge_node("node1", "content", "concept")
    assert success is True
    mock_store.add_embeddings.assert_called()
    
    # Test Search
    mock_store.search.return_value = []
    service.search_knowledge("query", node_type="concept")
    mock_store.search.assert_called()

# --- Video Service Tests ---

@pytest.mark.asyncio
async def test_video_service_analyze():
    mock_cv2 = MagicMock()
    mock_cap = MagicMock()
    mock_cv2.VideoCapture.return_value = mock_cap
    mock_cap.read.side_effect = [(True, "frame1"), (True, "frame2"), (False, None)]
    mock_cap.get.return_value = 30
    mock_cv2.imencode.return_value = (True, MagicMock(tobytes=lambda: b"encoded_frame"))
    
    mock_gateway = MagicMock()
    async def async_process(*args, **kwargs):
        return MagicMock(ok=True, content="Video Summary")
    mock_gateway.process.side_effect = async_process
    
    with patch('backend.services.video_service.CV2', mock_cv2):
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = "temp.mp4"
            vs = VideoService(llm_gateway=mock_gateway)
            result = await vs.analyze_video(b"video_bytes")
            
            # Debug outcome
            if 'error' in result:
                print(f"Video Error: {result['error']}")
                
            assert result['status'] == "completed"
            assert result['summary'] == "Video Summary"


# --- Audio Service Tests ---
from backend.services.audio_service import AudioService

@pytest.mark.asyncio
async def test_audio_service_transcribe_openai():
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.return_value.text = "OpenAI Transcript"
    
    with patch('backend.services.audio_service.OpenAI') as mock_openai_cls:
        mock_openai_cls.return_value = mock_client
        
        service = AudioService(api_key="sk-fake")
        transcript = await service.transcribe(b"audio", "test.wav")
        assert transcript == "OpenAI Transcript"

@pytest.mark.asyncio
async def test_audio_service_transcribe_google_failover():
    # OpenAI fails (client init failure or other)
    # Mock os.getenv to return None for OPENAI_API_KEY initially
    
    mock_response = MagicMock()
    mock_response.text = "Gemini Transcript"
    
    mock_genai_client = MagicMock()
    mock_genai_client.models.generate_content.return_value = mock_response
    
    # We patch OpenAI to raise error or return None, and patch Google
    with patch('backend.services.audio_service.OpenAI', side_effect=Exception("OpenAI Down")):
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "fake_google_key", "OPENAI_API_KEY": ""}):
            # Mock google.genai
            mock_genai = MagicMock()
            mock_genai.genai = mock_genai # Handle "from google import genai" if resolved via attr
            mock_genai.Client.return_value = mock_genai_client
            
            with patch.dict(sys.modules, {'google': mock_genai, 'google.genai': mock_genai}):
                 service = AudioService(api_key=None)
                 transcript = await service.transcribe(b"audio", "test.wav")
                 
                 # It should fall back to Gemini
                 assert transcript == "Gemini Transcript"

@pytest.mark.asyncio
async def test_audio_service_synthesize():
    mock_client = MagicMock()
    mock_client.audio.speech.create.return_value.content = b"audio_content"
    
    with patch('backend.services.audio_service.OpenAI') as mock_openai_cls:
        mock_openai_cls.return_value = mock_client
        service = AudioService(api_key="sk-fake")
        
        audio = await service.synthesize("Hello")
        assert audio == b"audio_content"
