"""Small additive schema upgrades for the app-owned desktop SQLite database."""

from __future__ import annotations

from sqlalchemy import inspect, text


TRACE_RUN_ADDITIVE_COLUMNS = {
    "tier": "VARCHAR(10)",
    "coordinate17_id": "VARCHAR(36)",
    "evidence_pack_hash": "VARCHAR(64)",
    "layers_executed": "JSON",
    "refinement_cycles": "INTEGER",
    "regulatory_pass": "BOOLEAN",
    "security_pass": "BOOLEAN",
    "truthgate_decision": "VARCHAR(16)",
    "token_cost": "INTEGER",
    "latency_ms": "INTEGER",
    "frost_depth": "INTEGER",
    "truth_engine_mode": "VARCHAR(50)",
}


def apply_desktop_sqlite_upgrades(engine) -> list[str]:
    """Add columns introduced after a desktop database was first created."""
    if engine.dialect.name != "sqlite":
        return []

    inspector = inspect(engine)
    if "trace_runs" not in inspector.get_table_names():
        return []

    existing = {column["name"] for column in inspector.get_columns("trace_runs")}
    missing = [name for name in TRACE_RUN_ADDITIVE_COLUMNS if name not in existing]
    if not missing:
        return []

    with engine.begin() as connection:
        for name in missing:
            ddl_type = TRACE_RUN_ADDITIVE_COLUMNS[name]
            connection.execute(text(f'ALTER TABLE trace_runs ADD COLUMN "{name}" {ddl_type}'))
    return missing
