"""Fail-closed policy for local MCP connector definitions and results.

The production connector transport is deliberately narrow: an owner-approved,
absolute executable over stdio with no shell, no package runner, no unqualified
network access, explicit file roots, bounded resources, and an exact consent
fingerprint. Connector output is untrusted evidence, never an instruction.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping


SUPPORTED_MCP_PROTOCOL_VERSION = "2025-11-25"
SUPPORTED_MCP_TRANSPORT = "stdio"

_DENIED_EXECUTABLES = frozenset(
    {
        "bitsadmin.exe",
        "certutil.exe",
        "cmd.exe",
        "cscript.exe",
        "mshta.exe",
        "npm.cmd",
        "npm.exe",
        "npx.cmd",
        "npx.exe",
        "pip.exe",
        "powershell.exe",
        "pwsh.exe",
        "regsvr32.exe",
        "rundll32.exe",
        "uvx.exe",
        "wscript.exe",
    }
)
_SHELL_ARGUMENT_PATTERN = re.compile(r"[\x00\r\n;&|<>]")
_ENV_NAME_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]{0,127}$", re.IGNORECASE)
_SECRET_ENV_PATTERN = re.compile(
    r"(?:API[_-]?KEY|TOKEN|SECRET|PASSWORD|PASSWD|PRIVATE[_-]?KEY|CREDENTIAL)",
    re.IGNORECASE,
)
_SCOPE_PATTERN = re.compile(r"^connector:[a-z0-9][a-z0-9._-]{0,63}:(?:read|write|execute)$")
_INJECTION_PATTERNS = (
    re.compile(r"ignore\s+(?:all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(?:all\s+)?prior\s+(?:instructions|prompts)", re.IGNORECASE),
    re.compile(r"(?:system|developer)\s+(?:message|override|instructions?)", re.IGNORECASE),
    re.compile(r"reveal\s+(?:the\s+)?(?:secret|token|password|credential)", re.IGNORECASE),
    re.compile(r"<\|(?:system|developer|assistant|user)\|>", re.IGNORECASE),
)
_SECRET_VALUE_PATTERNS = (
    re.compile(
        r"(?i)\b([a-z0-9_-]*(?:api[_-]?key|token|secret|password|credential))\s*[:=]\s*([^\s,;]+)"
    ),
    re.compile(r"(?i)\bbearer\s+[a-z0-9._~+/-]+=*"),
)


class MCPPolicyError(ValueError):
    """Stable fail-closed MCP policy rejection."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.public_message = message
        super().__init__(message)


def _string_list(value: Any, *, field: str, max_items: int = 64) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > max_items:
        raise MCPPolicyError(f"MCP_{field.upper()}_INVALID", f"{field} must be a bounded list")
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip() or len(item) > 4096:
            raise MCPPolicyError(f"MCP_{field.upper()}_INVALID", f"{field} contains an invalid value")
        normalized.append(item.strip())
    return normalized


