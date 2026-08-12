"""Verified adoption of released desktop SQLite/object data into the current product.

The adopter is intentionally conservative: it never deletes the source, never
overwrites populated target tables, and writes its receipt only after a verified
SQLite recovery copy and post-import count/hash checks pass.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import sqlite3
import uuid
from datetime import UTC, date, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, JSON, MetaData, String, Table, Uuid, func, inspect, select, text
from sqlalchemy.engine import Engine

from backend.security.windows_acl import ensure_restricted_user_acl


ADOPTION_SCHEMA_VERSION = "dle.retained-data-adoption.v1"
SOURCE_PRODUCT_VERSION = "0.1.1"
EXCLUDED_TABLES = {"alembic_version"}
RETAINED_COLUMN_DEFAULTS: dict[str, dict[str, Any]] = {
    "llm_provider_usage": {
        "provider_type": "legacy",
        "purpose": "legacy_activity",
        "request_stage": "legacy_provider_execution",
        "attempt_number": 1,
        "retry_index": 0,
        "pricing_status": "unknown",
        "status": "completed",
        "disclosed_categories": [],
    }
}


class LegacyAdoptionError(RuntimeError):
    """Safely reportable retained-data adoption failure."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sqlite_source_sha256(path: Path) -> str:
    """Hash the retained SQLite database and any committed WAL payload."""
    digest = hashlib.sha256()
    for candidate in (path, Path(f"{path}-wal")):
        if not candidate.is_file():
            continue
        digest.update(candidate.name.encode("utf-8"))
        with candidate.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def _open_source(path: Path) -> sqlite3.Connection:
    try:
        connection = sqlite3.connect(
            f"file:{path.as_posix()}?mode=ro",
            uri=True,
        )
        connection.execute("PRAGMA query_only=ON")
        result = connection.execute("PRAGMA integrity_check").fetchone()
    except sqlite3.DatabaseError as exc:
        raise LegacyAdoptionError("retained_sqlite_unreadable") from exc
    if not result or result[0] != "ok":
        connection.close()
        raise LegacyAdoptionError("retained_sqlite_integrity_failed")
    connection.row_factory = sqlite3.Row
    return connection


def create_verified_sqlite_recovery_copy(source: Path, destination: Path) -> dict[str, Any]:
    """Use SQLite's online backup API and verify the independent recovery copy."""
    source = source.resolve()
    destination = destination.resolve()
    if not source.is_file():
        raise LegacyAdoptionError("retained_sqlite_missing")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.unlink(missing_ok=True)
    source_connection = _open_source(source)
    try:
        target_connection = sqlite3.connect(temporary)
        try:
            source_connection.backup(target_connection)
            result = target_connection.execute("PRAGMA integrity_check").fetchone()
        finally:
            target_connection.close()
    finally:
        source_connection.close()
    if not result or result[0] != "ok":
        temporary.unlink(missing_ok=True)
        raise LegacyAdoptionError("retained_sqlite_backup_verification_failed")
    os.replace(temporary, destination)
    ensure_restricted_user_acl(destination, required=os.name == "nt")
    return {
        "path": str(destination),
        "size_bytes": destination.stat().st_size,
        "sha256": _sha256(destination),
        "integrity": "ok",
    }


def _source_tables(connection: sqlite3.Connection) -> list[str]:
    return [
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        if str(row[0]) not in EXCLUDED_TABLES
    ]


