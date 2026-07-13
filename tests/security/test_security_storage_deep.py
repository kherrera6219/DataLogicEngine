
import pytest
import os
from datetime import datetime, UTC, timedelta
from unittest.mock import MagicMock, patch

# Import targets
from backend.security.session_manager import SessionManager
from backend.storage.connection_manager import ConnectionManager, ConnectionMode
from backend.storage.object_store import ObjectStore, LocalFileBackend

class TestSessionManager:
    @pytest.fixture
    def mock_redis(self):
        return MagicMock()

    @pytest.fixture
    def session_manager(self, mock_redis):
        return SessionManager(redis_client=mock_redis)

    def test_session_rotation(self, session_manager):
        class MockSession(dict):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.modified = False
        
        mock_session = MockSession()
        mock_session.update({'user_id': 1, 'session_id': 'old-id', 'last_rotation': (datetime.now(UTC) - timedelta(minutes=10)).isoformat()})
        
        with patch("backend.security.session_manager.session", mock_session):
            session_manager.rotate_session()
            assert mock_session.modified is True
            assert 'last_rotation' in mock_session
            # Verify it set a new rotation timestamp
            assert mock_session['last_rotation'] != (datetime.now(UTC) - timedelta(minutes=10)).isoformat()
            assert mock_session['user_id'] == 1

    def test_concurrent_session_limits(self, session_manager, mock_redis):
        user_id = 123
        # Mock 4 existing sessions (over limit of 3)
        mock_redis.smembers.return_value = ["s1", "s2", "s3", "s4"]
        
        # hgetall is called twice: once for sorting in enforce_session_limit 
        # and once in invalidate_session
        meta_s1 = {'created_at': (datetime.now(UTC) - timedelta(hours=4)).isoformat(), 'user_id': str(user_id)}
        meta_s2 = {'created_at': (datetime.now(UTC) - timedelta(hours=3)).isoformat(), 'user_id': str(user_id)}
        meta_s3 = {'created_at': (datetime.now(UTC) - timedelta(hours=2)).isoformat(), 'user_id': str(user_id)}
        meta_s4 = {'created_at': (datetime.now(UTC) - timedelta(hours=1)).isoformat(), 'user_id': str(user_id)}
        
        mock_redis.hgetall.side_effect = [
            meta_s1, meta_s2, meta_s3, meta_s4, # For sorting
            meta_s1                             # For invalidate_session(s1)
        ]
        
        session_manager.enforce_session_limit(user_id)
        
        # Verify attempt to delete oldest
        calls = [str(c) for c in mock_redis.delete.call_args_list]
        if not any("session:s1" in c for c in calls):
            print(f"DEBUG Redis calls: {calls}")
        mock_redis.delete.assert_any_call("session:s1")

class TestConnectionManager:
    @patch.dict(os.environ, {
        "DB_MODE": "cloud",
        "POSTGRES_HOST": "127.0.0.1",
        "POSTGRES_CLOUD_URL": "postgresql://external.example/ukg",
        "REDIS_CLOUD_URL": "rediss://external.example/0",
        "NEO4J_CLOUD_URL": "neo4j+s://external.example",
        "VECTOR_CLOUD_URL": "https://external-vector.example",
        "VECTOR_API_KEY": "key",
        "S3_ENDPOINT_URL": "https://external-object.example",
        "AWS_ACCESS_KEY_ID": "key",
    }, clear=False)
    def test_config_loading_uses_internal_database_model(self):
        # Reset singleton for test
        ConnectionManager._instance = None
        cm = ConnectionManager()
        assert cm.config.mode == ConnectionMode.AUTO
        assert cm.config.postgres.host == "127.0.0.1"
        report = cm.get_status_report()
        assert all(service["is_cloud"] is False for service in report["services"].values())
        assert {service["source"] for service in report["services"].values()} == {"internal"}

    def test_health_checks(self):
        cm = ConnectionManager()
        with patch.object(cm, "_check_postgres_health", return_value=True):
            assert cm.check_health('postgres') is True
        with patch.object(cm, "_check_redis_health", return_value=False):
            assert cm.check_health('redis') is False

class TestObjectStore:
    def test_local_backend_crud(self, tmp_path):
        backend = LocalFileBackend(base_path=str(tmp_path))
        bucket = "test-bucket"
        key = "docs/test.txt"
        data = b"Hello UKG"
        
        # Put
        backend.put(bucket, key, data, content_type="text/plain")
        assert backend.exists(bucket, key)
        
        # Get
        assert backend.get(bucket, key) == data
        
        # Info
        info = backend.get_info(bucket, key)
        assert info.key == key
        assert info.content_type == "text/plain"
        
        # List
        files = backend.list(bucket)
        assert len(files) == 1
        assert files[0].key == key
        
        # Delete
        backend.delete(bucket, key)
        assert not backend.exists(bucket, key)

    @patch("backend.storage.object_store.get_object_store")
    def test_store_singleton_selection(self, mock_get_store):
        # Verify ObjectStore remains internal even if stale external config is present.
        with patch("backend.storage.connection_manager.get_connection_manager") as mock_cm:
            mock_cm.return_value.config.object_storage.is_cloud = True
            mock_cm.return_value.config.object_storage.endpoint_url = None
            mock_cm.return_value.config.object_storage.access_key = "key"
            mock_cm.return_value.config.object_storage.secret_key = None
            mock_cm.return_value.config.object_storage.local_path = "databases/objects"
            
            with patch("backend.storage.object_store.S3Backend") as mock_s3:
                store = ObjectStore()
                assert not mock_s3.called
                assert isinstance(store._backend, LocalFileBackend)

    def test_supervisor_owned_s3_endpoint_is_selected(self):
        with patch("backend.storage.connection_manager.get_connection_manager") as mock_cm:
            config = mock_cm.return_value.config.object_storage
            config.endpoint_url = "http://127.0.0.1:22005"
            config.access_key = "DLEAPP12345678901234567890123456789012"
            config.secret_key = "secret-value"
            config.region = "us-east-1"
            with patch("backend.storage.object_store.S3Backend") as backend:
                ObjectStore()
                backend.assert_called_once_with(
                    config.endpoint_url,
                    config.access_key,
                    config.secret_key,
                    config.region,
                )
