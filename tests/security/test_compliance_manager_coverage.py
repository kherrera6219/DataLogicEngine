from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import backend.security.compliance_manager as compliance_module


@pytest.fixture
def manager(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(compliance_module.SOC2ComplianceManager, "start_compliance_monitoring", lambda self: None)
    return compliance_module.SOC2ComplianceManager(config={"env": "test"})


def test_compliance_manager_initialization(manager):
    assert manager.config["env"] == "test"
    assert set(manager.compliance_state.keys()) == {
        "security",
        "availability",
        "processing_integrity",
        "confidentiality",
        "privacy",
    }
    assert Path("logs/compliance").exists()


def test_start_and_stop_monitoring_thread(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with patch("backend.security.compliance_manager.threading.Thread") as mock_thread:
        mgr = compliance_module.SOC2ComplianceManager()
        assert mgr.monitoring_active is True
        mock_thread.return_value.start.assert_called_once()

        mgr.stop_compliance_monitoring()
        assert mgr.monitoring_active is False
        mock_thread.return_value.join.assert_called_once()


def test_check_methods_update_state_and_log(manager):
    with patch.object(manager, "log_compliance_event") as log_event:
        manager._check_security_compliance()
        manager._check_availability_compliance()
        manager._check_processing_integrity_compliance()
        manager._check_confidentiality_compliance()
        manager._check_privacy_compliance()

    assert manager.compliance_state["security"]["status"] == "compliant"
    assert manager.compliance_state["availability"]["status"] == "compliant"
    assert manager.compliance_state["processing_integrity"]["status"] == "compliant"
    assert manager.compliance_state["confidentiality"]["status"] == "compliant"
    assert manager.compliance_state["privacy"]["status"] == "compliant"
    assert log_event.call_count == 5


def test_log_compliance_state_and_status(manager):
    manager._log_compliance_state()
    state_files = list(Path("logs/compliance").glob("state_*.json"))
    assert state_files

    status = manager.get_compliance_status()
    assert status["overall_status"] in {"compliant", "non_compliant"}
    assert "categories" in status

    manager.compliance_state["privacy"]["status"] = "non_compliant"
    status = manager.get_compliance_status()
    assert status["overall_status"] == "non_compliant"


def test_log_event_and_filtered_event_retrieval(manager):
    security_id = manager.log_compliance_event("security", "check", "security check complete")
    privacy_id = manager.log_compliance_event("privacy", "violation", "privacy event")
    assert security_id is not None
    assert privacy_id is not None

    all_events = manager.get_compliance_events(limit=100)
    assert len(all_events) >= 2

    security_events = manager.get_compliance_events(category="security")
    assert all(e["category"] == "security" for e in security_events)

    violation_events = manager.get_compliance_events(event_type="violation")
    assert all(e["type"] == "violation" for e in violation_events)

    start_time = datetime.now() + timedelta(days=1)
    future_filtered = manager.get_compliance_events(start_time=start_time)
    assert future_filtered == []


def test_get_compliance_events_handles_parse_errors(manager):
    events_file = Path("logs/compliance/events.jsonl")
    events_file.write_text("{bad-json-line}\n", encoding="utf-8")
    events = manager.get_compliance_events()
    assert events == []


def test_generate_compliance_report_with_counts(manager):
    now = datetime.now()
    sample_events = [
        {"timestamp": now.isoformat(), "category": "security", "type": "check", "details": "ok"},
        {"timestamp": now.isoformat(), "category": "security", "type": "violation", "details": "issue"},
        {"timestamp": now.isoformat(), "category": "availability", "type": "check", "details": "ok"},
    ]

    with patch.object(manager, "get_compliance_events", return_value=sample_events):
        report = manager.generate_compliance_report(start_date=now - timedelta(days=7), end_date=now)

    assert report["report_type"] == "SOC 2 Type 2"
    assert report["event_counts"]["security"]["check"] == 1
    assert report["event_counts"]["security"]["violation"] == 1
    assert "overall_compliance_score" in report

    report_file = Path("logs/compliance") / f"report_{(now - timedelta(days=7)).strftime('%Y%m%d')}_{now.strftime('%Y%m%d')}.json"
    assert report_file.exists()


def test_monitoring_loop_single_iteration(manager, monkeypatch):
    manager.monitoring_active = True

    for method_name in (
        "_check_security_compliance",
        "_check_availability_compliance",
        "_check_processing_integrity_compliance",
        "_check_confidentiality_compliance",
        "_check_privacy_compliance",
        "_log_compliance_state",
    ):
        monkeypatch.setattr(manager, method_name, MagicMock())

    def fake_sleep(_seconds):
        manager.monitoring_active = False

    monkeypatch.setattr(compliance_module.time, "sleep", fake_sleep)
    manager._compliance_monitoring_loop()

    manager._check_security_compliance.assert_called_once()
    manager._check_availability_compliance.assert_called_once()
    manager._check_processing_integrity_compliance.assert_called_once()
    manager._check_confidentiality_compliance.assert_called_once()
    manager._check_privacy_compliance.assert_called_once()
    manager._log_compliance_state.assert_called_once()
