"""
MCP connector scope enforcement helpers.

This module centralizes scope parsing and authorization checks for tool calls.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

logger = logging.getLogger(__name__)

STRICT_ENFORCEMENT_ENV = "MCP_SCOPE_ENFORCEMENT_STRICT"


class ScopeEnforcementError(PermissionError):
    """Raised when an MCP tool invocation lacks required scopes."""


@dataclass(frozen=True)
class ExecutionContext:
    """Normalized execution context carried through MCP tool calls."""

    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    scopes: frozenset[str] = frozenset()
    roles: frozenset[str] = frozenset()
    is_admin: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "scopes": sorted(self.scopes),
            "roles": sorted(self.roles),
            "is_admin": self.is_admin,
        }


def _normalize_token(value: Any) -> str:
    return str(value or "").strip().lower()


def normalize_scopes(values: Any) -> set[str]:
    """Normalize scope payloads from list/set/comma-separated string/dict keys."""
    if values is None:
        return set()
    if isinstance(values, str):
        return {_normalize_token(item) for item in values.split(",") if _normalize_token(item)}
    if isinstance(values, dict):
        normalized: set[str] = set()
        for key, enabled in values.items():
            if enabled:
                token = _normalize_token(key)
                if token:
                    normalized.add(token)
        return normalized
    if isinstance(values, Iterable):
        normalized = set()
        for item in values:
            token = _normalize_token(item)
            if token:
                normalized.add(token)
        return normalized
    token = _normalize_token(values)
    return {token} if token else set()


def parse_execution_context(raw_context: Optional[Dict[str, Any]]) -> ExecutionContext:
    """Convert untrusted/raw context payload into a normalized ExecutionContext."""
    raw_context = raw_context or {}
    scopes = normalize_scopes(raw_context.get("scopes"))
    roles = normalize_scopes(raw_context.get("roles"))
    is_admin = bool(raw_context.get("is_admin") or ("admin" in roles) or ("*" in scopes))
    user_id = raw_context.get("user_id")
    tenant_id = raw_context.get("tenant_id")
    return ExecutionContext(
        user_id=str(user_id) if user_id is not None else None,
        tenant_id=str(tenant_id) if tenant_id is not None else None,
        scopes=frozenset(scopes),
        roles=frozenset(roles),
        is_admin=is_admin,
    )


def _scope_matches(granted_scope: str, required_scope: str) -> bool:
    if granted_scope in {"*", "all"}:
        return True
    if granted_scope == required_scope:
        return True
    if granted_scope.endswith("*"):
        return required_scope.startswith(granted_scope[:-1])
    return False


def has_required_scope(granted_scopes: Iterable[str], required_scope: str) -> bool:
    required_scope = _normalize_token(required_scope)
    if not required_scope:
        return True
    return any(_scope_matches(_normalize_token(scope), required_scope) for scope in granted_scopes)


def _strict_enforcement_enabled() -> bool:
    return os.getenv(STRICT_ENFORCEMENT_ENV, "false").strip().lower() in {"1", "true", "yes", "on"}


def enforce_scopes(
    tool_name: str,
    required_scopes: Iterable[str],
    context: ExecutionContext,
    permissive_on_missing_context: bool = True,
) -> None:
    """Enforce required scopes for an MCP tool call."""
    required = [scope for scope in normalize_scopes(required_scopes) if scope]
    if not required:
        return

    if context.is_admin:
        return

    if not context.scopes:
        if permissive_on_missing_context and not _strict_enforcement_enabled():
            logger.warning(
                "MCP scope check bypassed for %s due to missing execution context (strict mode disabled)",
                tool_name,
            )
            return
        raise ScopeEnforcementError(
            f"Missing execution scope context for tool '{tool_name}'. Required scopes: {', '.join(sorted(required))}."
        )

    missing = [scope for scope in required if not has_required_scope(context.scopes, scope)]
    if missing:
        raise ScopeEnforcementError(
            f"Tool '{tool_name}' requires scopes: {', '.join(sorted(missing))}."
        )
