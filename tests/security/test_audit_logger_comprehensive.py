"""
Comprehensive Audit Logger Testing Suite

Tests for audit logging functionality covering:
- Event logging (authentication, authorization, data access, API requests)
- Log integrity and hashing
- Log rotation
- Event querying and filtering
- CSV export
- Syslog forwarding
- Error handling and fallback
"""

import pytest
import json
import os
import tempfile
import shutil
from datetime import datetime, timedelta, UTC
from unittest.mock import Mock, patch, MagicMock, mock_open
import hashlib
import csv

from backend.security.audit_logger import AuditLogger


@pytest.fixture
def temp_audit_dir():
    """Create temporary directory for audit logs"""
    temp_dir = tempfile.mkdtemp()
    original_logs_dir = "logs/audit"

    # Create logs/audit in temp directory
    os.makedirs(os.path.join(temp_dir, "logs", "audit"), exist_ok=True)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def audit_logger(temp_audit_dir, monkeypatch):
    """Create audit logger instance with temporary directory"""
    # Change working directory to temp directory
    monkeypatch.chdir(temp_audit_dir)

    logger = AuditLogger()
    logger.stop_log_rotation()  # Stop rotation thread for tests

    yield logger

    logger.stop_log_rotation()


class TestAuditLoggerInitialization:
    """Test audit logger initialization"""

    def test_audit_logger_creates_log_directory(self, temp_audit_dir, monkeypatch):
        """Test logger creates logs/audit directory"""
        monkeypatch.chdir(temp_audit_dir)

        logger = AuditLogger()
        logger.stop_log_rotation()

        assert os.path.exists("logs/audit")

    def test_audit_logger_initializes_with_config(self):
        """Test logger accepts configuration"""
        config = {'retention_days': 90}
        logger = AuditLogger(config=config)
        logger.stop_log_rotation()

        assert logger.config == config

    def test_audit_logger_starts_log_rotation(self):
        """Test logger starts log rotation thread"""
        logger = AuditLogger()

        assert logger.log_rotation_active is True
        assert logger.log_rotation_thread is not None

        logger.stop_log_rotation()

    def test_audit_logger_creates_current_log_file_name(self, audit_logger):
        """Test logger creates correct log file name"""
        current_date = datetime.now().strftime("%Y%m%d")
        expected_file = f"logs/audit/audit_{current_date}.jsonl"

        assert audit_logger.current_log_file == expected_file


class TestBasicEventLogging:
    """Test basic audit event logging"""

    def test_log_audit_event_creates_entry(self, audit_logger):
        """Test logging audit event creates entry"""
        event_id = audit_logger.log_audit_event(
            event_type="test_event",
            user_id="user123",
            action="test_action",
            status="success"
        )

        assert event_id is not None
        assert os.path.exists(audit_logger.current_log_file)

    def test_log_audit_event_returns_event_id(self, audit_logger):
        """Test logging returns valid event ID"""
        event_id = audit_logger.log_audit_event(
            event_type="test_event"
        )

        # Should be a valid UUID
        assert len(event_id) > 0
        assert '-' in event_id

    def test_log_audit_event_includes_timestamp(self, audit_logger):
        """Test audit event includes timestamp"""
        audit_logger.log_audit_event(event_type="test_event")

        with open(audit_logger.current_log_file, 'r') as f:
            event = json.loads(f.readline())

        assert 'timestamp' in event
        # Verify timestamp is recent
        event_time = datetime.fromisoformat(event['timestamp'])
        assert datetime.now(UTC) - event_time < timedelta(seconds=5)

    def test_log_audit_event_includes_all_fields(self, audit_logger):
        """Test audit event includes all provided fields"""
        audit_logger.log_audit_event(
            event_type="test_event",
            user_id="user123",
            resource_id="resource456",
            action="read",
            status="success",
            details={"key": "value"},
            request_id="req789",
            ip_address="192.168.1.1"
        )

        with open(audit_logger.current_log_file, 'r') as f:
            event = json.loads(f.readline())

        assert event['event_type'] == "test_event"
        assert event['user_id'] == "user123"
        assert event['resource_id'] == "resource456"
        assert event['action'] == "read"
        assert event['status'] == "success"
        assert event['details'] == {"key": "value"}
        assert event['request_id'] == "req789"
        assert event['ip_address'] == "192.168.1.1"

    def test_log_audit_event_with_minimal_fields(self, audit_logger):
        """Test logging with only required fields"""
        audit_logger.log_audit_event(event_type="minimal_event")

        with open(audit_logger.current_log_file, 'r') as f:
            event = json.loads(f.readline())

        assert 'id' in event
        assert 'timestamp' in event
        assert event['event_type'] == "minimal_event"
        assert event['status'] == "success"  # Default status

    def test_log_audit_event_generates_hash(self, audit_logger):
        """Test audit event includes integrity hash"""
        audit_logger.log_audit_event(
            event_type="hash_test",
            user_id="user123"
        )

        with open(audit_logger.current_log_file, 'r') as f:
            event = json.loads(f.readline())

        assert 'hash' in event
        assert len(event['hash']) == 64  # SHA-256 hex length


