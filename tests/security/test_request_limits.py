from io import BytesIO

import pytest
from flask import Flask
from werkzeug.datastructures import FileStorage

from backend.middleware.request_limits import (
    FILE_UPLOAD_LIMITS,
    configure_request_limits,
    validate_file_upload,
)


def create_limited_app(max_size):
    app = Flask(__name__)
    app.config["TESTING"] = True

    configure_request_limits(app, {"MAX_CONTENT_LENGTH": max_size})

    @app.route("/upload", methods=["POST"])
    def upload():
        return "ok"

    return app


def test_request_rejected_when_payload_exceeds_limit():
    app = create_limited_app(max_size=20)
    client = app.test_client()

    response = client.post("/upload", data=b"x" * 32, content_type="application/octet-stream")

    assert response.status_code == 413
    body = response.get_json()
    assert body["error"] == "Request too large"
    assert body["max_size_bytes"] == 20
    assert body["your_size_bytes"] == 32


def test_file_upload_validation_respects_size_limits(monkeypatch):
    # Reduce the image upload limit to keep the fixture light-weight
    monkeypatch.setitem(FILE_UPLOAD_LIMITS, "image", 10)

    too_large = FileStorage(stream=BytesIO(b"0" * 16), filename="photo.png")
    is_valid, error = validate_file_upload(too_large, file_type="image")
    assert is_valid is False
    assert "exceeds maximum allowed size" in error

    within_limit = FileStorage(stream=BytesIO(b"0" * 8), filename="photo.png")
    is_valid, error = validate_file_upload(within_limit, file_type="image")
    assert is_valid is True
    assert error is None


def test_file_upload_validation_rejects_disallowed_extensions():
    document = FileStorage(stream=BytesIO(b"content"), filename="malware.exe")

    is_valid, error = validate_file_upload(document, file_type="document")

    assert is_valid is False
    assert "not allowed" in error


def test_validate_file_upload_handles_missing_file():
    is_valid, error = validate_file_upload(None, file_type="document")

    assert is_valid is False
    assert error == "No file provided"

