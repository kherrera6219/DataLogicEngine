"""
Tests for backend.security.compliance_manager.SOC2ComplianceManager.

Coverage:
- Initialization and thread lifecycle
- Real SC-1..SC-5 check methods: compliant (happy-path) and non-compliant paths
- Event logging, filtering, and state persistence
- Report generation
"""
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import backend.security.compliance_manager as compliance_module


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def manager(tmp_path, monkeypatch):
    """Manager with monitoring disabled and CWD set to an isolated tmp directory."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        compliance_module.SOC2ComplianceManager,
        "start_compliance_monitoring",
        lambda self: None,
    )
    return compliance_module.SOC2ComplianceManager(config={"env": "test"})


def _make_route_files(base: Path) -> None:
    """Create the route stubs that SC-5 looks for."""
    routes_dir = base / "routes"
    routes_dir.mkdir(parents=True, exist_ok=True)
    (routes_dir / "user_data_routes.py").write_text(
        "# stub\n@bp.route('/export')\n@bp.route('/delete')\n"
    )
    backend_routes = base / "backend" / "routes"
    backend_routes.mkdir(parents=True, exist_ok=True)
    (backend_routes / "settings_routes.py").write_text(
        "# stub\nai_processing_enabled = True\n"
    )


# ---------------------------------------------------------------------------
# Initialization and thread lifecycle
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# SC-1 — Security (real checks)
# ---------------------------------------------------------------------------


def test_security_check_compliant(manager, tmp_path, monkeypatch):
    """SC-1 passes when key is set, rotation not needed, and audit dir is writable."""
    monkeypatch.setenv("ENCRYPTION_KEK_SECRET", "a-strong-32-char-production-key!")
    mock_mgr = MagicMock()
    mock_mgr.get_key_status.return_value = {"rotation_needed": False, "days_until_rotation": 45}

    # get_encryption_manager is a module-level name — patchable directly
    monkeypatch.setattr(compliance_module, "get_encryption_manager", lambda: mock_mgr)

    manager._check_security_compliance()

    assert manager.compliance_state["security"]["status"] == "compliant"
    assert "issues" not in manager.compliance_state["security"]


def test_security_check_non_compliant_missing_key(manager, monkeypatch):
    """SC-1 fails when ENCRYPTION_KEK_SECRET is not set."""
    monkeypatch.delenv("ENCRYPTION_KEK_SECRET", raising=False)

    with patch("backend.security.compliance_manager.get_encryption_manager") as mock_em:
        mock_em.return_value.get_key_status.return_value = {"rotation_needed": False}
        manager._check_security_compliance()

    assert manager.compliance_state["security"]["status"] == "non_compliant"
    issues = manager.compliance_state["security"]["issues"]
    assert any("ENCRYPTION_KEK_SECRET" in i for i in issues)


def test_security_check_non_compliant_dev_key(manager, monkeypatch):
    """SC-1 fails when ENCRYPTION_KEK_SECRET is a known dev default."""
    monkeypatch.setenv("ENCRYPTION_KEK_SECRET", "password")

    with patch("backend.security.compliance_manager.get_encryption_manager") as mock_em:
        mock_em.return_value.get_key_status.return_value = {"rotation_needed": False}
        manager._check_security_compliance()

    assert manager.compliance_state["security"]["status"] == "non_compliant"
    issues = manager.compliance_state["security"]["issues"]
    assert any("development default" in i for i in issues)


def test_security_check_non_compliant_rotation_overdue(manager, monkeypatch):
    """SC-1 fails when the encryption key rotation is overdue."""
    monkeypatch.setenv("ENCRYPTION_KEK_SECRET", "a-strong-32-char-production-key!")
    mock_mgr = MagicMock()
    mock_mgr.get_key_status.return_value = {
        "rotation_needed": True,
        "days_until_rotation": -5,
    }

    with patch(
        "backend.security.compliance_manager.get_encryption_manager",
        return_value=mock_mgr,
    ):
        manager._check_security_compliance()

    assert manager.compliance_state["security"]["status"] == "non_compliant"
    issues = manager.compliance_state["security"]["issues"]
    assert any("rotation overdue" in i for i in issues)


# ---------------------------------------------------------------------------
# SC-2 — Availability (real checks)
# ---------------------------------------------------------------------------


def _mock_db_ok():
    """Return a mock db whose engine.connect() succeeds."""
    mock_conn = MagicMock()
    mock_conn.__enter__ = lambda s: s
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_engine = MagicMock()
    mock_engine.connect.return_value = mock_conn
    mock_db = MagicMock()
    mock_db.engine = mock_engine
    mock_db.text = MagicMock(return_value="SELECT 1")
    return mock_db


def test_availability_check_compliant(manager):
    """SC-2 passes when DB is reachable and no violation spike."""
    with patch("backend.security.compliance_manager.db", _mock_db_ok(), create=True):
        manager._check_availability_compliance()

    assert manager.compliance_state["availability"]["status"] == "compliant"


def test_availability_check_non_compliant_db_failure(manager):
    """SC-2 fails when the database connection raises."""
    mock_db = MagicMock()
    mock_db.engine.connect.side_effect = Exception("Connection refused")
    mock_db.text = MagicMock(return_value="SELECT 1")

    with patch("backend.security.compliance_manager.db", mock_db, create=True):
        manager._check_availability_compliance()

    assert manager.compliance_state["availability"]["status"] == "non_compliant"
    issues = manager.compliance_state["availability"]["issues"]
    assert any("Database connection failed" in i for i in issues)


def test_availability_check_non_compliant_violation_spike(manager):
    """SC-2 fails when there are too many violations in the last hour."""
    # Create 10 violation events so the spike threshold (default 10) is hit
    fake_violations = [{"category": "security", "type": "violation"}] * 10

    with (
        patch("backend.security.compliance_manager.db", _mock_db_ok(), create=True),
        patch.object(manager, "get_compliance_events", return_value=fake_violations),
    ):
        manager._check_availability_compliance()

    assert manager.compliance_state["availability"]["status"] == "non_compliant"
    issues = manager.compliance_state["availability"]["issues"]
    assert any("violation spike" in i for i in issues)


# ---------------------------------------------------------------------------
# SC-3 — Processing Integrity (real checks)
# ---------------------------------------------------------------------------


def _mock_alembic_at_head(monkeypatch, tmp_path):
    """Patch Alembic so that current revision == head."""
    mock_script = MagicMock()
    mock_script.get_current_head.return_value = "abc123head"

    mock_ctx = MagicMock()
    mock_ctx.get_current_revision.return_value = "abc123head"

    monkeypatch.setattr(
        "backend.security.compliance_manager.ScriptDirectory",
        MagicMock(from_config=MagicMock(return_value=mock_script)),
    )
    monkeypatch.setattr(
        "backend.security.compliance_manager.MigrationContext",
        MagicMock(configure=MagicMock(return_value=mock_ctx)),
    )
    monkeypatch.setattr(
        "backend.security.compliance_manager.AlembicConfig",
        MagicMock(return_value=MagicMock()),
    )


def test_processing_integrity_check_compliant(manager, tmp_path, monkeypatch):
    """SC-3 passes when migration is at head and no hash chain rows exist."""
    mock_db = _mock_db_ok()
    mock_db.session = MagicMock()
    mock_db.session.query.return_value.order_by.return_value.first.return_value = None

    _mock_alembic_at_head(monkeypatch, tmp_path)

    with patch("backend.security.compliance_manager.db", mock_db, create=True):
        manager._check_processing_integrity_compliance()

    assert manager.compliance_state["processing_integrity"]["status"] == "compliant"


def test_processing_integrity_check_non_compliant_migration(manager, monkeypatch, tmp_path):
    """SC-3 fails when the migration is behind head."""
    mock_script = MagicMock()
    mock_script.get_current_head.return_value = "newerhead"

    mock_ctx = MagicMock()
    mock_ctx.get_current_revision.return_value = "oldrev"

    monkeypatch.setattr(
        "backend.security.compliance_manager.ScriptDirectory",
        MagicMock(from_config=MagicMock(return_value=mock_script)),
    )
    monkeypatch.setattr(
        "backend.security.compliance_manager.MigrationContext",
        MagicMock(configure=MagicMock(return_value=mock_ctx)),
    )
    monkeypatch.setattr(
        "backend.security.compliance_manager.AlembicConfig",
        MagicMock(return_value=MagicMock()),
    )
    mock_db = _mock_db_ok()
    mock_db.session = MagicMock()
    mock_db.session.query.return_value.order_by.return_value.first.return_value = None

    with patch("backend.security.compliance_manager.db", mock_db, create=True):
        manager._check_processing_integrity_compliance()

    assert manager.compliance_state["processing_integrity"]["status"] == "non_compliant"
    issues = manager.compliance_state["processing_integrity"]["issues"]
    assert any("not at head" in i for i in issues)


def test_processing_integrity_check_non_compliant_broken_chain(manager, monkeypatch, tmp_path):
    """SC-3 fails when the audit hash chain is broken."""
    _mock_alembic_at_head(monkeypatch, tmp_path)

    mock_latest = MagicMock()
    mock_latest.session_id = "sess-abc"

    mock_recorder = MagicMock()
    mock_recorder.verify_chain.return_value = {
        "valid": False,
        "broken_at": 3,
        "events_checked": 5,
    }

    mock_db = _mock_db_ok()
    mock_db.session = MagicMock()
    mock_db.session.query.return_value.order_by.return_value.first.return_value = mock_latest

    with (
        patch("backend.security.compliance_manager.db", mock_db, create=True),
        patch("backend.security.compliance_manager.TruthAuditEvent", MagicMock(), create=True),
        patch(
            "backend.security.compliance_manager.TruthAuditRecorder",
            return_value=mock_recorder,
            create=True,
        ),
    ):
        manager._check_processing_integrity_compliance()

    assert manager.compliance_state["processing_integrity"]["status"] == "non_compliant"
    issues = manager.compliance_state["processing_integrity"]["issues"]
    assert any("hash chain broken" in i for i in issues)


# ---------------------------------------------------------------------------
# SC-4 — Confidentiality (real checks)
# ---------------------------------------------------------------------------


def test_confidentiality_check_compliant(manager, monkeypatch):
    """SC-4 passes when the key is strong and the audit log has no PII."""
    monkeypatch.setenv("ENCRYPTION_KEK_SECRET", "a-strong-32-char-production-key!")
    # No events.jsonl in tmp_path → no PII scan needed
    manager._check_confidentiality_compliance()

    assert manager.compliance_state["confidentiality"]["status"] == "compliant"


def test_confidentiality_check_non_compliant_dev_key(manager, monkeypatch):
    """SC-4 fails when ENCRYPTION_KEK_SECRET is a weak value."""
    monkeypatch.setenv("ENCRYPTION_KEK_SECRET", "secret")
    manager._check_confidentiality_compliance()

    assert manager.compliance_state["confidentiality"]["status"] == "non_compliant"
    issues = manager.compliance_state["confidentiality"]["issues"]
    assert any("development default" in i for i in issues)


def test_confidentiality_check_non_compliant_pii_in_log(manager, tmp_path, monkeypatch):
    """SC-4 fails when the audit log contains an email address."""
    monkeypatch.setenv("ENCRYPTION_KEK_SECRET", "a-strong-32-char-production-key!")

    log_dir = tmp_path / "logs" / "compliance"
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "events.jsonl").write_text(
        '{"category": "security", "type": "check", '
        '"details": "user admin@example.com checked in"}\n'
    )

    manager._check_confidentiality_compliance()

    assert manager.compliance_state["confidentiality"]["status"] == "non_compliant"
    issues = manager.compliance_state["confidentiality"]["issues"]
    assert any("PII-like content" in i for i in issues)


# ---------------------------------------------------------------------------
# SC-5 — Privacy (real checks)
# ---------------------------------------------------------------------------


def test_privacy_check_compliant(manager, tmp_path):
    """SC-5 passes when route files exist with the expected endpoints."""
    _make_route_files(tmp_path)
    manager._check_privacy_compliance()

    assert manager.compliance_state["privacy"]["status"] == "compliant"


def test_privacy_check_non_compliant_missing_export_route(manager, tmp_path):
    """SC-5 fails when the user data routes file is absent."""
    # Do NOT create routes/user_data_routes.py
    backend_routes = tmp_path / "backend" / "routes"
    backend_routes.mkdir(parents=True)
    (backend_routes / "settings_routes.py").write_text("ai_processing_enabled = True\n")

    manager._check_privacy_compliance()

    assert manager.compliance_state["privacy"]["status"] == "non_compliant"
    issues = manager.compliance_state["privacy"]["issues"]
    assert any("user data routes file missing" in i.lower() for i in issues)


def test_privacy_check_non_compliant_missing_delete_endpoint(manager, tmp_path):
    """SC-5 fails when the delete endpoint is missing from the route file."""
    routes_dir = tmp_path / "routes"
    routes_dir.mkdir()
    (routes_dir / "user_data_routes.py").write_text("@bp.route('/export')\n")  # no /delete

    backend_routes = tmp_path / "backend" / "routes"
    backend_routes.mkdir(parents=True)
    (backend_routes / "settings_routes.py").write_text("ai_processing_enabled = True\n")

    manager._check_privacy_compliance()

    assert manager.compliance_state["privacy"]["status"] == "non_compliant"
    issues = manager.compliance_state["privacy"]["issues"]
    assert any("/delete" in i for i in issues)


def test_privacy_check_non_compliant_missing_ai_toggle(manager, tmp_path):
    """SC-5 fails when ai_processing_enabled is absent from settings routes."""
    _make_route_files(tmp_path)
    # Overwrite settings file without the toggle
    (tmp_path / "backend" / "routes" / "settings_routes.py").write_text(
        "# settings without the toggle\n"
    )

    manager._check_privacy_compliance()

    assert manager.compliance_state["privacy"]["status"] == "non_compliant"
    issues = manager.compliance_state["privacy"]["issues"]
    assert any("ai_processing_enabled" in i for i in issues)


# ---------------------------------------------------------------------------
# All five checks — combined happy-path run
# ---------------------------------------------------------------------------


def test_check_methods_update_state_and_log(manager, tmp_path, monkeypatch):
    """All five checks report compliant when the environment is properly configured."""
    # SC-1 / SC-4: valid key
    monkeypatch.setenv("ENCRYPTION_KEK_SECRET", "a-strong-32-char-production-key!")

    # SC-1: encryption manager key rotation not needed
    mock_em = MagicMock()
    mock_em.get_key_status.return_value = {"rotation_needed": False, "days_until_rotation": 30}

    # SC-2 / SC-3: live DB
    mock_db = _mock_db_ok()
    mock_db.session = MagicMock()
    mock_db.session.query.return_value.order_by.return_value.first.return_value = None

    # SC-3: migration at head
    mock_script = MagicMock()
    mock_script.get_current_head.return_value = "head_rev"
    mock_ctx = MagicMock()
    mock_ctx.get_current_revision.return_value = "head_rev"
    monkeypatch.setattr(
        "backend.security.compliance_manager.ScriptDirectory",
        MagicMock(from_config=MagicMock(return_value=mock_script)),
    )
    monkeypatch.setattr(
        "backend.security.compliance_manager.MigrationContext",
        MagicMock(configure=MagicMock(return_value=mock_ctx)),
    )
    monkeypatch.setattr(
        "backend.security.compliance_manager.AlembicConfig",
        MagicMock(return_value=MagicMock()),
    )

    # SC-5: route files present
    _make_route_files(tmp_path)

    with (
        patch(
            "backend.security.compliance_manager.get_encryption_manager",
            return_value=mock_em,
        ),
        patch("backend.security.compliance_manager.db", mock_db, create=True),
        patch.object(manager, "log_compliance_event") as log_event,
    ):
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


# ---------------------------------------------------------------------------
# Event logging, state persistence, and report generation
# ---------------------------------------------------------------------------


def test_log_compliance_state_and_status(manager):
    manager._log_compliance_state()
    state_files = list(Path("logs/compliance").glob("state_*.json"))
    assert state_files

    status = manager.get_compliance_status()
    assert status["schema_version"] == "dle.compliance-check-status.v1"
    assert status["report_classification"] == "self_assessment_evidence"
    assert status["framework_map"] == "SOC2"
    assert status["framework_map_is_certification"] is False
    assert status["overall_check_result"] in {
        "checks_passed",
        "checks_failed",
        "not_measured",
    }
    assert "category_checks" in status

    manager.compliance_state["privacy"]["status"] = "non_compliant"
    status = manager.get_compliance_status()
    assert status["overall_check_result"] == "checks_failed"
    assert status["category_checks"]["privacy"]["result"] == "failed"


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

    future_filtered = manager.get_compliance_events(
        start_time=datetime.now() + timedelta(days=1)
    )
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
        report = manager.generate_compliance_report(
            start_date=now - timedelta(days=7), end_date=now
        )

    assert report["schema_version"] == "dle.compliance-event-evidence.v1"
    assert report["report_classification"] == "self_assessment_evidence"
    assert report["framework_map"] == "SOC2"
    assert report["framework_map_is_certification"] is False
    assert report["certification_claim"] is False
    assert report["event_counts"]["security"]["check"] == 1
    assert report["event_counts"]["security"]["violation"] == 1
    assert report["category_results"]["security"] == "failed"
    assert report["category_results"]["availability"] == "passed"
    assert report["overall_check_result"] == "checks_failed"
    assert "overall_compliance_score" not in report

    report_file = Path("logs/compliance") / (
        f"self_assessment_{(now - timedelta(days=7)).strftime('%Y%m%d')}_"
        f"{now.strftime('%Y%m%d')}.json"
    )
    assert report_file.exists()