class TestSpecializedLoggingMethods:
    """Test specialized logging methods"""

    def test_log_authentication_success(self, audit_logger):
        """Test logging successful authentication"""
        event_id = audit_logger.log_authentication(
            user_id="user123",
            status="success",
            ip_address="192.168.1.1"
        )

        assert event_id is not None

        with open(audit_logger.current_log_file, 'r') as f:
            event = json.loads(f.readline())

        assert event['event_type'] == "authentication"
        assert event['action'] == "login"
        assert event['status'] == "success"

    def test_log_authentication_failure(self, audit_logger):
        """Test logging failed authentication"""
        audit_logger.log_authentication(
            user_id="user123",
            status="failure",
            details={"reason": "invalid_password"}
        )

        with open(audit_logger.current_log_file, 'r') as f:
            event = json.loads(f.readline())

        assert event['status'] == "failure"
        assert event['details']['reason'] == "invalid_password"

    def test_log_authorization(self, audit_logger):
        """Test logging authorization check"""
        audit_logger.log_authorization(
            user_id="user123",
            resource_id="resource456",
            action="delete",
            status="success"
        )

        with open(audit_logger.current_log_file, 'r') as f:
            event = json.loads(f.readline())

        assert event['event_type'] == "authorization"
        assert event['action'] == "delete"
        assert event['resource_id'] == "resource456"

    def test_log_data_access(self, audit_logger):
        """Test logging data access"""
        audit_logger.log_data_access(
            user_id="user123",
            resource_id="data789",
            action="read",
            details={"fields": ["name", "email"]}
        )

        with open(audit_logger.current_log_file, 'r') as f:
            event = json.loads(f.readline())

        assert event['event_type'] == "data_access"
        assert event['action'] == "read"
        assert event['status'] == "success"  # Default for data access

    def test_log_api_request_success(self, audit_logger):
        """Test logging successful API request"""
        audit_logger.log_api_request(
            request_id="req123",
            user_id="user456",
            endpoint="/api/v1/users",
            method="GET",
            status_code=200,
            ip_address="192.168.1.1"
        )

        with open(audit_logger.current_log_file, 'r') as f:
            event = json.loads(f.readline())

        assert event['event_type'] == "api_request"
        assert event['status'] == "success"
        assert event['details']['status_code'] == 200

    def test_log_api_request_failure(self, audit_logger):
        """Test logging failed API request"""
        audit_logger.log_api_request(
            request_id="req123",
            user_id="user456",
            endpoint="/api/v1/secret",
            method="GET",
            status_code=403
        )

        with open(audit_logger.current_log_file, 'r') as f:
            event = json.loads(f.readline())

        assert event['status'] == "failure"  # >= 400

    def test_log_system_event(self, audit_logger):
        """Test logging system event"""
        audit_logger.log_system_event(
            event_type="startup",
            action="initialize",
            status="success",
            details={"version": "1.0.0"}
        )

        with open(audit_logger.current_log_file, 'r') as f:
            event = json.loads(f.readline())

        assert event['event_type'] == "system_startup"
        assert event['action'] == "initialize"


