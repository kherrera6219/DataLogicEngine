from sqlalchemy import Column, Integer, MetaData, String, Table

from backend.security.tenant_rls import (
    GLOBAL_TENANT_SENTINEL,
    bootstrap_postgres_tenant_rls,
    build_tenant_policy_expression,
    discover_tenant_tables,
    resolve_request_tenant_id,
    set_postgres_tenant_context,
    tenant_rls_prometheus_lines,
)


class _FakeConnection:
    def __init__(self, statements):
        self._statements = statements

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, statement, params=None):
        self._statements.append((str(statement), params))


class _FakeEngine:
    class Dialect:
        def __init__(self, name):
            self.name = name

    def __init__(self, dialect_name: str):
        self.dialect = self.Dialect(dialect_name)
        self.statements = []

    def begin(self):
        return _FakeConnection(self.statements)


class _FakeSession:
    def __init__(self):
        self.statement = None
        self.params = None

    def execute(self, statement, params=None):
        self.statement = str(statement)
        self.params = params or {}


def test_build_tenant_policy_expression_covers_global_and_scoped_tenants():
    expression = build_tenant_policy_expression()
    assert "tenant_id IS NULL" in expression
    assert "tenant_id = current_setting" in expression
    assert "__global__" in expression


def test_discover_tenant_tables_detects_tenant_id_columns():
    metadata = MetaData()
    Table("trace_runs", metadata, Column("id", Integer), Column("tenant_id", String(64)))
    Table("trace_artifacts", metadata, Column("id", Integer), Column("tenant_id", String(64)))
    Table("system_events", metadata, Column("id", Integer), Column("event_type", String(64)))

    assert discover_tenant_tables(metadata) == ["trace_artifacts", "trace_runs"]


def test_bootstrap_postgres_tenant_rls_applies_policy_statements():
    engine = _FakeEngine("postgresql")

    result = bootstrap_postgres_tenant_rls(engine, tenant_tables=["trace_runs"])

    assert result["status"] == "ok"
    assert result["tables_applied"] == ["trace_runs"]
    statements = [sql for sql, _ in engine.statements]
    assert any('ALTER TABLE "trace_runs" ENABLE ROW LEVEL SECURITY' in sql for sql in statements)
    assert any('ALTER TABLE "trace_runs" FORCE ROW LEVEL SECURITY' in sql for sql in statements)
    assert any('DROP POLICY IF EXISTS "dle_tenant_isolation" ON "trace_runs"' in sql for sql in statements)
    assert any('CREATE POLICY "dle_tenant_isolation" ON "trace_runs"' in sql for sql in statements)


def test_bootstrap_postgres_tenant_rls_skips_non_postgres():
    engine = _FakeEngine("sqlite")
    result = bootstrap_postgres_tenant_rls(engine, tenant_tables=["trace_runs"])

    assert result["status"] == "skipped"
    assert result["reason"] == "non_postgres"
    assert engine.statements == []


def test_resolve_request_tenant_id_priority_order():
    headers = {"X-Tenant-ID": " header-tenant "}
    resolved = resolve_request_tenant_id(headers, user_tenant="user-tenant", session_tenant="session-tenant")
    assert resolved == "header-tenant"

    resolved_user = resolve_request_tenant_id({}, user_tenant="user-tenant", session_tenant="session-tenant")
    assert resolved_user == "user-tenant"

    resolved_session = resolve_request_tenant_id({}, user_tenant=None, session_tenant="session-tenant")
    assert resolved_session == "session-tenant"


def test_set_postgres_tenant_context_sets_global_sentinel_when_missing():
    fake_session = _FakeSession()
    effective_tenant = set_postgres_tenant_context(fake_session, None)

    assert effective_tenant == GLOBAL_TENANT_SENTINEL
    assert "set_config" in fake_session.statement
    assert fake_session.params["tenant_id"] == GLOBAL_TENANT_SENTINEL


def test_tenant_rls_prometheus_lines_emit_expected_gauges():
    lines = tenant_rls_prometheus_lines(
        {"enabled": True, "bootstrap": {"status": "ok"}},
        prefix="datalogicengine",
    )
    payload = "\n".join(lines)
    assert "datalogicengine_tenant_rls_enabled 1" in payload
    assert "datalogicengine_tenant_rls_bootstrap_ok 1" in payload
