from sqlalchemy import create_engine, inspect, text

from backend.desktop.schema_upgrade import (
    TRACE_RUN_ADDITIVE_COLUMNS,
    apply_desktop_sqlite_upgrades,
)


def test_desktop_sqlite_upgrade_adds_missing_trace_columns(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'desktop.db'}")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE trace_runs (run_id VARCHAR(36) PRIMARY KEY)"))

    added = apply_desktop_sqlite_upgrades(engine)

    columns = {column["name"] for column in inspect(engine).get_columns("trace_runs")}
    assert set(added) == set(TRACE_RUN_ADDITIVE_COLUMNS)
    assert set(TRACE_RUN_ADDITIVE_COLUMNS) <= columns
    assert apply_desktop_sqlite_upgrades(engine) == []
