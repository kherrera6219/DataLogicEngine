import pytest
import uuid
from unittest.mock import MagicMock, patch
from backend.ukg_db import UkgDatabaseManager

@pytest.fixture
def mock_db():
    mock = MagicMock()
    mock.session = MagicMock()
    return mock

@pytest.fixture
def mock_cache():
    return MagicMock()

@pytest.fixture
def db_manager(mock_db, mock_cache):
    # Patch at the ukg_db level to catch the imports
    with patch('backend.ukg_db.db', mock_db), \
         patch('backend.ukg_db.cache', mock_cache), \
         patch('backend.ukg_db.Node') as MockNode, \
         patch('backend.ukg_db.Edge') as MockEdge, \
         patch('backend.ukg_db.KAExecution') as MockKA:
        manager = UkgDatabaseManager(tenant_id="tenant-1")
        # Store mocks on the manager for easy access in tests if needed
        manager._mock_db = mock_db
        manager._mock_cache = mock_cache
        manager._MockNode = MockNode
        yield manager

def test_tenant_isolation_create(db_manager):
    """Verify that nodes are created with the correct tenant_id."""
    node_data = {
        'uid': 'node-123',
        'node_type': 'entity',
        'label': 'Test Node'
    }
    
    db_manager.create_node(node_data)
    
    # Verify that Node was instantiated with tenant_id="tenant-1"
    args, kwargs = db_manager._MockNode.call_args
    assert kwargs['tenant_id'] == "tenant-1"
    assert kwargs['uid'] == 'node-123'
    
    # Verify DB session operations
    db_manager._mock_db.session.add.assert_called_once()
    db_manager._mock_db.session.commit.assert_called_once()

def test_cache_hit(db_manager):
    """Verify that get_node_by_uid returns cached data if available."""
    uid = "node-cache-1"
    cached_node = {'uid': uid, 'label': 'Cached'}
    
    db_manager._mock_cache.get.return_value = cached_node
    
    result = db_manager.get_node_by_uid(uid)
    
    assert result == cached_node
    db_manager._mock_cache.get.assert_called_with(f"node:{uid}:tenant-1")
    # DB should NOT be queried
    db_manager._mock_db.session.query.assert_not_called()

def test_cache_miss_and_populate(db_manager):
    """Verify that cache is populated after a DB hit."""
    uid = "node-db-1"
    db_manager._mock_cache.get.return_value = None
    
    mock_node = MagicMock()
    mock_node.to_dict.return_value = {'uid': uid, 'label': 'From DB'}
    
    mock_query = db_manager._mock_db.session.query.return_value
    mock_filter1 = mock_query.filter.return_value
    mock_filter2 = mock_filter1.filter.return_value
    mock_filter2.first.return_value = mock_node
    
    result = db_manager.get_node_by_uid(uid)
    
    assert result['label'] == 'From DB'
    db_manager._mock_cache.set.assert_called_once()
    assert db_manager._mock_cache.set.call_args[0][0] == f"node:{uid}:tenant-1"

def test_update_invalidates_cache(db_manager):
    """Verify that updating a node invalidates its cache entry."""
    uid = "node-update-1"
    
    mock_node = MagicMock()
    mock_node.to_dict.return_value = {'uid': uid}
    
    mock_query = db_manager._mock_db.session.query.return_value
    mock_filter1 = mock_query.filter.return_value
    mock_filter2 = mock_filter1.filter.return_value
    mock_filter2.first.return_value = mock_node
    
    db_manager.update_node(uid, {'label': 'New Label'})
    
    db_manager._mock_db.session.commit.assert_called_once()
    db_manager._mock_cache.delete.assert_called_with(f"node:{uid}:tenant-1")

def test_delete_node_tenant_check(db_manager):
    """Verify that delete_node respects tenant isolation."""
    uid = "node-delete-1"
    
    mock_query = db_manager._mock_db.session.query.return_value
    mock_filter1 = mock_query.filter.return_value
    mock_filter2 = mock_filter1.filter.return_value
    mock_filter2.first.return_value = MagicMock()
    
    db_manager.delete_node(uid)
    
    assert db_manager._mock_db.session.delete.called
    assert db_manager._mock_db.session.commit.called
    db_manager._mock_cache.delete.assert_called_with(f"node:{uid}:tenant-1")