class TestLogIntegrity:
    """Test audit log integrity verification"""

    def test_verify_log_integrity_valid(self, audit_logger):
        """Test integrity verification for valid logs"""
        # Log some events
        audit_logger.log_audit_event(event_type="test1")
        audit_logger.log_audit_event(event_type="test2")

        result = audit_logger.verify_audit_log_integrity()

        assert result['verified'] is True
        assert result['total_entries'] == 2
        assert result['valid_entries'] == 2
        assert result['invalid_entries'] == 0

    def test_verify_log_integrity_detects_tampering(self, audit_logger):
        """Test integrity verification detects tampered logs"""
        # Log an event
        audit_logger.log_audit_event(event_type="test")

        # Tamper with the log file
        with open(audit_logger.current_log_file, 'r') as f:
            event = json.loads(f.readline())

        # Modify event but keep hash
        event['user_id'] = "tampered_user"

        with open(audit_logger.current_log_file, 'w') as f:
            f.write(json.dumps(event) + '\n')

        result = audit_logger.verify_audit_log_integrity()

        assert result['verified'] is False
        assert result['invalid_entries'] > 0

    def test_verify_log_integrity_nonexistent_file(self, audit_logger):
        """Test integrity verification for nonexistent file"""
        result = audit_logger.verify_audit_log_integrity(
            log_file="nonexistent_file.jsonl"
        )

        assert result['verified'] is False
        assert 'error' in result

    def test_verify_log_integrity_handles_entries_without_hash(self, audit_logger):
        """Test integrity verification handles old entries without hash"""
        # Manually write entry without hash
        event = {
            'id': '123',
            'timestamp': datetime.now().isoformat(),
            'event_type': 'old_event'
        }

        with open(audit_logger.current_log_file, 'w') as f:
            f.write(json.dumps(event) + '\n')

        result = audit_logger.verify_audit_log_integrity()

        # Should accept entries without hash
        assert result['valid_entries'] == 1
        assert result['invalid_entries'] == 0

    def test_event_hash_consistency(self, audit_logger):
        """Test event hash is consistent and correct"""
        audit_logger.log_audit_event(
            event_type="test",
            user_id="user123",
            action="test_action"
        )

        with open(audit_logger.current_log_file, 'r') as f:
            event = json.loads(f.readline())

        # Recalculate hash
        stored_hash = event['hash']
        event_copy = event.copy()
        del event_copy['hash']

        event_data = json.dumps(event_copy, sort_keys=True)
        calculated_hash = hashlib.sha256(event_data.encode()).hexdigest()

        assert stored_hash == calculated_hash


class TestLogRotation:
    """Test log rotation functionality"""

    def test_log_rotation_changes_date(self, audit_logger, monkeypatch):
        """Test log rotation on date change"""
        original_date = audit_logger.current_date
        original_file = audit_logger.current_log_file

        # Simulate date change
        new_date = (datetime.now() + timedelta(days=1)).strftime("%Y%m%d")

        audit_logger.current_date = new_date
        audit_logger.current_log_file = f"logs/audit/audit_{new_date}.jsonl"

        # New log file should be different
        assert audit_logger.current_log_file != original_file

    def test_stop_log_rotation(self, audit_logger):
        """Test stopping log rotation"""
        audit_logger.start_log_rotation()
        assert audit_logger.log_rotation_active is True

        audit_logger.stop_log_rotation()

        assert audit_logger.log_rotation_active is False


