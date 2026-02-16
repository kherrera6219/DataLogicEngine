
import pytest
from unittest.mock import MagicMock, patch
import sys
from flask import Flask
from datetime import datetime

# Explicitly import services
from backend.email_service import send_email, init_mail
from backend.export_service import (
    export_simulation_to_csv, export_nodes_to_csv, 
    generate_pdf_report, export_to_excel
)
from backend.search_service import search_knowledge_nodes, global_search
from backend.retention_service import DataRetentionService, RetentionCategory

# --- Fixtures ---

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['MAIL_SUPPRESS_SEND'] = True 
    
    init_mail(app)
    
    with app.app_context():
        yield app

# --- Email Service Tests ---

def test_email_init(app):
    with patch('backend.email_service.mail') as mock_mail_obj:
        init_mail(app)
        mock_mail_obj.init_app.assert_called_with(app)

def test_send_email_mock(app, caplog):
    # Patch Message to avoid real Flask-Mail Message creation issues
    with patch('backend.email_service.mail') as mock_mail_obj, \
         patch('backend.email_service.Message'):
        
        with patch('backend.email_service.Thread') as mock_thread:
            # Sync
            success = send_email("Sub", ["a@b.com"], body="Hello", async_send=False)
            if not success:
                print(f"Sync Email Failed: {caplog.text}")
            assert success is True
            mock_mail_obj.send.assert_called()
            
            # Async
            success = send_email("Sub", ["a@b.com"], body="Hello", async_send=True)
            assert success is True
            mock_thread.assert_called()

def test_send_email_error():
    # Test internal exception handling
    with patch('backend.email_service.Message', side_effect=Exception("Mail Error")):
        assert send_email("S", ["a"]) is False

# --- Export Service Tests ---

def test_export_simulation_csv():
    sim = MagicMock()
    sim.id = 1
    sim.session_id = "s1"
    sim.name = "Sim 1"
    sim.description = "Desc"
    sim.status = "done"
    sim.created_at = datetime(2023,1,1)
    sim.started_at = None
    sim.completed_at = None
    sim.parameters = {"p1": "v1"}
    sim.results = {"r1": 100}
    
    csv_io = export_simulation_to_csv(sim)
    content = csv_io.getvalue()
    assert "Session ID,s1" in content
    assert "p1,v1" in content

def test_export_nodes_csv():
    node = MagicMock()
    node.id = 1
    node.node_id = "n1"
    node.node_type = "concept"
    node.label = "Label"
    node.created_at = datetime(2023,1,1)
    
    csv_io = export_nodes_to_csv([node])
    content = csv_io.getvalue()
    assert "n1,concept,Label" in content

def test_generate_pdf_weasyprint():
    mock_html = MagicMock()
    mock_html.write_pdf.return_value = b"%PDF-1.4"
    
    with patch.dict(sys.modules, {'weasyprint': MagicMock(HTML=MagicMock(return_value=mock_html))}):
        pdf = generate_pdf_report("Title", {"Section": "Content"})
        assert pdf == b"%PDF-1.4"

def test_generate_pdf_fallback():
    # Force ImportError
    with patch.dict(sys.modules, {'weasyprint': None}):
        output = generate_pdf_report("Title", {"Section": "Content"})
        # Should return HTML bytes
        assert b"<!DOCTYPE html>" in output
        assert b"Title" in output

def test_export_excel():
    mock_wb = MagicMock()
    mock_ws = MagicMock()
    mock_wb.active = mock_ws
    
    mock_openpyxl = MagicMock()
    mock_openpyxl.Workbook.return_value = mock_wb
    
    data = [{"col1": "val1", "col2": "val2"}]
    
    with patch.dict(sys.modules, {'openpyxl': mock_openpyxl}):
        bio = export_to_excel(data)
        assert bio is not None
        mock_wb.save.assert_called()
        
    # Test missing openpyxl
    with patch.dict(sys.modules, {'openpyxl': None}):
        with pytest.raises(ImportError):
            export_to_excel(data)

# --- Search Service Tests ---

def test_search_nodes():
    # Mock db.session.execute on the service module directly
    mock_result = MagicMock()
    row1 = MagicMock()
    row1._mapping = {'id': 1, 'label': 'Test Node', 'rank': 0.9}
    mock_result.__iter__.return_value = [row1]
    
    mock_scalar_result = MagicMock()
    mock_scalar_result.scalar.return_value = 1
    
    # Patch backend.search_service.db.session.execute
    with patch('backend.search_service.db.session.execute', side_effect=[mock_result, mock_scalar_result]):
        res = search_knowledge_nodes("query")
        if not res['success']:
             print(f"Search failed: {res.get('error')}")
        assert res['success'] is True
        assert len(res['results']) == 1
        assert res['results'][0]['label'] == 'Test Node'
        assert res['total'] == 1

def test_global_search():
    # Mock individual search functions
    with patch('backend.search_service.search_knowledge_nodes') as m_nodes, \
         patch('backend.search_service.search_ukg_nodes') as m_ukg, \
         patch('backend.search_service.search_algorithms') as m_algos:
         
         m_nodes.return_value = {'success': True, 'results': ['n']}
         m_ukg.return_value = {'success': True, 'results': ['u']}
         m_algos.return_value = {'success': True, 'results': ['a']}
         
         res = global_search("q")
         assert res['results']['nodes']['results'] == ['n']
         assert res['results']['ukg_nodes']['results'] == ['u']

# --- Retention Service Tests ---

def test_retention_init():
    srv = DataRetentionService()
    assert RetentionCategory.SESSIONS in srv.policies
    policy = srv.get_policy(RetentionCategory.SESSIONS)
    assert policy.retention_days > 0

def test_retention_cleanup_sessions():
    srv = DataRetentionService()
    
    mock_db = MagicMock()
    mock_session_cls = MagicMock()
    mock_query = MagicMock()
    mock_query.count.return_value = 5
    mock_session_cls.query.filter.return_value = mock_query
    
    # Allow < comparison for created_at
    mock_session_cls.created_at.__lt__.return_value = MagicMock()
    
    with patch.dict(sys.modules):
        sys.modules['extensions'] = MagicMock(db=mock_db)
        sys.modules['models'] = MagicMock(ChatSession=mock_session_cls)
        
        res = srv.cleanup_sessions(dry_run=False)
        
        if res['status'] != 'success':
            print(f"Retention Failed: {res.get('error')}")
            
        assert res['status'] == 'success'
        assert res['deleted_count'] == 5
        mock_db.session.commit.assert_called()

def test_run_cleanup_all():
    srv = DataRetentionService()
    with patch.object(srv, 'cleanup_sessions') as m_sess, \
         patch.object(srv, 'cleanup_trace_runs') as m_trace:
         
         m_sess.return_value = {"category":"sessions", "status": "success"}
         m_trace.return_value = {"category":"trace_runs", "status": "success"}
         
         summary = srv.run_cleanup()
         assert summary['status'] == "success"
         assert len(summary['cleanups']) == 2
