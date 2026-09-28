import uuid

from extensions import db
from models import IngestionJob, User
from tests.conftest import create_test_user


def _job(*, user_id: int, status: str, label: str) -> IngestionJob:
    job = IngestionJob(
        id=uuid.uuid4(),
        user_id=user_id,
        status=status,
        source_path=f"C:/corpus/{label}",
        source_label=label,
        source_digest=(label.encode("utf-8").hex() + "0" * 64)[:64],
        recursive=True,
        chunk_size=1200,
        max_file_bytes=1024,
        max_total_bytes=4096,
        max_files=10,
        current_checkpoint=status,
    )
    db.session.add(job)
    db.session.flush()
    return job


def test_ingestion_workspace_lists_and_scans_only_current_principal(
    app,
    authenticated_client,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("DATALOGIC_INGESTION_MANIFEST_DIR", str(tmp_path / "manifests"))
    with app.app_context():
        user = User.query.filter_by(username="testuser").first()
        foreign_user_id = create_test_user(
            username="knowledge-workspace-foreign",
            email="knowledge-workspace-foreign@example.com",
        )
        own_job = _job(user_id=user.id, status="completed", label="owner-source")
        foreign_job = _job(
            user_id=foreign_user_id,
            status="completed",
            label="foreign-source",
        )
        db.session.commit()
        own_id = str(own_job.id)
        foreign_id = str(foreign_job.id)

    history = authenticated_client.get("/api/v1/ingestion/history?limit=20")
    assert history.status_code == 200
    items = history.get_json()["data"]["items"]
    assert [item["ingestion_id"] for item in items] == [own_id]

    consistency = authenticated_client.get("/api/v1/ingestion/corpus/consistency")
    assert consistency.status_code == 200
    report = consistency.get_json()["data"]
    assert report["scanned_jobs"] == 1
    assert report["jobs"][0]["ingestion_id"] == own_id

    own_status = authenticated_client.get(f"/api/v1/ingestion/status/{own_id}")
    assert own_status.status_code == 200
    foreign_status = authenticated_client.get(f"/api/v1/ingestion/status/{foreign_id}")
    assert foreign_status.status_code == 404


def test_ingestion_workspace_denies_foreign_lifecycle_actions(
    app,
    authenticated_client,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("DATALOGIC_INGESTION_MANIFEST_DIR", str(tmp_path / "manifests"))
    with app.app_context():
        foreign_user_id = create_test_user(
            username="knowledge-action-foreign",
            email="knowledge-action-foreign@example.com",
        )
        queued = _job(user_id=foreign_user_id, status="queued", label="queued")
        completed = _job(user_id=foreign_user_id, status="completed", label="completed")
        db.session.commit()
        queued_id = str(queued.id)
        completed_id = str(completed.id)

    for path in (
        f"/api/v1/ingestion/jobs/{queued_id}/cancel",
        f"/api/v1/ingestion/jobs/{queued_id}/pause",
        f"/api/v1/ingestion/jobs/{completed_id}/repair",
        f"/api/v1/ingestion/jobs/{completed_id}/delete",
    ):
        response = authenticated_client.post(path)
        assert response.status_code == 404, path

