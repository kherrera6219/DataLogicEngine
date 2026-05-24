from io import BytesIO

import app as app_module
from backend.routes import multimodal_routes


def test_trusted_host_policy_rejects_unknown_host(app, client):
    previous_hosts = app.config.get("TRUSTED_HOSTS")
    app.config["TRUSTED_HOSTS"] = "trusted.example"
    try:
        with app.test_request_context("http://evil.example/live"):
            response = app_module.validate_trusted_host()
    finally:
        app.config["TRUSTED_HOSTS"] = previous_hosts

    payload, status_code = response
    assert status_code == 400
    assert payload.get_json()["code"] == "UNTRUSTED_HOST"


def test_https_redirect_does_not_trust_forwarded_proto_without_proxy_trust(app, monkeypatch):
    previous_testing = app.config.get("TESTING")
    previous_hosts = app.config.get("TRUSTED_HOSTS")
    app.config["TESTING"] = False
    app.config["TRUSTED_HOSTS"] = "trusted.example"
    monkeypatch.setenv("FLASK_ENV", "production")

    try:
        with app.test_request_context(
            "http://trusted.example/health?x=1",
            headers={"X-Forwarded-Proto": "https", "X-Forwarded-Host": "evil.example"},
        ):
            assert app_module.validate_trusted_host() is None
            response = app_module.force_https()
    finally:
        app.config["TESTING"] = previous_testing
        app.config["TRUSTED_HOSTS"] = previous_hosts

    assert response.status_code == 301
    assert response.headers["Location"] == "https://trusted.example/health?x=1"


def test_document_upload_rejects_spoofed_content(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/multimodal/document/process",
        data={"file": (BytesIO(b"not a real pdf"), "document.pdf")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 415
    assert response.json["error"] == "File content does not match an allowed type"


def test_document_upload_sanitizes_filename_before_processing(authenticated_client, monkeypatch):
    captured = {}

    def fake_process_file(file_bytes, filename, mime_type):
        captured["file_bytes"] = file_bytes
        captured["filename"] = filename
        captured["mime_type"] = mime_type
        return {"text": "ok"}

    monkeypatch.setattr(multimodal_routes.document_processor, "process_file", fake_process_file)

    response = authenticated_client.post(
        "/api/v1/multimodal/document/process",
        data={"file": (BytesIO(b"%PDF-1.4\n"), "../../secret.pdf")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    assert captured == {
        "file_bytes": b"%PDF-1.4\n",
        "filename": "secret.pdf",
        "mime_type": "application/pdf",
    }


def test_document_upload_normalizes_processor_errors(authenticated_client, monkeypatch):
    def fail_process_file(file_bytes, filename, mime_type):
        raise RuntimeError("database password leaked")

    monkeypatch.setattr(multimodal_routes.document_processor, "process_file", fail_process_file)

    response = authenticated_client.post(
        "/api/v1/multimodal/document/process",
        data={"file": (BytesIO(b"%PDF-1.4\n"), "safe.pdf")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 500
    assert "password" not in response.json["error"]
    assert response.json["error"] == "An internal error occurred. Please try again later."


def test_upload_policy_enforces_size_before_processing(app):
    small_policy = multimodal_routes.UploadPolicy(
        max_bytes=4,
        extensions=frozenset({".txt"}),
        signatures=(),
        mime_by_extension={".txt": "text/plain"},
    )
    with app.test_request_context(
        "/api/v1/multimodal/document/process",
        method="POST",
        data={"file": (BytesIO(b"hello"), "note.txt")},
        content_type="multipart/form-data",
    ):
        data, filename, mime_type, error = multimodal_routes._read_validated_upload("file", small_policy)

    assert data is None
    assert filename is None
    assert mime_type is None
    assert error == ({"error": "File too large", "max_size_bytes": 4}, 413)
