
import pytest
from unittest.mock import MagicMock, patch, mock_open
import sys
import os
import io
import logging

from backend.services.analytics_service import AnalyticsService
from backend.services.document_processor import DocumentProcessor
from backend.services.rag_service import RAGService
from backend.services.video_service import VideoService
from backend.services.file_upload_service import FileUploadService, UploadedFile

# --- Analytics Service Tests ---

@patch('backend.services.analytics_service.db')
@patch('backend.services.analytics_service.KAExecution')
@patch('backend.services.analytics_service.Node')
@patch('backend.services.analytics_service.Edge')
def test_analytics_service_dashboard(mock_edge, mock_node, mock_ka, mock_db, caplog):
    # Setup mocks
    mock_db.session.query.return_value.filter.return_value.count.return_value = 50
    # The side_effect needs to cover calls for Node and Edge counts
    mock_db.session.query.return_value.count.side_effect = [100, 200]
    
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

@patch('backend.services.document_processor.io.BytesIO')
def test_document_processor_pdf_mock(mock_bytes_io):
    mock_pdf = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "PDF Content"
    mock_pdf.PdfReader.return_value.pages = [mock_page]
    
    with patch.dict(sys.modules, {'PyPDF2': mock_pdf}):
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
    
    with patch.dict(sys.modules, {'cv2': mock_cv2}):
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = "temp.mp4"
            vs = VideoService(llm_gateway=mock_gateway)
            result = await vs.analyze_video(b"video_bytes")
            assert result['status'] == "completed"
            assert result['summary'] == "Video Summary"


# --- File Upload Service Tests ---

def test_file_upload_validation():
    service = FileUploadService()
    # Mock internal lazy loaders to return Nones or Mocks if needed
    # But for validation we don't need them
    
    valid, msg = service.validate_file(b"content", "valid.txt", "text/plain")
    assert valid is True
    
    valid, msg = service.validate_file(b"", "empty.txt", "text/plain")
    assert valid is False
    assert "empty" in msg

@patch('backend.services.file_upload_service.get_file_upload_service') 
def test_file_upload_process(mock_get_service):
    # We test the service instance directly
    mock_store = MagicMock()
    mock_processor = MagicMock()
    mock_rag = MagicMock()
    
    service = FileUploadService(object_store=mock_store, document_processor=mock_processor, rag_service=mock_rag)
    
    # Mock processor
    mock_processor.process_file.return_value = {"text": "Extracted Content"}
    
    # Mock RAG
    mock_rag.ingest_document.return_value = ["chunk1"]
    
    result = service.upload_file(
        file_bytes=b"file_content",
        filename="test.txt",
        mime_type="text/plain",
        user_id=123
    )
    
    assert result.filename == "test.txt"
    assert result.processed is True
    assert "embedded_chunks" in result.metadata
    
    mock_store.put.assert_called()
    mock_processor.process_file.assert_called()
    mock_rag.ingest_document.assert_called()
