import json

from backend.security.audit_logger import AuditLogger


def test_audit_logger_writes_and_verifies_immutable_replica(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AUDIT_IMMUTABLE_REPLICA_ENABLED", "true")
    monkeypatch.setenv("AUDIT_IMMUTABLE_HMAC_SECRET", "immutable-replica-secret")

    audit_logger = AuditLogger()
    audit_logger.stop_log_rotation()

    audit_logger.log_audit_event(event_type="test_replica_1", user_id="u1")
    audit_logger.log_audit_event(event_type="test_replica_2", user_id="u2")

    replica_file = tmp_path / audit_logger._immutable_log_file_path()
    assert replica_file.exists()

    result = audit_logger.verify_immutable_replica_integrity(str(replica_file))
    assert result["verified"] is True
    assert result["total_entries"] == 2
    assert result["invalid_entries"] == 0


def test_audit_logger_detects_immutable_replica_tampering(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AUDIT_IMMUTABLE_REPLICA_ENABLED", "true")
    monkeypatch.setenv("AUDIT_IMMUTABLE_HMAC_SECRET", "immutable-replica-secret")

    audit_logger = AuditLogger()
    audit_logger.stop_log_rotation()
    audit_logger.log_audit_event(event_type="test_replica_tamper", user_id="u9")

    replica_file = tmp_path / audit_logger._immutable_log_file_path()
    lines = replica_file.read_text(encoding="utf-8").splitlines()
    entry = json.loads(lines[0])
    entry["event"]["user_id"] = "tampered-user"
    replica_file.write_text(json.dumps(entry) + "\n", encoding="utf-8")

    result = audit_logger.verify_immutable_replica_integrity(str(replica_file))
    assert result["verified"] is False
    assert result["invalid_entries"] >= 1
