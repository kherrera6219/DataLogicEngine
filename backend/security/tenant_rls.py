"""
PostgreSQL tenant row-level security (RLS) helpers.

This module provides:
- Bootstrap of per-table tenant RLS policies for Postgres databases.
- Per-request binding of tenant context into the SQL session.
- Lightweight status export for observability.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Mapping, Optional, Sequence

from flask import g, jsonify, request, session
from flask_login import current_user
from sqlalchemy import text

logger = logging.getLogger(__name__)

TENANT_SETTING_KEY = "app.current_tenant_id"
GLOBAL_TENANT_SENTINEL = "__global__"
DEFAULT_POLICY_NAME = "dle_tenant_isolation"


def _env_truthy(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _normalize_tenant_id(raw: Any) -> Optional[str]:
    if raw is None:
        return None
    value = str(raw).strip()
    if not value:
        return None
    return value


def _quote_ident(identifier: str) -> str:
    """
    Quote SQL identifiers defensively (including optional schema-qualified names).
    """
    parts = [part for part in str(identifier).split(".") if part]
    return ".".join(f"\"{part.replace('\"', '\"\"')}\"" for part in parts)


def discover_tenant_tables(metadata) -> list[str]:
    """
    Return all table names that expose a `tenant_id` column.
    """
    tables: list[str] = []
    for table in getattr(metadata, "sorted_tables", []):
        try:
            has_tenant_id = any(column.name == "tenant_id" for column in table.columns)
        except Exception:
            has_tenant_id = False
        if has_tenant_id:
            tables.append(str(table.name))
    return sorted(set(tables))


def build_tenant_policy_expression(
    *,
    setting_key: str = TENANT_SETTING_KEY,
    global_sentinel: str = GLOBAL_TENANT_SENTINEL,
) -> str:
    """
    Build SQL expression for tenant visibility policy.

    Behavior:
    - If request tenant is `__global__`, only rows with NULL tenant are visible.
    - Otherwise only exact tenant matches are visible.
    """
    escaped_setting = setting_key.replace("'", "''")
    escaped_global = global_sentinel.replace("'", "''")
    return (
        "("
        f"(current_setting('{escaped_setting}', true) = '{escaped_global}' AND tenant_id IS NULL)"
        " OR "
        f"(tenant_id = current_setting('{escaped_setting}', true))"
        ")"
    )


def bootstrap_postgres_tenant_rls(
    engine,
    *,
    tenant_tables: Sequence[str],
    policy_name: str = DEFAULT_POLICY_NAME,
    setting_key: str = TENANT_SETTING_KEY,
    force: bool = True,
) -> dict[str, Any]:
    """
    Apply/refresh tenant RLS policy on every configured tenant table.
    """
    dialect_name = str(getattr(getattr(engine, "dialect", None), "name", "")).lower()
    result: dict[str, Any] = {
        "status": "skipped",
        "dialect": dialect_name or "unknown",
        "tables_discovered": sorted({str(table) for table in tenant_tables if str(table).strip()}),
        "tables_applied": [],
        "policy_name": policy_name,
    }

    if dialect_name not in {"postgresql", "postgres"}:
        result["reason"] = "non_postgres"
        return result

    if not result["tables_discovered"]:
        result["reason"] = "no_tenant_tables"
        return result

    policy_expression = build_tenant_policy_expression(setting_key=setting_key)
    quoted_policy = _quote_ident(policy_name)

    try:
        with engine.begin() as connection:
            for table_name in result["tables_discovered"]:
                quoted_table = _quote_ident(table_name)
                connection.execute(text(f"ALTER TABLE {quoted_table} ENABLE ROW LEVEL SECURITY"))
                if force:
                    connection.execute(text(f"ALTER TABLE {quoted_table} FORCE ROW LEVEL SECURITY"))
                connection.execute(text(f"DROP POLICY IF EXISTS {quoted_policy} ON {quoted_table}"))
                connection.execute(
                    text(
                        f"CREATE POLICY {quoted_policy} ON {quoted_table} "
                        f"USING ({policy_expression}) "
                        f"WITH CHECK ({policy_expression})"
                    )
                )
                result["tables_applied"].append(table_name)
        result["status"] = "ok"
    except Exception as exc:  # noqa: BLE001
        result["status"] = "error"
        result["error"] = str(exc)
        logger.error("Postgres tenant RLS bootstrap failed", exc_info=exc)

    return result


def resolve_request_tenant_id(
    headers: Mapping[str, Any],
    *,
    user_tenant: Optional[str] = None,
    session_tenant: Optional[str] = None,
) -> Optional[str]:
    """
    Resolve effective tenant for the current request.
    """
    for candidate in (
        headers.get("X-Tenant-ID"),
        headers.get("X-Tenant-Id"),
        headers.get("x-tenant-id"),
        user_tenant,
        session_tenant,
    ):
        normalized = _normalize_tenant_id(candidate)
        if normalized:
            return normalized
    return None


def set_postgres_tenant_context(
    db_session,
    tenant_id: Optional[str],
    *,
    setting_key: str = TENANT_SETTING_KEY,
) -> str:
    """
    Bind request tenant context into the active SQL transaction/session.
    """
    effective_tenant = _normalize_tenant_id(tenant_id) or GLOBAL_TENANT_SENTINEL
    escaped_setting = setting_key.replace("'", "''")
    db_session.execute(
        text(f"SELECT set_config('{escaped_setting}', :tenant_id, true)"),
        {"tenant_id": effective_tenant},
    )
    return effective_tenant


def configure_tenant_rls(app, db) -> dict[str, Any]:
    """
    Configure Postgres tenant RLS bootstrap + per-request context binding.
    """
    env_name = str(os.environ.get("FLASK_ENV", "development")).lower()
    enabled = _env_truthy("POSTGRES_TENANT_RLS_ENABLED", env_name == "production")
    enforce = _env_truthy("POSTGRES_TENANT_RLS_ENFORCE", env_name == "production")
    bootstrap_on_startup = _env_truthy("POSTGRES_TENANT_RLS_BOOTSTRAP_ON_STARTUP", enabled)
    force_rls = _env_truthy("POSTGRES_TENANT_RLS_FORCE", True)
    policy_name = os.environ.get("POSTGRES_TENANT_RLS_POLICY_NAME", DEFAULT_POLICY_NAME).strip() or DEFAULT_POLICY_NAME

    with app.app_context():
        dialect_name = str(getattr(getattr(db.engine, "dialect", None), "name", "")).lower()
        is_postgres = dialect_name in {"postgresql", "postgres"}

        status: dict[str, Any] = {
            "enabled": bool(enabled and is_postgres and not app.config.get("TESTING")),
            "enforce": bool(enforce and not app.config.get("TESTING")),
            "dialect": dialect_name or "unknown",
            "policy_name": policy_name,
            "bootstrap": {"status": "skipped", "reason": "disabled"},
            "last_request_tenant": None,
            "last_effective_tenant": None,
        }

        if status["enabled"] and bootstrap_on_startup:
            tenant_tables = discover_tenant_tables(db.Model.metadata)
            status["bootstrap"] = bootstrap_postgres_tenant_rls(
                db.engine,
                tenant_tables=tenant_tables,
                policy_name=policy_name,
                force=force_rls,
            )
            if status["enforce"] and status["bootstrap"].get("status") == "error":
                raise RuntimeError("Postgres tenant RLS bootstrap failed in enforced mode")
        elif enabled and not is_postgres:
            status["bootstrap"] = {"status": "skipped", "reason": "non_postgres"}

    @app.before_request
    def _bind_tenant_rls_context():
        if not status["enabled"]:
            return None

        user_tenant = None
        if getattr(current_user, "is_authenticated", False):
            user_tenant = getattr(current_user, "tenant_id", None)
        tenant_id = resolve_request_tenant_id(
            request.headers,
            user_tenant=user_tenant,
            session_tenant=session.get("tenant_id"),
        )

        g.tenant_id = tenant_id
        status["last_request_tenant"] = tenant_id

        try:
            effective = set_postgres_tenant_context(db.session, tenant_id)
            status["last_effective_tenant"] = effective
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to bind Postgres tenant context for request", exc_info=exc)
            try:
                db.session.rollback()
            except Exception:
                pass
            if status["enforce"]:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": {
                                "code": "TENANT_CONTEXT_UNAVAILABLE",
                                "message": "Tenant isolation context could not be applied.",
                            },
                        }
                    ),
                    503,
                )
        return None

    return status


def tenant_rls_prometheus_lines(status: Mapping[str, Any], prefix: str = "datalogicengine") -> list[str]:
    """
    Render tenant RLS controller status into Prometheus text lines.
    """
    enabled = 1 if status.get("enabled") else 0
    bootstrap_ok = 1 if status.get("bootstrap", {}).get("status") == "ok" else 0
    return [
        f"# HELP {prefix}_tenant_rls_enabled Tenant RLS controller enabled flag (1=true, 0=false).",
        f"# TYPE {prefix}_tenant_rls_enabled gauge",
        f"{prefix}_tenant_rls_enabled {enabled}",
        f"# HELP {prefix}_tenant_rls_bootstrap_ok Tenant RLS bootstrap health flag (1=ok, 0=non-ok).",
        f"# TYPE {prefix}_tenant_rls_bootstrap_ok gauge",
        f"{prefix}_tenant_rls_bootstrap_ok {bootstrap_ok}",
    ]
