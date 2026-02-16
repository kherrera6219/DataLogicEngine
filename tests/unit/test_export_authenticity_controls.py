import pytest

from backend.security.export_integrity import build_trace_export_document


def _sample_bundle():
    return {
        "run": {"run_id": "run-123", "status": "pass"},
        "stages": [{"id": "stage-1", "name": "layer1"}],
        "evidence": [{"id": "ev-1", "hash": "abc"}],
    }


def test_build_trace_export_document_signs_bundle_when_secret_present(monkeypatch):
    monkeypatch.setenv("TRACE_EXPORT_HMAC_SECRET", "trace-export-secret")
    document = build_trace_export_document(
        _sample_bundle(),
        exported_by="42",
        sign_bundle=True,
        encrypt_bundle=False,
    )

    manifest = document["manifest"]
    assert manifest["signature_algorithm"] == "hmac-sha256"
    assert manifest.get("bundle_signature")
    assert manifest["bundle_hash"]
    assert manifest["section_hashes"]["run"]
    assert manifest["encrypted"] is False
    assert "bundle" in document


def test_build_trace_export_document_encrypts_payload(monkeypatch):
    cryptography = pytest.importorskip("cryptography.fernet")
    key = cryptography.Fernet.generate_key().decode("utf-8")
    monkeypatch.setenv("TRACE_EXPORT_FERNET_KEY", key)
    monkeypatch.setenv("TRACE_EXPORT_HMAC_SECRET", "trace-export-secret")

    document = build_trace_export_document(
        _sample_bundle(),
        exported_by="7",
        sign_bundle=True,
        encrypt_bundle=True,
    )

    assert document["manifest"]["encrypted"] is True
    assert document["manifest"]["encryption_algorithm"] == "fernet"
    assert document["manifest"]["signature_algorithm"] == "hmac-sha256"
    assert document["manifest"].get("envelope_signature")
    assert document.get("payload_encrypted")
    assert "bundle" not in document


def test_build_trace_export_document_encryption_requires_key(monkeypatch):
    monkeypatch.delenv("TRACE_EXPORT_FERNET_KEY", raising=False)
    monkeypatch.delenv("TRACE_EXPORT_ENCRYPTION_KEY", raising=False)

    with pytest.raises(ValueError):
        build_trace_export_document(
            _sample_bundle(),
            exported_by="9",
            sign_bundle=True,
            encrypt_bundle=True,
        )
