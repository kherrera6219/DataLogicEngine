import json

import pytest

from backend.security.secret_resolver import (
    resolve_runtime_secret,
    resolve_secret_with_source,
)


def test_resolve_secret_with_source_reads_secret_file(tmp_path, monkeypatch):
    secret_path = tmp_path / "session_secret.txt"
    secret_path.write_text("vault-file-secret\n", encoding="utf-8")
    monkeypatch.setenv("SESSION_SECRET_FILE", str(secret_path))
    monkeypatch.delenv("SESSION_SECRET", raising=False)

    secret, source = resolve_secret_with_source("SESSION_SECRET")
    assert secret == "vault-file-secret"
    assert source == "file"


def test_resolve_secret_with_source_reads_json_store(tmp_path, monkeypatch):
    store_path = tmp_path / "secrets.json"
    store_path.write_text(json.dumps({"JWT_SECRET_KEY": "json-vault-secret"}), encoding="utf-8")
    monkeypatch.setenv("DLE_SECRET_STORE_JSON", str(store_path))
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)

    secret, source = resolve_secret_with_source("JWT_SECRET_KEY")
    assert secret == "json-vault-secret"
    assert source == "json_store"


def test_resolve_runtime_secret_rejects_plaintext_env_in_production(monkeypatch):
    monkeypatch.setenv("PRODUCTION_VAULT_SECRETS_REQUIRED", "true")
    monkeypatch.delenv("ALLOW_PLAINTEXT_PROD_SECRETS", raising=False)
    monkeypatch.setenv("SESSION_SECRET", "plain-env-secret")
    monkeypatch.delenv("SESSION_SECRET_FILE", raising=False)

    with pytest.raises(ValueError):
        resolve_runtime_secret("SESSION_SECRET", production_mode=True)


def test_resolve_runtime_secret_allows_override_for_plaintext_env(monkeypatch):
    monkeypatch.setenv("PRODUCTION_VAULT_SECRETS_REQUIRED", "true")
    monkeypatch.setenv("ALLOW_PLAINTEXT_PROD_SECRETS", "true")
    monkeypatch.setenv("SESSION_SECRET", "plain-env-secret")

    secret, source = resolve_runtime_secret("SESSION_SECRET", production_mode=True)
    assert secret == "plain-env-secret"
    assert source == "env"


def test_resolve_runtime_secret_required_missing_raises(monkeypatch):
    monkeypatch.delenv("MISSING_RUNTIME_SECRET", raising=False)
    monkeypatch.delenv("MISSING_RUNTIME_SECRET_FILE", raising=False)
    with pytest.raises(ValueError):
        resolve_runtime_secret("MISSING_RUNTIME_SECRET", required=True, production_mode=False)
