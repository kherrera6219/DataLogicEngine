from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from backend.services.analytics_service import AnalyticsService
from extensions import db
from models import ChatSession, TraceRun, UkgSession
from tests.conftest import create_test_user


def test_analytics_uses_current_chat_and_trace_records_while_trends_keep_legacy_contract(app):
    session_id = f"analytics-{uuid4()}"
    started_at = datetime.now(UTC)

    with app.app_context():
        user_id = create_test_user(
            username="analytics-current-owner",
            email="analytics-current-owner@example.com",
            password="SecureTest789$#@",
        )
        record = UkgSession(
            session_id=session_id,
            user_query="Installed analytics contract",
            started_at=started_at,
        )
        db.session.add(record)
        chat = ChatSession(
            id=uuid4(), user_id=user_id, title="Current governed chat", updated_at=started_at
        )
        run = TraceRun(run_id=uuid4(), user_id=user_id, status="completed", created_at=started_at)
        db.session.add_all([chat, run])
        db.session.commit()

        try:
            overview = AnalyticsService.get_dashboard_overview(user_id=user_id)
            activity = AnalyticsService.get_recent_activity(limit=100, user_id=user_id)
            session_trends = AnalyticsService.get_trends(metric="sessions", days=1)
            execution_trends = AnalyticsService.get_trends(metric="executions", days=1)

            assert overview is not None
            assert activity is not None
            assert overview["api_requests_24h"] >= 1
            assert any(item["id"] == str(chat.id) for item in activity)
            assert not any(item["id"] == session_id for item in activity)
            assert session_trends["data_points"][0]["value"] >= 1
            assert execution_trends["metric"] == "executions"
        finally:
            db.session.delete(record)
            db.session.delete(chat)
            db.session.delete(run)
            db.session.commit()
