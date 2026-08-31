import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import SQLAlchemyError

from extensions import db
from models import TraceEvidence, TraceRun, User
from tests.conftest import create_test_user


def _trace_run(
    *,
    user_id: int,
    status: str = "completed",
    provider: str | None = "google",
    mode: str | None = "governed",
    confidence: float | None = None,
    token_cost: int | None = None,
) -> TraceRun:
    run = TraceRun(
        run_id=uuid.uuid4(),
        user_id=user_id,
        status=status,
        created_at=datetime.now(UTC) - timedelta(hours=1),
        completed_at=datetime.now(UTC),
        model_name="gemini-3.7-flash" if provider == "google" else "gpt-5.6-sol",
        truth_engine_mode=mode,
        confidence=confidence,
        token_cost=token_cost,
        data_snapshot={
            "provider_used": provider,
            "refinement_disposition": {
                "status": "not_needed",
                "measurement_status": "measured",
                "reason": "confidence_sufficient",
            },
        },
    )
    db.session.add(run)
    db.session.flush()
    return run


def test_trace_analytics_is_principal_scoped_and_keeps_missing_values_explicit(
    app,
    authenticated_client,
):
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        foreign_user_id = create_test_user(
            username="trace-analytics-foreign",
            email="trace-analytics-foreign@example.com",
        )
        own_run = _trace_run(user_id=user.id)
        _trace_run(
            user_id=foreign_user_id,
            provider="openai",
            mode="standard",
            confidence=0.91,
            token_cost=100,
        )
        db.session.add(
            TraceEvidence(
                run_id=own_run.run_id,
                source_type="document",
                source_id="source-1",
                source_title="Observed evidence",
            )
        )
        db.session.commit()
        own_run_id = str(own_run.run_id)

    response = authenticated_client.get("/api/v1/trace/analytics?days=30")

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["scope"] == "principal"
    assert payload["summary"]["run_count"] == 1
    assert payload["summary"]["confidence"] == {
        "average": None,
        "measured_runs": 0,
        "status": "not_measured",
    }
    assert payload["summary"]["tokens"] == {
        "total": None,
        "measured_runs": 0,
        "status": "not_measured",
    }
    assert payload["summary"]["evidence"] == {
        "total": 1,
        "status": "measured",
    }
    assert payload["runs"][0]["run_id"] == own_run_id
    assert payload["runs"][0]["confidence_status"] == "not_measured"
    assert payload["runs"][0]["token_status"] == "not_measured"
    assert payload["runs"][0]["refinement"]["status"] == "not_needed"
    assert payload["runs"][0]["detail_url"] == f"/runs/view?trace={own_run_id}"


def test_trace_analytics_owner_scope_filters_and_bounds(app, authenticated_client):
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        foreign_user_id = create_test_user(
            username="trace-analytics-owner-visible",
            email="trace-analytics-owner-visible@example.com",
        )
        _trace_run(user_id=user.id, provider="google", mode="governed")
        _trace_run(user_id=foreign_user_id, provider="openai", mode="standard")
        db.session.commit()

    filtered = authenticated_client.get(
        "/api/v1/trace/analytics?scope=all&days=7&status=completed"
        "&provider=openai&mode=standard&limit=25"
    )
    assert filtered.status_code == 200
    payload = filtered.get_json()
    assert payload["scope"] == "owner"
    assert payload["filters"] == {
        "days": 7,
        "limit": 25,
        "mode": "standard",
        "provider": "openai",
        "status": "completed",
    }
    assert payload["summary"]["run_count"] == 1
    assert payload["runs"][0]["provider"] == "openai"

    for query in (
        "days=0",
        "days=91",
        "limit=0",
        "limit=101",
        "status=completed%20or%201%3D1",
        f"provider={'x' * 65}",
    ):
        response = authenticated_client.get(f"/api/v1/trace/analytics?{query}")
        assert response.status_code == 400, query


def test_trace_analytics_reports_authority_unavailable(
    app,
    authenticated_client,
    monkeypatch,
):
    import backend.tracing.api as trace_api

    def unavailable(**_kwargs):
        raise SQLAlchemyError("trace authority unavailable")

    monkeypatch.setattr(trace_api, "_build_trace_analytics", unavailable)
    response = authenticated_client.get("/api/v1/trace/analytics")

    assert response.status_code == 503
    payload = response.get_json()
    assert payload["status"] == "unavailable"
    assert payload["error"]["code"] == "TRACE_ANALYTICS_UNAVAILABLE"
    assert "summary" not in payload

