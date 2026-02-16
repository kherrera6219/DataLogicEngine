"""
Runtime secret resolution helpers.

Resolution order:
1. `<SECRET_NAME>_FILE` or `<SECRET_NAME>_VAULT_FILE`
2. `DLE_SECRET_STORE_JSON` key lookup
3. `<SECRET_NAME>_DPAPI_B64` / `<SECRET_NAME>_VAULT_DPAPI_B64`
4. OS keyring (`<SECRET_NAME>_KEYRING_KEY`, optional)
5. Plain environment variable (`<SECRET_NAME>`)
6. Default value
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional, Tuple

from backend.security.dpapi_store import decrypt_data, is_available as dpapi_available

logger = logging.getLogger(__name__)

SECURE_SECRET_SOURCES = {"file", "json_store", "dpapi", "keyring"}


def _env_truthy(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _read_secret_file(path: str) -> Optional[str]:
    try:
        content = Path(path).read_text(encoding="utf-8").strip()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Secret file read failed for path=%s", path, exc_info=exc)
        return None
    return content or None


def _resolve_from_json_store(secret_name: str) -> Optional[str]:
    store_path = os.environ.get("DLE_SECRET_STORE_JSON", "").strip()
    if not store_path:
        return None
    try:
        payload = json.loads(Path(store_path).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("JSON secret store load failed: %s", store_path, exc_info=exc)
        return None
    value = payload.get(secret_name)
    if value is None:
        return None
    secret = str(value).strip()
    return secret or None


def _resolve_from_keyring(secret_name: str) -> Optional[str]:
    if not _env_truthy("SECRET_KEYRING_ENABLED", False):
        return None
    key_name = os.environ.get(f"{secret_name}_KEYRING_KEY", secret_name).strip()
    service_name = os.environ.get("SECRET_KEYRING_SERVICE", "DataLogicEngine").strip()
    if not key_name:
        return None

    try:
        import keyring  # type: ignore
    except Exception:
        return None

    try:
        value = keyring.get_password(service_name, key_name)
    except Exception as exc:  # noqa: BLE001
        logger.warning("OS keyring lookup failed for secret=%s", secret_name, exc_info=exc)
        return None
    if value is None:
        return None
    secret = str(value).strip()
    return secret or None


def resolve_secret_with_source(
    secret_name: str,
    *,
    default: Optional[str] = None,
    allow_plaintext_env: bool = True,
) -> Tuple[Optional[str], str]:
    """
    Resolve a secret and return `(value, source)`.
    """
    env_file_path = os.environ.get(f"{secret_name}_FILE") or os.environ.get(f"{secret_name}_VAULT_FILE")
    if env_file_path:
        secret = _read_secret_file(env_file_path.strip())
        if secret:
            return secret, "file"

    json_secret = _resolve_from_json_store(secret_name)
    if json_secret:
        return json_secret, "json_store"

    dpapi_blob = os.environ.get(f"{secret_name}_DPAPI_B64") or os.environ.get(f"{secret_name}_VAULT_DPAPI_B64")
    if dpapi_blob and dpapi_available():
        decrypted = decrypt_data(dpapi_blob.strip())
        if decrypted:
            return decrypted, "dpapi"

    keyring_secret = _resolve_from_keyring(secret_name)
    if keyring_secret:
        return keyring_secret, "keyring"

    if allow_plaintext_env:
        plain = os.environ.get(secret_name)
        if plain is not None and str(plain).strip():
            return str(plain).strip(), "env"

    if default is not None and str(default).strip():
        return str(default).strip(), "default"
    return None, "missing"


def is_secure_secret_source(source: str) -> bool:
    return str(source).strip().lower() in SECURE_SECRET_SOURCES


def enforce_production_secret_source(secret_name: str, source: str) -> None:
    """
    Enforce secure secret sources in production unless explicitly overridden.
    """
    if not _env_truthy("PRODUCTION_VAULT_SECRETS_REQUIRED", True):
        return
    if _env_truthy("ALLOW_PLAINTEXT_PROD_SECRETS", False):
        return
    if is_secure_secret_source(source):
        return
    raise ValueError(
        f"{secret_name} must resolve from a vault-backed source in production "
        f"(source={source}). Configure *_FILE, *_DPAPI_B64, JSON secret store, or OS keyring."
    )


def resolve_runtime_secret(
    secret_name: str,
    *,
    default: Optional[str] = None,
    required: bool = False,
    production_mode: bool = False,
) -> tuple[Optional[str], str]:
    """
    Resolve a runtime secret with optional production enforcement.
    """
    value, source = resolve_secret_with_source(secret_name, default=default, allow_plaintext_env=True)
    if production_mode:
        enforce_production_secret_source(secret_name, source)
    if required and not value:
        raise ValueError(f"Required secret is missing: {secret_name}")
    return value, source
