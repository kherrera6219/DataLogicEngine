from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import backend.truth_engine.truth_gate.budget as budget_module
import backend.truth_engine.truth_gate.compliance as compliance_module


def test_budget_manager_in_memory_paths():
    manager = budget_module.BudgetManager(default_budget=10.0)

    budget = manager.get_budget("tenant-a")
    assert budget["budget_limit"] == 10.0
    assert budget["budget_remaining"] == 10.0

    estimated = manager.estimate_cost("moderate", token_count=2000)
    assert estimated > 0.01

    charged = manager.charge("tenant-a", amount=9.6, tier="high_stakes", session_id="s-1")
    assert charged["kill_switch_triggered"] is True

    can_proceed = manager.check_can_proceed("tenant-a", tier="extreme", estimated_tokens=1000)
    assert can_proceed["can_proceed"] is False
    assert can_proceed["recommended_tier"] == "trivial"

    reset = manager.reset_budget("tenant-a", new_limit=20.0)
    assert reset["budget_limit"] == 20.0
    assert reset["budget_spent"] == 0.0


def test_budget_manager_fallback_tier_logic():
    manager = budget_module.BudgetManager(default_budget=1.0)
    manager.in_memory_budgets["tenant-b"] = {
        "tenant_id": "tenant-b",
        "budget_limit": 1.0,
        "budget_spent": 0.995,
        "budget_remaining": 0.005,
        "budget_utilization": 0.995,
        "kill_switch_triggered": False,
        "kill_switch_threshold": 0.99,
        "downgrade_tier": "trivial",
        "created_at": datetime.now(UTC).isoformat(),
    }

    decision = manager.check_can_proceed("tenant-b", tier="extreme", estimated_tokens=1000)
    assert decision["requested_tier"] == "extreme"
    assert decision["recommended_tier"] in {"trivial", "moderate", "high_stakes", "extreme"}


def test_budget_manager_db_error_paths():
    failing_session = MagicMock()
    failing_query = failing_session.query.return_value.filter_by.return_value
    failing_query.first.side_effect = RuntimeError("db failure")

    manager = budget_module.BudgetManager(db_session=failing_session, default_budget=5.0)
    budget = manager.get_budget("tenant-db")
    assert budget["tenant_id"] == "tenant-db"
    failing_session.rollback.assert_called()

    # Update path with DB errors should not raise.
    manager.in_memory_budgets["tenant-db"]["budget_remaining"] = 5.0
    manager.charge("tenant-db", amount=1.0)
    manager.reset_budget("tenant-db")


def test_compliance_enforcer_core_paths():
    enforcer = compliance_module.ComplianceEnforcer(retention_years=3)
    request = {
        "query": "contact me at user@example.com and call 555-111-2222",
        "tier": "moderate",
        "rationale": "policy rationale",
        "personas_used": ["analyst"],
        "axis_context": {"axis": 6},
        "confidence": 0.8,
    }

    result = enforcer.enforce(request, session_id="session-1")
    assert result["compliant"] is True
    assert result["article_53"]["logged"] is True
    assert result["article_13"]["explainability_enabled"] is True
    assert result["pii_check"]["pii_found"] is True

    hashed = enforcer._hash_query("hello")
    assert len(hashed) == 16

    report = enforcer.get_compliance_report(tenant_id="tenant-a")
    assert report["tenant_id"] == "tenant-a"
    assert report["summary"]["compliance_rate"] == 1.0

    assert enforcer.get_audit_trail("session-1") == []


def test_compliance_enforcer_db_paths_and_errors():
    db_session = MagicMock()
    previous_event = SimpleNamespace(hash_chain="f" * 64)
    db_session.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = previous_event
    db_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = [
        SimpleNamespace(to_dict=lambda: {"event_id": "1"})
    ]

    with patch("models.TruthAuditEvent", create=True) as truth_event_cls:
        truth_event_cls.id.desc.return_value = "id-desc"
        truth_event_cls.timestamp = datetime.now(UTC)
        enforcer = compliance_module.ComplianceEnforcer(db_session=db_session, retention_years=2)

        result = enforcer.enforce({"query": "safe query", "tier": "trivial"}, session_id="session-db")
        assert result["article_53"]["logged"] is True
        db_session.add.assert_called()
        db_session.commit.assert_called()

        trail = enforcer.get_audit_trail("session-db")
        assert trail == [{"event_id": "1"}]

    failing_session = MagicMock()
    failing_session.query.return_value.filter_by.return_value.order_by.return_value.first.side_effect = RuntimeError(
        "insert fail"
    )
    enforcer = compliance_module.ComplianceEnforcer(db_session=failing_session)
    enforce_result = enforcer.enforce({"query": "safe", "tier": "moderate"}, session_id="bad-session")
    assert enforce_result["article_53"]["logged"] is False

    failing_session.query.return_value.filter_by.return_value.order_by.return_value.all.side_effect = RuntimeError(
        "read fail"
    )
    assert enforcer.get_audit_trail("bad-session") == []
