"""Resolve the experimental model-egress audit from the current app context."""

from __future__ import annotations

import os
from collections.abc import Callable

from flask import current_app, has_app_context

from backend.observability.context import current_correlation_id
from core.security.egress_guard import EgressDenied


class EgressAuditConfigurationError(EgressDenied):
    """Experimental egress auditing cannot safely identify its owner or request."""


def experimental_egress_audit_enabled() -> bool:
    setting = os.environ.get("DLE_EXPERIMENTAL_EGRESS_AUDIT", "false").strip().lower()
    if setting in {"0", "false", "no", "off"}:
        return False
    if setting in {"1", "true", "yes", "on"}:
        return True
    raise EgressAuditConfigurationError("Invalid DLE_EXPERIMENTAL_EGRESS_AUDIT setting")


def resolve_model_egress_audit() -> tuple[Callable[..., object], str] | None:
    """Return the app-owned writer and request correlation ID when enabled."""
    if not has_app_context():
        if experimental_egress_audit_enabled():
            raise EgressAuditConfigurationError(
                "Egress auditing requires an application context"
            )
        return None
    configured = current_app.config.get("DLE_EXPERIMENTAL_EGRESS_AUDIT", False)
    if not isinstance(configured, bool):
        raise EgressAuditConfigurationError("Invalid app egress audit configuration")
    if not configured:
        if experimental_egress_audit_enabled():
            raise EgressAuditConfigurationError(
                "Egress audit is not configured on this application"
            )
        return None
    audit = current_app.extensions.get("dle_audit_logger")
    if audit is None or not callable(getattr(audit, "log_egress_event", None)):
        raise EgressAuditConfigurationError("Egress audit writer is unavailable")
    if not getattr(audit, "immutable_replica_enabled", False):
        raise EgressAuditConfigurationError("Egress audit replica is disabled")
    correlation_id = current_correlation_id()
    if correlation_id in {"", "startup", "unknown"}:
        raise EgressAuditConfigurationError(
            "Egress audit requires a request correlation ID"
        )
    return audit.log_egress_event, correlation_id
