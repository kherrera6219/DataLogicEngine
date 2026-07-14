"""DPAPI protection for MCP connector environment credentials."""

from __future__ import annotations

from typing import Any, Mapping

from backend.security.dpapi_store import decrypt_data, encrypt_data
from backend.mcp_server.policy import MCPPolicyError


DPAPI_PREFIX = "dpapi:v1:"


def protect_connector_credentials(
    credential_env: Mapping[str, str],
    supplied_credentials: Any,
) -> dict[str, str]:
    """Encrypt exact referenced credentials; reject extras and plaintext fallbacks."""

    required_refs = {str(ref) for ref in credential_env.values()}
    supplied = supplied_credentials or {}
    if not isinstance(supplied, Mapping):
        raise MCPPolicyError("MCP_CREDENTIALS_INVALID", "credentials must be an object")
    supplied_refs = {str(key) for key in supplied}
    if supplied_refs != required_refs:
        raise MCPPolicyError(
            "MCP_CREDENTIAL_SET_MISMATCH",
            "Every credential reference must be supplied exactly once",
        )

    protected: dict[str, str] = {}
    for ref in sorted(required_refs):
        value = supplied.get(ref)
        if not isinstance(value, str) or not value or len(value) > 16_384:
            raise MCPPolicyError("MCP_CREDENTIALS_INVALID", "Credential value is invalid")
        blob = encrypt_data(value)
        if not blob:
            raise MCPPolicyError("MCP_DPAPI_REQUIRED", "DPAPI credential protection is required")
        protected[ref] = f"{DPAPI_PREFIX}{blob}"
    return protected


def resolve_connector_credentials(
    credential_env: Mapping[str, str],
    credential_blobs: Any,
) -> dict[str, str]:
    """Resolve protected references into a process-only environment mapping."""

    blobs = credential_blobs or {}
    if not isinstance(blobs, Mapping):
        raise MCPPolicyError("MCP_CREDENTIAL_STORE_INVALID", "Credential store is invalid")
    resolved: dict[str, str] = {}
    for env_name, ref in credential_env.items():
        protected = blobs.get(ref)
        if not isinstance(protected, str) or not protected.startswith(DPAPI_PREFIX):
            raise MCPPolicyError("MCP_CREDENTIAL_MISSING", "A protected credential is missing")
        value = decrypt_data(protected.removeprefix(DPAPI_PREFIX))
        if not value:
            raise MCPPolicyError("MCP_CREDENTIAL_DECRYPT_FAILED", "A protected credential could not be decrypted")
        resolved[str(env_name)] = value
    return resolved
