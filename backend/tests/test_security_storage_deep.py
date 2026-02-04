
import pytest
import os
import json
import socket
from datetime import datetime, UTC, timedelta
from unittest.mock import MagicMock, patch, mock_open, ANY
from pathlib import Path

# Import targets
from backend.security.security_monitoring import SecurityMonitor, SecurityEventType, ThreatLevel, SecurityAlert
from backend.security.session_manager import SessionManager
from backend.storage.connection_manager import ConnectionManager, ConnectionMode, StorageConfig
from backend.storage.object_store import ObjectStore, LocalFileBackend, S3Backend, ObjectInfo

@pytest.fixture
def mock_audit_logger():
    return MagicMock()

@pytest.fixture
def security_monitor(mock_audit_logger, tmp_path):
    # Set alert file to tmp path
    alert_file = tmp_path / "alerts.jsonl"
    with patch("backend.security.security_monitoring.os.makedirs"):
        monitor = SecurityMonitor(audit_logger=mock_audit_logger)
        monitor.alert_file = str(alert_file)
        return monitor

class TestSecurityMonitoring:
    def test_alert_creation_and_persistence(self, security_monitor):
        alert = security_monitor.create_alert(
            event_type=SecurityEventType.SUSPICIOUS_LOGIN,
            threat_level=ThreatLevel.MEDIUM,
            message="Test alert",
            details={"ip": "1.2.3.4"}
        )
        
        assert alert.event_type == SecurityEventType.SUSPICIOUS_LOGIN
        assert alert.threat_level == ThreatLevel.MEDIUM
        assert len(security_monitor.alerts) == 1
        
        # Verify persistence
        assert os.path.exists(security_monitor.alert_file)
        with open(security_monitor.alert_file, 'r') as f:
            line = f.readline()
            saved_alert = json.loads(line)
            assert saved_alert['event_type'] == "suspicious_login"
            assert saved_alert['details']['ip'] == "1.2.3.4"

    def test_brute_force_detection(self, security_monitor):
        ip = "10.0.0.1"
        # 5 failed logins within 5 mins
        for _ in range(5):
            security_monitor.process_event(
                event_type=SecurityEventType.LOGIN_FAILURE,
                details={},
                ip_address=ip
            )
        
        # Should have created an alert
        alerts = security_monitor.get_alerts(event_type=SecurityEventType.LOGIN_BRUTE_FORCE)
        assert len(alerts) == 1
        assert security_monitor.is_ip_blocked(ip)

    def test_suspicious_pattern_detection(self, security_monitor):
        # SQL Injection
        security_monitor.process_event(
            event_type=SecurityEventType.ANOMALOUS_BEHAVIOR,
            details={"query": "' OR '1'='1"},
            ip_address="1.1.1.1"
        )
        assert len(security_monitor.get_alerts(event_type=SecurityEventType.SQL_INJECTION_ATTEMPT)) == 1
        
        # XSS
        security_monitor.process_event(
            event_type=SecurityEventType.ANOMALOUS_BEHAVIOR,
            details={"payload": "<script>alert(1)</script>"},
            ip_address="2.2.2.2"
        )
        assert len(security_monitor.get_alerts(event_type=SecurityEventType.XSS_ATTEMPT)) == 1

    def test_metrics(self, security_monitor):
        security_monitor.create_alert(SecurityEventType.COMPLIANCE_BREACH, ThreatLevel.CRITICAL, "Err", {})
        metrics = security_monitor.get_metrics()
        assert metrics['total_alerts'] == 1
        assert metrics['critical_alerts'] == 1

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
    @patch.dict(os.environ, {"DB_MODE": "cloud", "POSTGRES_HOST": "cloud-db"})
    def test_config_loading(self):
        # Reset singleton for test
        ConnectionManager._instance = None
        cm = ConnectionManager()
        assert cm.config.mode == ConnectionMode.CLOUD
        assert cm.config.postgres.host == "cloud-db"

    def test_health_checks(self):
        cm = ConnectionManager()
        with patch("socket.socket") as mock_sock:
            # Mock successful connection
            mock_sock.return_value.connect_ex.return_value = 0
            assert cm.check_health('postgres') is True
            
            # Mock failed connection
            mock_sock.return_value.connect_ex.return_value = 1
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
        # Verify ObjectStore selects backend correctly
        with patch("backend.storage.connection_manager.get_connection_manager") as mock_cm:
            mock_cm.return_value.config.object_storage.is_cloud = True
            mock_cm.return_value.config.object_storage.access_key = "key"
            
            with patch("backend.storage.object_store.S3Backend") as mock_s3:
                store = ObjectStore()
                assert mock_s3.called
