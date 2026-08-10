from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from backend.services.analytics_service import AnalyticsService
from extensions import db
from models import UkgSession


def test_analytics_uses_started_at_model_contract(app):
    session_id = f"analytics-{uuid4()}"
    started_at = datetime.now(UTC)

    with app.app_context():
        record = UkgSession(
            session_id=session_id,
            user_query="Installed analytics contract",
            started_at=started_at,
        )
        db.session.add(record)
        db.session.commit()

        try:
            overview = AnalyticsService.get_dashboard_overview()
            activity = AnalyticsService.get_recent_activity(limit=100)
            session_trends = AnalyticsService.get_trends(metric="sessions", days=1)
            execution_trends = AnalyticsService.get_trends(metric="executions", days=1)

            assert overview is not None
            assert activity is not None
            assert any(item["id"] == session_id for item in activity)
            assert session_trends["data_points"][0]["value"] >= 1
            assert execution_trends["metric"] == "executions"
        finally:
            db.session.delete(record)
            db.session.commit()