def build_sqlite_adoption_plan(source: Path, target_engine: Engine) -> dict[str, Any]:
    """Build a content-free import plan and report every incompatible table."""
    source = source.resolve()
    source_connection = _open_source(source)
    try:
        target_inspector = inspect(target_engine)
        target_names = set(target_inspector.get_table_names())
        tables: list[dict[str, Any]] = []
        blockers: list[str] = []
        for name in _source_tables(source_connection):
            escaped = name.replace('"', '""')
            row_count = int(
                source_connection.execute(
                    f'SELECT count(*) FROM "{escaped}"'  # nosec B608 -- identifier is SQLite-catalog-derived and quoted
                ).fetchone()[0]
            )
            if row_count == 0:
                continue
            if name not in target_names:
                blockers.append(f"target_table_missing:{name}")
                tables.append({"table": name, "source_rows": row_count, "action": "blocked"})
                continue
            source_columns = {
                str(row[1])
                for row in source_connection.execute(f'PRAGMA table_info("{escaped}")')
            }
            source_column_types = {
                str(row[1]): str(row[2]).upper()
                for row in source_connection.execute(f'PRAGMA table_info("{escaped}")')
            }
            target_columns = target_inspector.get_columns(name)
            target_names_for_table = {str(column["name"]) for column in target_columns}
            common = sorted(source_columns & target_names_for_table)
            required_missing = sorted(
                str(column["name"])
                for column in target_columns
                if str(column["name"]) not in source_columns
                and not bool(column.get("nullable", True))
                and column.get("default") is None
                and not bool(column.get("autoincrement"))
                and str(column["name"]) not in RETAINED_COLUMN_DEFAULTS.get(name, {})
            )
            if required_missing:
                blockers.append(f"required_target_columns_missing:{name}:{','.join(required_missing)}")
            tables.append(
                {
                    "table": name,
                    "source_rows": row_count,
                    "common_columns": common,
                    "source_column_types": {
                        column: source_column_types[column] for column in common
                    },
                    "source_only_columns": sorted(source_columns - target_names_for_table),
                    "required_target_columns_missing": required_missing,
                    "action": "import" if common and not required_missing else "blocked",
                }
            )
        return {
            "schema_version": ADOPTION_SCHEMA_VERSION,
            "source_version": SOURCE_PRODUCT_VERSION,
            "source_size_bytes": source.stat().st_size,
            "source_sha256": _sqlite_source_sha256(source),
            "tables": tables,
            "source_row_count": sum(int(item["source_rows"]) for item in tables),
            "blockers": sorted(blockers),
            "ready": not blockers and all(item["action"] == "import" for item in tables),
        }
    finally:
        source_connection.close()


def _target_tables_in_dependency_order(engine: Engine, names: set[str]) -> list[Table]:
    metadata = MetaData()
    metadata.reflect(bind=engine, only=sorted(names))
    return [table for table in metadata.sorted_tables if table.name in names]


def _coerce_value(column, value: Any, *, source_type: str = "") -> Any:
    """Convert SQLite's weakly typed values to the target SQLAlchemy contract."""
    if value is None:
        return None
    column_type = column.type
    if source_type == "UUID" or isinstance(column_type, Uuid):
        try:
            parsed = uuid.UUID(str(value))
        except (ValueError, AttributeError) as exc:
            raise LegacyAdoptionError(
                f"retained_uuid_invalid:{column.table.name}:{column.name}"
            ) from exc
        return str(parsed) if isinstance(column_type, String) else parsed
    if isinstance(column_type, Boolean):
        return bool(value)
    if isinstance(column_type, DateTime) and not isinstance(value, datetime):
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError as exc:
            raise LegacyAdoptionError(
                f"retained_datetime_invalid:{column.table.name}:{column.name}"
            ) from exc
    if isinstance(column_type, Date) and not isinstance(value, (date, datetime)):
        try:
            return date.fromisoformat(str(value))
        except ValueError as exc:
            raise LegacyAdoptionError(
                f"retained_date_invalid:{column.table.name}:{column.name}"
            ) from exc
    if isinstance(column_type, JSON) and isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return value
    return value


def _transform_retained_row(table_name: str, row: dict[str, Any]) -> dict[str, Any]:
    """Apply explicit security transitions without discarding product history.

    Provider ciphertext from the legacy desktop release was protected under a
    different key contract.  The verified source recovery copy retains it, but
    carrying it into the live service could make a provider look usable when it
    is not.  Import the provider definition and history in a disabled state so
    the owner can re-enter the credential through the current DPAPI flow.
    """
    if table_name == "llm_providers":
        row["api_key_encrypted"] = None
        row["is_active"] = False
        row["is_default"] = False
    return row


def _prepare_row(table: Table, item: dict[str, Any], row: sqlite3.Row) -> dict[str, Any]:
    source_types = item.get("source_column_types", {})
    values = {
        column: _coerce_value(
            table.columns[column],
            row[column],
            source_type=source_types.get(column, ""),
        )
        for column in item["common_columns"]
    }
    values.update(RETAINED_COLUMN_DEFAULTS.get(table.name, {}))
    if table.name == "llm_provider_usage" and not bool(values.get("success", True)):
        values["status"] = "failed"
    return _transform_retained_row(table.name, values)


