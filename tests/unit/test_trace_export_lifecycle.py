import json
import uuid

from extensions import db
from models import TraceExport, TraceRun, TraceStage, User


def test_trace_export_persists_history_and_download(app, authenticated_client):
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        user_id = user.id
        run_id = uuid.uuid4()
        db.session.add(
            TraceRun(
                run_id=run_id,
                user_id=user_id,
                status="pass",
                input_message="Trace export lifecycle test",
                final_answer="Lifecycle answer",
                confidence=0.88,
            )
        )
        db.session.flush()
        db.session.add(
            TraceStage(
                run_id=run_id,
                name="L1 Context",
                stage_type="layer",
                layer_index=1,
                status="completed",
                outputs={"summary": "context parsed"},
            )
        )
        db.session.commit()

    response = authenticated_client.post(
        f"/api/v1/trace/runs/{run_id}/export",
        json={"sign_bundle": False},
    )

    assert response.status_code == 200
    export_payload = json.loads(response.data)
    assert export_payload["manifest"]["bundle_hash"]
    assert export_payload["bundle"]["run"]["run_id"] == str(run_id)

    with app.app_context():
        export_record = TraceExport.query.filter_by(run_id=run_id).one()
        assert export_record.status == "ready"
        assert export_record.user_id == user_id
        assert export_record.manifest_hash == export_payload["manifest"]["bundle_hash"]
        assert export_record.file_size_bytes == len(response.data)
        assert export_record.bundle_ref == f"/api/v1/trace/exports/{export_record.export_id}/download"
        download_url = export_record.bundle_ref

    history = authenticated_client.get("/api/v1/trace/exports")
    assert history.status_code == 200
    history_payload = history.get_json()
    assert history_payload["exports"][0]["run_id"] == str(run_id)
    assert history_payload["exports"][0]["download_url"] == download_url

    download = authenticated_client.get(download_url)
    assert download.status_code == 200
    downloaded_payload = json.loads(download.data)
    assert downloaded_payload["manifest"]["bundle_hash"] == export_payload["manifest"]["bundle_hash"]


def test_trace_export_ignores_non_object_options(app, authenticated_client):
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        user_id = user.id
        run_id = uuid.uuid4()
        db.session.add(
            TraceRun(
                run_id=run_id,
                user_id=user_id,
                status="pass",
                input_message="Trace export option shape test",
            )
        )
        db.session.commit()

    response = authenticated_client.post(
        f"/api/v1/trace/runs/{run_id}/export",
        json=["not", "an", "object"],
    )

    assert response.status_code == 200
    payload = json.loads(response.data)
    assert payload["manifest"]["signature_algorithm"] in {"none", "hmac-sha256"}


def test_trace_export_hides_integrity_configuration_errors(
    app,
    authenticated_client,
    monkeypatch,
):
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        run_id = uuid.uuid4()
        db.session.add(
            TraceRun(
                run_id=run_id,
                user_id=user.id,
                status="pass",
                input_message="Trace export integrity error test",
            )
        )
        db.session.commit()

    def fail_export_document(*_args, **_kwargs):
        raise ValueError("<script>secret-export-key-path</script>")

    monkeypatch.setattr(
        "backend.tracing.api.build_trace_export_document",
        fail_export_document,
    )

    response = authenticated_client.post(
        f"/api/v1/trace/runs/{run_id}/export",
        json={"encrypt_bundle": True},
    )

    assert response.status_code == 400
    body = response.get_json()
    assert body["error"] == "Trace export could not be prepared"
    assert "secret-export-key-path" not in response.get_data(as_text=True)
