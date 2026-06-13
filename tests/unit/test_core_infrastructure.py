
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import SQLAlchemyError
from backend.ukg_db import UkgDatabaseManager
from backend.truth_engine.truth_core.engine import TruthCoreEngine

class TestUkgDatabaseManager:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def mock_cache(self):
        return MagicMock()

    @pytest.fixture
    def db_manager(self, mock_db, mock_cache):
        # tenant_id is the first arg
        return UkgDatabaseManager("test_tenant", db_session=mock_db, cache_client=mock_cache)

    def test_create_node_success(self, db_manager, mock_db):
        node_data = {
            'uid': 'node-1',
            'node_type': 'concept',
            'label': 'Test Node'
        }
        mock_node = MagicMock()
        mock_node.uid = 'node-1'
        mock_node.created_at = None
        mock_node.updated_at = None

        with patch.object(db_manager, 'Node', return_value=mock_node):
            result = db_manager.create_node(node_data)
            assert result['uid'] == 'node-1'
            assert mock_db.session.add.called
            assert mock_db.session.commit.called

    def test_create_node_failure(self, db_manager, mock_db):
        mock_db.session.commit.side_effect = SQLAlchemyError("DB Error")
        with patch.object(db_manager, 'Node', MagicMock()):
            result = db_manager.create_node({'uid': 'fail'})
            assert result is None
            assert mock_db.session.rollback.called

    def test_get_node_by_uid_cached(self, db_manager, mock_cache):
        mock_cache.get.return_value = {'uid': 'cached-node'}
        result = db_manager.get_node_by_uid('cached-node')
        assert result['uid'] == 'cached-node'
        
    def test_get_node_by_uid_db(self, db_manager, mock_db, mock_cache):
        mock_cache.get.return_value = None
        mock_node = MagicMock()
        mock_node.to_dict.return_value = {'uid': 'db-node'}
        
        mock_query = mock_db.session.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_node
        
        result = db_manager.get_node_by_uid('db-node')
        assert result['uid'] == 'db-node'
        assert mock_cache.set.called

    def test_create_edge_success(self, db_manager, mock_db):
        edge_data = {'uid': 'edge-1', 'source_uid': 'n1', 'target_uid': 'n2'}
        mock_edge = MagicMock()
        mock_edge.uid = 'edge-1'
        mock_edge.to_dict.return_value = {'uid': 'edge-1'}
        
        # Mock source and target nodes
        mock_node = MagicMock()
        mock_node.id = 1
        mock_db.session.query.return_value.filter.return_value.first.return_value = mock_node
        
        with patch.object(db_manager, 'Edge', return_value=mock_edge):
            result = db_manager.create_edge(edge_data)
            assert result['uid'] == 'edge-1'
            assert mock_db.session.commit.called

class TestTruthCoreEngine:
    @pytest.fixture
    def engine(self):
        # Mock dependencies that __init__ uses
        mock_db = MagicMock()
        with patch("backend.truth_engine.truth_core.engine.PersonaEnhancer", MagicMock()), \
             patch("backend.truth_engine.truth_core.engine.PersonaSufficiencyTool", MagicMock()), \
             patch("backend.truth_engine.truth_core.engine.RefinementOrchestrator", MagicMock()):
            engine = TruthCoreEngine(db_session=mock_db)
            return engine

    def test_engine_initialization(self, engine):
        assert engine.db_session is not None

    @pytest.mark.asyncio
    async def test_determine_tier(self, engine):
        # Using a simple query that might hit Trivial tier
        tier = await engine.determine_tier("What is the time?")
        assert isinstance(tier, str)

    @pytest.mark.asyncio
    @patch("backend.truth_engine.truth_core.engine.AsyncMock", create=True)
    async def test_process_session(self, mock_async_class, engine):
        # Mocking process logic
        with patch.object(engine, "get_session_status", return_value={"status": "ready"}), \
             patch.object(engine, "_execute_workflow", return_value=MagicMock()):
            result = await engine.process("session-123")
            assert result is not None
