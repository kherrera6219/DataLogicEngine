import json
import sys
from types import SimpleNamespace

import pytest

from backend.security.secret_resolver import (
    enforce_production_secret_source,
    is_secure_secret_source,
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


def test_resolver_falls_through_invalid_files_and_json_to_defaults(tmp_path, monkeypatch):
    missing = tmp_path / "missing.secret"
    monkeypatch.setenv("FALLBACK_SECRET_FILE", str(missing))
    monkeypatch.setenv("DLE_SECRET_STORE_JSON", str(missing))
    monkeypatch.delenv("FALLBACK_SECRET", raising=False)
    assert resolve_secret_with_source("FALLBACK_SECRET", default=" default-value ") == (
        "default-value",
        "default",
    )
    assert resolve_secret_with_source("FALLBACK_SECRET", default=" ") == (None, "missing")


def test_resolver_supports_dpapi_keyring_and_desktop_handoff(monkeypatch):
    import backend.security.secret_resolver as module

    monkeypatch.setattr(module, "dpapi_available", lambda: True)
    monkeypatch.setattr(module, "decrypt_data", lambda value: f"decrypted-{value}")
    monkeypatch.setenv("DPAPI_SECRET_DPAPI_B64", "blob")
    assert resolve_secret_with_source("DPAPI_SECRET") == ("decrypted-blob", "dpapi")

    monkeypatch.setenv("SECRET_KEYRING_ENABLED", "true")
    monkeypatch.setenv("KEYRING_SECRET_KEYRING_KEY", "owner-key")
    monkeypatch.setenv("SECRET_KEYRING_SERVICE", "DLE Tests")
    monkeypatch.setitem(sys.modules, "keyring", SimpleNamespace(get_password=lambda service, key: f"{service}:{key}"))
    assert resolve_secret_with_source("KEYRING_SECRET") == ("DLE Tests:owner-key", "keyring")

    monkeypatch.setenv("SECRET_KEYRING_ENABLED", "false")
    monkeypatch.setenv("IS_DESKTOP_APP", "true")
    monkeypatch.setenv("DLE_DESKTOP_SECRET_HANDOFF", "yes")
    monkeypatch.setenv("DESKTOP_SECRET", " handoff ")
    assert resolve_secret_with_source("DESKTOP_SECRET") == ("handoff", "desktop_handoff")
    assert resolve_secret_with_source("DESKTOP_SECRET", allow_plaintext_env=False) == (None, "missing")


def test_keyring_failures_and_production_policy_exemptions(monkeypatch):
    import backend.security.secret_resolver as module

    monkeypatch.setenv("SECRET_KEYRING_ENABLED", "true")
    monkeypatch.setenv("EMPTY_SECRET_KEYRING_KEY", " ")
    assert module._resolve_from_keyring("EMPTY_SECRET") is None
    monkeypatch.setenv("BROKEN_SECRET_KEYRING_KEY", "broken")
    monkeypatch.setitem(sys.modules, "keyring", SimpleNamespace(get_password=lambda *_args: (_ for _ in ()).throw(RuntimeError("keyring offline"))))
    assert module._resolve_from_keyring("BROKEN_SECRET") is None

    assert is_secure_secret_source(" FILE ") is True
    assert is_secure_secret_source("env") is False
    monkeypatch.setenv("PRODUCTION_VAULT_SECRETS_REQUIRED", "false")
    enforce_production_secret_source("SECRET", "env")
    monkeypatch.setenv("PRODUCTION_VAULT_SECRETS_REQUIRED", "true")
    monkeypatch.setenv("ALLOW_PLAINTEXT_PROD_SECRETS", "false")
    enforce_production_secret_source("SECRET", "json_store")
