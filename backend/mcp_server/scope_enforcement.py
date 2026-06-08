"""Compatibility exports for provider-neutral MCP scope enforcement."""

from core.mcp.scope_enforcement import (
    ExecutionContext,
    ScopeEnforcementError,
    enforce_scopes,
    has_required_scope,
    normalize_scopes,
    parse_execution_context,
)

__all__ = [
    "ExecutionContext",
    "ScopeEnforcementError",
    "enforce_scopes",
    "has_required_scope",
    "normalize_scopes",
    "parse_execution_context",
]
