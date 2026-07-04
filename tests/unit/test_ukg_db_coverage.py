
import pytest
from unittest.mock import MagicMock
from datetime import datetime, UTC
from backend.ukg_db import UkgDatabaseManager

class TestUkgDatabaseManager:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.session = MagicMock()
        db.session.add = MagicMock()
        db.session.commit = MagicMock()
        db.session.rollback = MagicMock()
        return db

    @pytest.fixture
    def mock_cache(self):
        cache = MagicMock()
        cache.get.return_value = None
        cache.set = MagicMock()
        cache.delete = MagicMock()
        return cache

    @pytest.fixture
    def mock_models(self):
        models = MagicMock()
        
        # Mock Node
        models.Node = MagicMock()
        models.Node.return_value.uid = "node_1"
        models.Node.return_value.to_dict.return_value = {"uid": "node_1", "label": "Test Node"}
        
        # Mock Edge
        models.Edge = MagicMock()
        
        return models

    @pytest.fixture
    def db_manager(self, mock_db, mock_cache, mock_models):
        # Inject dependencies
        manager = UkgDatabaseManager(
            tenant_id="test_tenant",
            db_session=mock_db,
            models_module=mock_models,
            cache_client=mock_cache
        )
        return manager

    def test_create_node_success(self, db_manager, mock_db, mock_models):
        node_data = {
            "uid": "node_1",
            "node_type": "concept",
            "label": "Test Node"
        }
        
        # Setup mock return for instantiation
        mock_instance = mock_models.Node.return_value
        mock_instance.uid = "node_1"
        mock_instance.created_at = datetime.now(UTC)
        mock_instance.updated_at = datetime.now(UTC)
        
        result = db_manager.create_node(node_data)
        
        assert result is not None
        assert result['uid'] == "node_1"
        mock_db.session.add.assert_called_with(mock_instance)
        mock_db.session.commit.assert_called_once()

    def test_get_node_cache_hit(self, db_manager, mock_cache):
        # Mock cache hit
        mock_cache.get.return_value = {"uid": "cached_node"}
        
        result = db_manager.get_node_by_uid("cached_node")
        assert result["uid"] == "cached_node"
        mock_cache.get.assert_called()

    def test_get_node_db_miss(self, db_manager, mock_db, mock_models):
        # Mock cache miss
        db_manager.cache.get.return_value = None
        
        # Mock DB miss
        mock_query = MagicMock()
        mock_db.session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None 
        
        result = db_manager.get_node_by_uid("missing_node")
        assert result is None

    def test_update_node_logic(self, db_manager, mock_db):
        # Mock finding the node
        mock_node = MagicMock()
        mock_node.to_dict.return_value = {"uid": "node_1", "label": "New Label"}
        
        mock_query = MagicMock()
        mock_db.session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_node
        
        result = db_manager.update_node("node_1", {"label": "New Label"})
        
        assert result["label"] == "New Label"
        assert mock_node.label == "New Label"
        mock_db.session.commit.assert_called()

    def test_delete_node(self, db_manager, mock_db):
        mock_node = MagicMock()
        mock_query = MagicMock()
        mock_db.session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_node
        
        result = db_manager.delete_node("node_1")
        
        assert result is True
        mock_db.session.delete.assert_called_with(mock_node)
        mock_db.session.commit.assert_called()

    def test_create_ka_execution_uses_current_schema(self, db_manager, mock_db):
        mock_execution = MagicMock()
        mock_execution.id = 1
        mock_execution.uid = "exec-1"
        mock_execution.ka_id = "KA-001"
        mock_execution.status = "completed"
        mock_execution.input_data = {"query": "test", "session_id": "session-1"}
        mock_execution.output_data = {"answer": "ok"}
        mock_execution.error_message = None
        mock_execution.execution_time_ms = 12
        mock_execution.tenant_id = "test_tenant"
        mock_execution.started_at = datetime(2026, 7, 4, tzinfo=UTC)
        mock_execution.completed_at = datetime(2026, 7, 4, 0, 0, 1, tzinfo=UTC)

        db_manager.KAExecution = MagicMock(return_value=mock_execution)
        mock_query = MagicMock()
        mock_db.session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = MagicMock()

        result = db_manager.create_ka_execution(
            {
                "execution_id": "exec-1",
                "ka_id": "KA-001",
                "session_id": "session-1",
                "params": {"query": "test"},
                "results": {"answer": "ok"},
                "duration_ms": 12.4,
                "status": "success",
                "start_time": "2026-07-04T00:00:00+00:00",
                "end_time": "2026-07-04T00:00:01+00:00",
            }
        )

        kwargs = db_manager.KAExecution.call_args.kwargs
        assert kwargs["uid"] == "exec-1"
        assert kwargs["ka_id"] == "KA-001"
        assert kwargs["status"] == "completed"
        assert kwargs["input_data"] == {"query": "test", "session_id": "session-1"}
        assert kwargs["output_data"] == {"answer": "ok"}
        assert kwargs["execution_time_ms"] == 12
        assert "algorithm_id" not in kwargs
        assert "execution_time" not in kwargs
        assert result["duration_ms"] == 12
        assert result["session_id"] == "session-1"
        mock_db.session.add.assert_called_with(mock_execution)
        mock_db.session.commit.assert_called()

    def test_get_ka_executions_returns_current_schema_dicts(self, db_manager, mock_db):
        mock_execution = MagicMock()
        mock_execution.id = 1
        mock_execution.uid = "exec-1"
        mock_execution.ka_id = "KA-001"
        mock_execution.status = "failed"
        mock_execution.input_data = {"query": "test"}
        mock_execution.output_data = None
        mock_execution.error_message = "boom"
        mock_execution.execution_time_ms = 15
        mock_execution.tenant_id = "test_tenant"
        mock_execution.started_at = datetime(2026, 7, 4, tzinfo=UTC)
        mock_execution.completed_at = datetime(2026, 7, 4, 0, 0, 1, tzinfo=UTC)

        db_manager.KAExecution = MagicMock()
        mock_query = MagicMock()
        mock_db.session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [mock_execution]

        result = db_manager.get_ka_executions({"ka_id": "KA-001"}, limit=10, offset=0)

        assert result == [
            {
                "id": 1,
                "uid": "exec-1",
                "execution_id": "exec-1",
                "ka_id": "KA-001",
                "session_id": None,
                "status": "failed",
                "input_data": {"query": "test"},
                "output_data": None,
                "results": None,
                "error_message": "boom",
                "error": "boom",
                "execution_time_ms": 15,
                "duration_ms": 15,
                "tenant_id": "test_tenant",
                "started_at": "2026-07-04T00:00:00+00:00",
                "completed_at": "2026-07-04T00:00:01+00:00",
                "start_time": "2026-07-04T00:00:00+00:00",
                "end_time": "2026-07-04T00:00:01+00:00",
            }
        ]