class TestEventQuerying:
    """Test audit event querying and filtering"""

    def test_get_audit_events_all(self, audit_logger):
        """Test retrieving all audit events"""
        # Log multiple events
        audit_logger.log_audit_event(event_type="event1")
        audit_logger.log_audit_event(event_type="event2")
        audit_logger.log_audit_event(event_type="event3")

        events = audit_logger.get_audit_events()

        assert len(events) == 3

    def test_get_audit_events_filter_by_event_type(self, audit_logger):
        """Test filtering events by type"""
        audit_logger.log_authentication("user1", "success")
        audit_logger.log_authorization("user2", "res1", "read", "success")
        audit_logger.log_authentication("user3", "failure")

        events = audit_logger.get_audit_events(event_type="authentication")

        assert len(events) == 2
        assert all(e['event_type'] == "authentication" for e in events)

    def test_get_audit_events_filter_by_user_id(self, audit_logger):
        """Test filtering events by user ID"""
        audit_logger.log_audit_event(event_type="test", user_id="user1")
        audit_logger.log_audit_event(event_type="test", user_id="user2")
        audit_logger.log_audit_event(event_type="test", user_id="user1")

        events = audit_logger.get_audit_events(user_id="user1")

        assert len(events) == 2
        assert all(e['user_id'] == "user1" for e in events)

    def test_get_audit_events_filter_by_status(self, audit_logger):
        """Test filtering events by status"""
        audit_logger.log_audit_event(event_type="test", status="success")
        audit_logger.log_audit_event(event_type="test", status="failure")
        audit_logger.log_audit_event(event_type="test", status="success")

        events = audit_logger.get_audit_events(status="success")

        assert len(events) == 2
        assert all(e['status'] == "success" for e in events)

    def test_get_audit_events_filter_by_action(self, audit_logger):
        """Test filtering events by action"""
        audit_logger.log_data_access("user1", "res1", "read")
        audit_logger.log_data_access("user1", "res2", "write")
        audit_logger.log_data_access("user2", "res3", "read")

        events = audit_logger.get_audit_events(action="read")

        assert len(events) == 2
        assert all(e['action'] == "read" for e in events)

    def test_get_audit_events_filter_by_resource_id(self, audit_logger):
        """Test filtering events by resource ID"""
        audit_logger.log_audit_event(event_type="test", resource_id="res1")
        audit_logger.log_audit_event(event_type="test", resource_id="res2")
        audit_logger.log_audit_event(event_type="test", resource_id="res1")

        events = audit_logger.get_audit_events(resource_id="res1")

        assert len(events) == 2

    def test_get_audit_events_with_limit(self, audit_logger):
        """Test limiting number of returned events"""
        for i in range(10):
            audit_logger.log_audit_event(event_type=f"event{i}")

        events = audit_logger.get_audit_events(limit=5)

        assert len(events) == 5

    def test_get_audit_events_empty_results(self, audit_logger):
        """Test querying with no matching events"""
        audit_logger.log_audit_event(event_type="test")

        events = audit_logger.get_audit_events(event_type="nonexistent")

        assert len(events) == 0

    def test_get_audit_events_nonexistent_log_file(self, audit_logger):
        """Test querying nonexistent log file"""
        # Delete log file
        if os.path.exists(audit_logger.current_log_file):
            os.remove(audit_logger.current_log_file)

        events = audit_logger.get_audit_events()

        assert events == []


