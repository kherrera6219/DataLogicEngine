
from unittest.mock import MagicMock, patch
import sys

# Explicitly import services
from backend.search_service import search_knowledge_nodes, global_search
from backend.retention_service import DataRetentionService, RetentionCategory

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