def _resolve_existing_directory(value: Any, *, field: str, code_prefix: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise MCPPolicyError(f"{code_prefix}_REQUIRED", f"{field} is required")
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        raise MCPPolicyError(f"{code_prefix}_ABSOLUTE_REQUIRED", f"{field} must be an absolute path")
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise MCPPolicyError(f"{code_prefix}_NOT_FOUND", f"{field} does not exist") from exc
    if not resolved.is_dir():
        raise MCPPolicyError(f"{code_prefix}_NOT_DIRECTORY", f"{field} must be a directory")
    return resolved


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _validated_limits(raw: Any) -> dict[str, int]:
    values = raw if isinstance(raw, Mapping) else {}
    defaults = {
        "request_timeout_seconds": 30,
        "max_message_bytes": 65_536,
        "max_stderr_bytes": 16_384,
        "max_process_memory_mb": 256,
    }
    ranges = {
        "request_timeout_seconds": (1, 120),
        "max_message_bytes": (1_024, 1_048_576),
        "max_stderr_bytes": (1_024, 262_144),
        "max_process_memory_mb": (64, 2_048),
    }
    normalized: dict[str, int] = {}
    for key, default in defaults.items():
        value = values.get(key, default)
        if isinstance(value, bool):
            raise MCPPolicyError("MCP_LIMIT_INVALID", f"{key} must be an integer")
        try:
            integer = int(value)
        except (TypeError, ValueError) as exc:
            raise MCPPolicyError("MCP_LIMIT_INVALID", f"{key} must be an integer") from exc
        minimum, maximum = ranges[key]
        if integer < minimum or integer > maximum:
            raise MCPPolicyError("MCP_LIMIT_INVALID", f"{key} is outside the supported range")
        normalized[key] = integer
    return normalized


def validate_stdio_definition(name: str, raw_definition: Mapping[str, Any]) -> dict[str, Any]:
    """Validate, normalize, fingerprint, and redact one connector definition."""

    if not isinstance(raw_definition, Mapping):
        raise MCPPolicyError("MCP_DEFINITION_INVALID", "Connector definition must be an object")
    normalized_name = str(name or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", normalized_name):
        raise MCPPolicyError("MCP_NAME_INVALID", "Connector name is invalid")

    transport = str(raw_definition.get("transport") or SUPPORTED_MCP_TRANSPORT).strip().lower()
    if transport != SUPPORTED_MCP_TRANSPORT:
        raise MCPPolicyError("MCP_TRANSPORT_UNSUPPORTED", "Only the stdio transport is supported")
    protocol_version = str(
        raw_definition.get("protocol_version") or SUPPORTED_MCP_PROTOCOL_VERSION
    ).strip()
    if protocol_version != SUPPORTED_MCP_PROTOCOL_VERSION:
        raise MCPPolicyError(
            "MCP_PROTOCOL_UNSUPPORTED",
            f"Protocol version must be {SUPPORTED_MCP_PROTOCOL_VERSION}",
        )

    command_value = raw_definition.get("command")
    if not isinstance(command_value, str) or not command_value.strip():
        raise MCPPolicyError("MCP_EXECUTABLE_REQUIRED", "An executable is required")
    command = Path(command_value).expanduser()
    if not command.is_absolute():
        raise MCPPolicyError("MCP_EXECUTABLE_ABSOLUTE_REQUIRED", "Executable must be an absolute path")
    if command.name.lower() in _DENIED_EXECUTABLES:
        raise MCPPolicyError("MCP_EXECUTABLE_DENIED", "Shells and package runners are not allowed")
    try:
        command = command.resolve(strict=True)
    except OSError as exc:
        raise MCPPolicyError("MCP_EXECUTABLE_NOT_FOUND", "Executable does not exist") from exc
    if not command.is_file():
        raise MCPPolicyError("MCP_EXECUTABLE_NOT_FILE", "Executable must be a file")
    if command.name.lower() in _DENIED_EXECUTABLES:
        raise MCPPolicyError("MCP_EXECUTABLE_DENIED", "Shells and package runners are not allowed")

    args = _string_list(raw_definition.get("args"), field="arguments", max_items=64)
    if any(_SHELL_ARGUMENT_PATTERN.search(argument) for argument in args):
        raise MCPPolicyError("MCP_ARGUMENT_REJECTED", "Arguments contain a prohibited control or shell token")

    cwd = _resolve_existing_directory(raw_definition.get("cwd"), field="cwd", code_prefix="MCP_CWD")
    file_roots_raw = _string_list(raw_definition.get("file_roots"), field="file_roots", max_items=16)
    if not file_roots_raw:
        raise MCPPolicyError("MCP_FILE_ROOT_REQUIRED", "At least one file root is required")
    file_roots = [
        _resolve_existing_directory(value, field="file root", code_prefix="MCP_FILE_ROOT")
        for value in file_roots_raw
    ]
    if not any(_is_relative_to(cwd, root) for root in file_roots):
        raise MCPPolicyError("MCP_CWD_OUTSIDE_FILE_ROOT", "cwd must be inside an approved file root")

    env_raw = raw_definition.get("env") or {}
    if not isinstance(env_raw, Mapping) or len(env_raw) > 64:
        raise MCPPolicyError("MCP_ENV_INVALID", "env must be a bounded object")
    env: dict[str, str] = {}
    for raw_key, raw_value in env_raw.items():
        key = str(raw_key or "").strip()
        if not _ENV_NAME_PATTERN.fullmatch(key):
            raise MCPPolicyError("MCP_ENV_NAME_INVALID", "Environment variable name is invalid")
        if _SECRET_ENV_PATTERN.search(key):
            raise MCPPolicyError(
                "MCP_SECRET_ENV_REQUIRES_CREDENTIAL_REF",
                "Secret environment values require a DPAPI credential reference",
            )
        if not isinstance(raw_value, (str, int, float, bool)):
            raise MCPPolicyError("MCP_ENV_VALUE_INVALID", "Environment variable value is invalid")
        value = str(raw_value)
        if len(value) > 4096 or "\x00" in value or "\r" in value or "\n" in value:
            raise MCPPolicyError("MCP_ENV_VALUE_INVALID", "Environment variable value is invalid")
        env[key] = value

    credential_env_raw = raw_definition.get("credential_env") or {}
    if not isinstance(credential_env_raw, Mapping) or len(credential_env_raw) > 32:
        raise MCPPolicyError("MCP_CREDENTIAL_REFS_INVALID", "credential_env must be a bounded object")
    credential_env: dict[str, str] = {}
    for raw_key, raw_ref in credential_env_raw.items():
        key = str(raw_key or "").strip()
        ref = str(raw_ref or "").strip()
        if not _ENV_NAME_PATTERN.fullmatch(key) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", ref):
            raise MCPPolicyError("MCP_CREDENTIAL_REFS_INVALID", "Credential reference is invalid")
        credential_env[key] = ref

    network_destinations = _string_list(
        raw_definition.get("network_destinations"), field="network_destinations", max_items=32
    )
    if network_destinations:
        raise MCPPolicyError(
            "MCP_NETWORK_CONNECTORS_NOT_QUALIFIED",
            "Network-capable stdio connectors are not qualified for production",
        )

    requested_scopes = sorted(set(_string_list(
        raw_definition.get("requested_scopes"), field="requested_scopes", max_items=32
    )))
    if not requested_scopes:
        raise MCPPolicyError("MCP_SCOPE_REQUIRED", "At least one granular connector scope is required")
    if any(not _SCOPE_PATTERN.fullmatch(scope.lower()) for scope in requested_scopes):
        raise MCPPolicyError("MCP_SCOPE_REJECTED", "Wildcard or malformed connector scope is not allowed")
    connector_scope_prefix = f"connector:{normalized_name.lower()}:"
    if any(not scope.lower().startswith(connector_scope_prefix) for scope in requested_scopes):
        raise MCPPolicyError("MCP_SCOPE_REJECTED", "Scopes must belong to the configured connector")

    definition = {
        "schema_version": "mcp-connector-config.v1",
        "name": normalized_name,
        "transport": transport,
        "protocol_version": protocol_version,
        "command": str(command),
        "args": args,
        "cwd": str(cwd),
        "env": env,
        "credential_env": credential_env,
        "file_roots": [str(root) for root in file_roots],
        "network_destinations": [],
        "requested_scopes": requested_scopes,
        "limits": _validated_limits(raw_definition.get("limits")),
    }
    canonical = json.dumps(definition, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    renderer_view = deepcopy(definition)
    renderer_view.pop("env", None)
    renderer_view.pop("credential_env", None)
    renderer_view["env_keys"] = sorted(env)
    renderer_view["credential_keys"] = sorted(credential_env)
    renderer_view["command_fingerprint"] = fingerprint
    return {
        "definition": definition,
        "fingerprint": fingerprint,
        "renderer_view": renderer_view,
    }


def redact_sensitive_text(text: str) -> str:
    """Redact common secret assignments and bearer tokens from connector text."""
    redacted = text
    for pattern in _SECRET_VALUE_PATTERNS:
        if pattern.groups >= 2:
            redacted = pattern.sub(lambda match: f"{match.group(1)}=[REDACTED]", redacted)
        else:
            redacted = pattern.sub("Bearer [REDACTED]", redacted)
    return redacted


def govern_connector_result(result: Any, *, max_bytes: int = 65_536) -> dict[str, Any]:
    """Return a content-bounded, hashed, untrusted-evidence envelope."""

    if isinstance(result, str):
        text = result
    else:
        try:
            text = json.dumps(result, sort_keys=True, ensure_ascii=False, default=str)
        except (TypeError, ValueError) as exc:
            raise MCPPolicyError("MCP_OUTPUT_INVALID", "Connector output is not serializable") from exc
    payload = text.encode("utf-8")
    if len(payload) > int(max_bytes):
        raise MCPPolicyError("MCP_OUTPUT_LIMIT_EXCEEDED", "Connector output exceeded the configured limit")
    patterns = [pattern.pattern for pattern in _INJECTION_PATTERNS if pattern.search(text)]
    preview = redact_sensitive_text(text[:2_000])
    return {
        "schema_version": "mcp-result.v1",
        "trust": "untrusted_connector_output",
        "requires_governance": True,
        "prompt_injection_risk": bool(patterns),
        "detected_patterns": patterns,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "size_bytes": len(payload),
        "preview": preview,
        "content": text,
    }