def _fingerprint_values(rows: list[tuple[Any, ...]]) -> str:
    normalized = sorted(
        json.dumps([str(value) for value in row], separators=(",", ":"))
        for row in rows
    )
    return hashlib.sha256("\n".join(normalized).encode("utf-8")).hexdigest()


def _primary_key_fingerprints(
    source_connection: sqlite3.Connection,
    target_connection,
    table: Table,
    item: dict[str, Any],
) -> tuple[str, str]:
    primary_keys = [column for column in table.primary_key.columns]
    if not primary_keys:
        raise LegacyAdoptionError(f"retained_target_existing_without_key:{table.name}")
    escaped_table = table.name.replace('"', '""')
    selected = ",".join(
        f'"{column.name.replace(chr(34), chr(34) * 2)}"' for column in primary_keys
    )
    source_rows = [
        tuple(
            _coerce_value(
                column,
                row[column.name],
                source_type=item.get("source_column_types", {}).get(column.name, ""),
            )
            for column in primary_keys
        )
        for row in source_connection.execute(
            f'SELECT {selected} FROM "{escaped_table}"'  # nosec B608 -- reflected identifiers are quoted
        )
    ]
    target_rows = [tuple(row) for row in target_connection.execute(select(*primary_keys))]
    return _fingerprint_values(source_rows), _fingerprint_values(target_rows)


def import_sqlite_rows(
    source: Path,
    target_engine: Engine,
    *,
    plan: dict[str, Any],
    batch_size: int = 500,
) -> dict[str, int]:
    """Import planned rows transactionally into empty target tables."""
    if not plan.get("ready"):
        raise LegacyAdoptionError("retained_sqlite_plan_blocked")
    if plan.get("source_sha256") != _sqlite_source_sha256(source):
        raise LegacyAdoptionError("retained_sqlite_changed_after_plan")
    planned = {str(item["table"]): item for item in plan.get("tables", [])}
    tables = _target_tables_in_dependency_order(target_engine, set(planned))
    if target_engine.dialect.name == "sqlite":
        # SQLite reports SQLAlchemy UUID columns as NUMERIC when reflecting a
        # table.  Restore the declared retained type so UUID text is bound as
        # text in disposable qualification databases instead of coerced to a
        # floating-point number.  PostgreSQL retains its native UUID type.
        for table in tables:
            source_types = planned[table.name].get("source_column_types", {})
            for column in table.columns:
                if source_types.get(column.name) == "UUID":
                    column.type = String(36)
    source_connection = _open_source(source)
    imported: dict[str, int] = {}
    try:
        with target_engine.begin() as target:
            existing_counts = {
                table.name: int(
                    target.execute(select(func.count()).select_from(table)).scalar_one()
                )
                for table in tables
            }
            if any(existing_counts.values()):
                for table in tables:
                    expected = int(planned[table.name]["source_rows"])
                    if existing_counts[table.name] != expected:
                        raise LegacyAdoptionError(f"retained_target_not_empty:{table.name}")
                    source_fingerprint, target_fingerprint = _primary_key_fingerprints(
                        source_connection,
                        target,
                        table,
                        planned[table.name],
                    )
                    if source_fingerprint != target_fingerprint:
                        raise LegacyAdoptionError(
                            f"retained_target_identity_mismatch:{table.name}"
                        )
                    imported[table.name] = expected
                return imported
            for table in tables:
                item = planned[table.name]
                columns = [str(column) for column in item["common_columns"]]
                escaped_table = table.name.replace('"', '""')
                selected_columns = ",".join(
                    f'"{column.replace(chr(34), chr(34) * 2)}"' for column in columns
                )
                cursor = source_connection.execute(
                    f'SELECT {selected_columns} FROM "{escaped_table}"'  # nosec B608 -- plan identifiers are catalog-verified and quoted
                )
                count = 0
                while True:
                    rows = cursor.fetchmany(max(1, int(batch_size)))
                    if not rows:
                        break
                    target.execute(
                        table.insert(),
                        [_prepare_row(table, item, row) for row in rows],
                    )
                    count += len(rows)
                imported[table.name] = count
            for table in tables:
                actual = int(
                    target.execute(select(func.count()).select_from(table)).scalar_one()
                )
                if actual != imported[table.name]:
                    raise LegacyAdoptionError(f"retained_target_count_mismatch:{table.name}")
    finally:
        source_connection.close()
    return imported