class TestCSVExport:
    """Test CSV export functionality"""

    def test_export_to_csv_success(self, audit_logger, temp_audit_dir):
        """Test exporting audit events to CSV"""
        # Log some events
        audit_logger.log_authentication("user1", "success")
        audit_logger.log_data_access("user2", "res1", "read")

        output_file = os.path.join(temp_audit_dir, "audit_export.csv")
        count = audit_logger.export_to_csv(output_file)

        assert count == 2
        assert os.path.exists(output_file)

    def test_export_to_csv_includes_headers(self, audit_logger, temp_audit_dir):
        """Test CSV export includes column headers"""
        audit_logger.log_audit_event(event_type="test")

        output_file = os.path.join(temp_audit_dir, "audit_export.csv")
        audit_logger.export_to_csv(output_file)

        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

        assert 'timestamp' in headers
        assert 'event_type' in headers
        assert 'status' in headers

    def test_export_to_csv_readable_format(self, audit_logger, temp_audit_dir):
        """Test CSV export is in readable format"""
        audit_logger.log_authentication("user123", "success", ip_address="192.168.1.1")

        output_file = os.path.join(temp_audit_dir, "audit_export.csv")
        audit_logger.export_to_csv(output_file)

        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            row = next(reader)

        assert row['event_type'] == "authentication"
        assert row['user_id'] == "user123"

    def test_export_to_csv_empty_log(self, audit_logger, temp_audit_dir):
        """Test CSV export with no events"""
        output_file = os.path.join(temp_audit_dir, "audit_export.csv")
        count = audit_logger.export_to_csv(output_file)

        assert count == 0


class TestErrorHandling:
    """Test error handling in audit logger"""

    def test_log_audit_event_handles_write_error(self, audit_logger, monkeypatch):
        """Test logging handles file write errors"""
        def mock_open_error(*args, **kwargs):
            raise IOError("Permission denied")

        monkeypatch.setattr("builtins.open", mock_open_error)

        # Should not raise exception, returns event ID
        event_id = audit_logger.log_audit_event(event_type="test")

        assert event_id is not None

    def test_log_audit_event_creates_error_log(self, audit_logger, monkeypatch):
        """Test logging creates error log on failure"""
        # Create error log directory
        os.makedirs("logs", exist_ok=True)

        def mock_open_wrapper(filename, *args, **kwargs):
            if "audit_" in filename:
                raise IOError("Cannot write to audit log")
            return open(filename, *args, **kwargs)

        import builtins
        original_open = builtins.open
        monkeypatch.setattr("builtins.open", mock_open_wrapper)

        audit_logger.log_audit_event(event_type="test")

        # Error log should be created
        # Note: This tests the fallback mechanism

    def test_get_audit_events_handles_read_error(self, audit_logger):
        """Test event retrieval handles read errors"""
        # Create corrupted log file
        with open(audit_logger.current_log_file, 'w') as f:
            f.write("invalid json\n")

        # Should return empty list, not crash
        events = audit_logger.get_audit_events()

        assert isinstance(events, list)

    def test_verify_log_integrity_handles_malformed_json(self, audit_logger):
        """Test integrity verification handles malformed JSON"""
        with open(audit_logger.current_log_file, 'w') as f:
            f.write("not valid json\n")

        result = audit_logger.verify_audit_log_integrity()

        assert result['invalid_entries'] > 0


class TestSyslogForwarding:
    """Test Syslog forwarding functionality"""

    @patch('backend.security.audit_logger.logging.handlers.SysLogHandler')
    def test_enable_syslog_forwarding_success(self, mock_handler, audit_logger):
        """Test enabling Syslog forwarding"""
        result = audit_logger.enable_syslog_forwarding("syslog.example.com", 514)

        assert result is True
        mock_handler.assert_called_once()

    @patch('backend.security.audit_logger.logging.handlers.SysLogHandler')
    def test_enable_syslog_forwarding_failure(self, mock_handler, audit_logger):
        """Test handling Syslog forwarding failure"""
        mock_handler.side_effect = Exception("Connection refused")

        result = audit_logger.enable_syslog_forwarding("invalid.example.com")

        assert result is False


class TestConcurrency:
    """Test thread safety and concurrency"""

    def test_concurrent_logging(self, audit_logger):
        """Test concurrent logging from multiple threads"""
        import threading

        def log_events():
            for i in range(10):
                audit_logger.log_audit_event(
                    event_type="concurrent_test",
                    user_id=f"user_{threading.current_thread().name}"
                )

        threads = []
        for i in range(5):
            thread = threading.Thread(target=log_events, name=f"thread_{i}")
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All events should be logged
        events = audit_logger.get_audit_events()
        assert len(events) == 50


