
from unittest.mock import MagicMock, patch
import sys
import uuid

# Explicitly import services
from backend.routes import storage_routes
from backend.search_service import (
    global_search,
    search_algorithms,
    search_knowledge_nodes,
    search_ukg_nodes,
)
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


def test_search_failures_hide_exception_details():
    sentinel = "secret-search-backend-path"
    cases = (
        (search_knowledge_nodes, "Knowledge node search failed"),
        (search_ukg_nodes, "UKG search failed"),
        (search_algorithms, "Algorithm search failed"),
    )

    for search_function, expected_error in cases:
        with patch(
            'backend.search_service.db.session.execute',
            side_effect=RuntimeError(sentinel),
        ):
            result = search_function("query")

        assert result['success'] is False
        assert result['error'] == expected_error
        assert sentinel not in repr(result)

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


def test_retention_cleanup_trace_runs_purges_matching_capture():
    srv = DataRetentionService()
    run_id = uuid.uuid4()
    mock_db = MagicMock()
    mock_model = MagicMock()
    mock_query = MagicMock()
    mock_model.created_at.__lt__.return_value = MagicMock()
    mock_model.query.filter.return_value = mock_query
    mock_query.with_entities.return_value.all.return_value = [(run_id,)]
    mock_modules = {
        'extensions': MagicMock(db=mock_db),
        'models': MagicMock(TraceRun=mock_model),
    }

    with patch.dict(sys.modules, mock_modules), patch(
        'backend.dataset_exporter.runtime_capture.purge_staged_capture_runs'
    ) as purge:
        result = srv.cleanup_trace_runs()

    assert result['status'] == 'success'
    assert result['deleted_count'] == 1
    purge.assert_called_once_with([str(run_id)])
    mock_query.delete.assert_called_once_with(synchronize_session=False)
    mock_db.session.commit.assert_called_once_with()

def test_run_cleanup_all():
    srv = DataRetentionService()
    with patch.object(srv, 'cleanup_sessions') as m_sess, \
         patch.object(srv, 'cleanup_trace_runs') as m_trace:

         m_sess.return_value = {"category":"sessions", "status": "success"}
         m_trace.return_value = {"category":"trace_runs", "status": "success"}

         summary = srv.run_cleanup()
         assert summary['status'] == "success"
         assert len(summary['cleanups']) == 2


def test_retention_cleanup_failures_hide_exception_details():
    srv = DataRetentionService()
    sentinel = "secret-retention-database-path"

    with patch.object(
        srv,
        'cleanup_sessions',
        side_effect=RuntimeError(sentinel),
    ), patch.object(
        srv,
        'cleanup_trace_runs',
        side_effect=RuntimeError(sentinel),
    ):
        summary = srv.run_cleanup()

    assert [item['error'] for item in summary['cleanups']] == [
        "Category cleanup failed",
        "Category cleanup failed",
    ]
    assert sentinel not in repr(summary)


def test_individual_retention_failures_hide_exception_details():
    srv = DataRetentionService()
    sentinel = "secret-retention-query"
    mock_model = MagicMock()
    mock_model.query.filter.side_effect = RuntimeError(sentinel)
    mock_modules = {
        'extensions': MagicMock(db=MagicMock()),
        'models': MagicMock(ChatSession=mock_model, TraceRun=mock_model),
    }

    with patch.dict(sys.modules, mock_modules):
        session_result = srv.cleanup_sessions()
        trace_result = srv.cleanup_trace_runs()

    assert session_result['error'] == "Session cleanup failed"
    assert trace_result['error'] == "Trace run cleanup failed"
    assert sentinel not in repr((session_result, trace_result))


def test_sqlite_metrics_hide_exception_details(tmp_path):
    sentinel = "secret-sqlite-database-path"
    database_path = tmp_path / "metrics.db"
    database_path.write_bytes(b"")

    with patch.object(
        storage_routes,
        '_sqlite_path_from_database_url',
        return_value=database_path,
    ), patch.object(
        storage_routes.sqlite3,
        'connect',
        side_effect=RuntimeError(sentinel),
    ):
        metrics = storage_routes._sqlite_metrics()

    assert metrics['available'] is False
    assert metrics['error'] == "SQLite metrics unavailable"
    assert sentinel not in repr(metrics)