def synchronize_postgresql_sequences(target_engine: Engine) -> dict[str, int]:
    """Advance owned serial sequences after retained rows keep their IDs.

    SQLite stores integer primary keys directly. PostgreSQL keeps the next
    value in a separate sequence, so a verified row import must advance those
    sequences before normal application writes resume.
    """
    if target_engine.dialect.name != "postgresql":
        return {}

    sequence_query = text(
        """
        SELECT table_schema, table_name, column_name,
               pg_get_serial_sequence(
                   quote_ident(table_schema) || '.' || quote_ident(table_name),
                   column_name
               ) AS sequence_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND column_default LIKE 'nextval(%'
        ORDER BY table_name, column_name
        """
    )
    metadata = MetaData()
    synchronized: dict[str, int] = {}
    with target_engine.begin() as connection:
        sequence_rows = connection.execute(sequence_query).mappings().all()
        for row in sequence_rows:
            sequence_name = row["sequence_name"]
            if not sequence_name:
                continue
            table = Table(
                str(row["table_name"]),
                metadata,
                schema=str(row["table_schema"]),
                autoload_with=connection,
            )
            column = table.columns[str(row["column_name"])]
            maximum = connection.execute(select(func.max(column))).scalar_one()
            next_base = int(maximum) if maximum is not None else 1
            connection.execute(
                text("SELECT setval(to_regclass(:sequence_name), :value, :is_called)"),
                {
                    "sequence_name": str(sequence_name),
                    "value": next_base,
                    "is_called": maximum is not None,
                },
            )
            synchronized[f"{table.name}.{column.name}"] = next_base
    return synchronized


def import_legacy_objects(source_root: Path, object_store: Any) -> dict[str, Any]:
    """Copy legacy filesystem objects to the managed object service with hash parity."""
    source_root = source_root.resolve()
    if not source_root.is_dir():
        return {"object_count": 0, "size_bytes": 0, "sha256": {}}
    imported: dict[str, str] = {}
    total_size = 0
    for path in sorted(item for item in source_root.rglob("*") if item.is_file()):
        if path.name.endswith(".meta"):
            continue
        relative = PurePosixPath(path.relative_to(source_root).as_posix())
        if len(relative.parts) < 2:
            raise LegacyAdoptionError("retained_object_bucket_missing")
        bucket = relative.parts[0].replace("_", "-")
        key = PurePosixPath(*relative.parts[1:]).as_posix()
        payload = path.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        object_store.put(
            bucket,
            key,
            payload,
            content_type=mimetypes.guess_type(path.name)[0] or "application/octet-stream",
            metadata={"sha256": digest, "adopted-from": SOURCE_PRODUCT_VERSION},
        )
        if hashlib.sha256(object_store.get(bucket, key)).hexdigest() != digest:
            raise LegacyAdoptionError(f"retained_object_hash_mismatch:{bucket}:{key}")
        imported[f"{bucket}/{key}"] = digest
        total_size += len(payload)
    return {
        "object_count": len(imported),
        "size_bytes": total_size,
        "sha256": imported,
    }


def write_adoption_receipt(path: Path, payload: dict[str, Any]) -> None:
    """Persist the final receipt atomically after every parity check passes."""
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema_version": ADOPTION_SCHEMA_VERSION,
        "source_version": SOURCE_PRODUCT_VERSION,
        "target_version": str(payload["target_version"]),
        "completed_at": datetime.now(UTC).isoformat(),
        "source_sha256": str(payload["source_sha256"]),
        "backup_sha256": str(payload["backup_sha256"]),
        "tables": dict(payload["tables"]),
        "objects": dict(payload["objects"]),
        "graph": dict(payload.get("graph") or {}),
        "status": "verified",
    }
    temporary = path.with_suffix(path.suffix + ".tmp")
    try:
        temporary.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)
        ensure_restricted_user_acl(path, required=os.name == "nt")
    finally:
        temporary.unlink(missing_ok=True)