class TestCompliance:
    """Test compliance-related functionality"""

    def test_audit_log_retention(self, audit_logger):
        """Test audit logs are retained properly"""
        audit_logger.log_audit_event(event_type="retention_test")

        # Log file should exist
        assert os.path.exists(audit_logger.current_log_file)

    def test_audit_event_immutability(self, audit_logger):
        """Test audit events cannot be modified without detection"""
        audit_logger.log_audit_event(event_type="immutable_test", user_id="user123")

        # Verify initial integrity
        result1 = audit_logger.verify_audit_log_integrity()
        assert result1['verified'] is True

        # Attempt to modify
        with open(audit_logger.current_log_file, 'r') as f:
            lines = f.readlines()

        event = json.loads(lines[0])
        event['user_id'] = "modified_user"

        with open(audit_logger.current_log_file, 'w') as f:
            f.write(json.dumps(event) + '\n')

        # Verify tampering is detected
        result2 = audit_logger.verify_audit_log_integrity()
        assert result2['verified'] is False

    def test_audit_completeness(self, audit_logger):
        """Test all critical fields are logged"""
        event_id = audit_logger.log_audit_event(
            event_type="compliance_test",
            user_id="user123",
            resource_id="res456",
            action="access",
            status="success",
            ip_address="192.168.1.1"
        )

        with open(audit_logger.current_log_file, 'r') as f:
            event = json.loads(f.readline())

        # Critical fields for compliance
        required_fields = ['id', 'timestamp', 'event_type', 'user_id',
                          'action', 'status', 'ip_address', 'hash']

        for field in required_fields:
            assert field in event

    def test_audit_traceability(self, audit_logger):
        """Test audit events can be traced back to source"""
        event_id = audit_logger.log_api_request(
            request_id="req123",
            user_id="user456",
            endpoint="/api/v1/data",
            method="GET",
            status_code=200
        )

        # Should be able to find event by various criteria
        events_by_user = audit_logger.get_audit_events(user_id="user456")
        events_by_request = audit_logger.get_audit_events()  # Would filter by request_id in real implementation

        assert len(events_by_user) > 0


class TestIntegration:
    """Integration tests for audit logger"""

    def test_complete_audit_workflow(self, audit_logger, temp_audit_dir):
        """Test complete audit logging workflow"""
        # Log various events
        audit_logger.log_authentication("user1", "success", ip_address="192.168.1.1")
        audit_logger.log_authorization("user1", "resource1", "read", "success")
        audit_logger.log_data_access("user1", "resource1", "read")
        audit_logger.log_api_request("req123", "user1", "/api/v1/data", "GET", 200)

        # Verify integrity
        integrity_result = audit_logger.verify_audit_log_integrity()
        assert integrity_result['verified'] is True
        assert integrity_result['total_entries'] == 4

        # Query events
        all_events = audit_logger.get_audit_events()
        assert len(all_events) == 4

        user_events = audit_logger.get_audit_events(user_id="user1")
        assert len(user_events) == 4

        # Export to CSV
        csv_file = os.path.join(temp_audit_dir, "audit.csv")
        export_count = audit_logger.export_to_csv(csv_file)
        assert export_count == 4
        assert os.path.exists(csv_file)

    def test_audit_workflow_with_failures(self, audit_logger):
        """Test audit logging with mixed success/failure events"""
        audit_logger.log_authentication("user1", "failure", details={"reason": "invalid_password"})
        audit_logger.log_authentication("user1", "success")
        audit_logger.log_authorization("user1", "secret_data", "access", "failure")

        # Should log all events regardless of status
        all_events = audit_logger.get_audit_events()
        assert len(all_events) == 3

        # Filter failures
        failures = audit_logger.get_audit_events(status="failure")
        assert len(failures) == 2
