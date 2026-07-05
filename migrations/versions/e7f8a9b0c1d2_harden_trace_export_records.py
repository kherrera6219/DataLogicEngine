"""Harden trace export records

Revision ID: e7f8a9b0c1d2
Revises: d6e7f8a9b0c1
Create Date: 2026-07-05

Adds persisted export metadata and payload storage for trace export history and
download endpoints.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision = "e7f8a9b0c1d2"
down_revision = "d6e7f8a9b0c1"
branch_labels = None
depends_on = None

_TABLE = "trace_exports"


def _json_type(bind):
    if bind.dialect.name == "postgresql":
        return postgresql.JSONB(astext_type=sa.Text())
    return sa.JSON()


def _table_exists(inspector, table):
    return table in inspector.get_table_names()


def _column_exists(inspector, table, col):
    return any(c["name"] == col for c in inspector.get_columns(table))


def _index_exists(inspector, table, index_name):
    try:
        return any(idx.get("name") == index_name for idx in inspector.get_indexes(table))
    except Exception:
        return False


def _columns(bind):
    json_type = _json_type(bind)
    return [
        ("status", sa.String(length=20)),
        ("bundle_ref", sa.String(length=512)),
        ("manifest_hash", sa.String(length=128)),
        ("file_size_bytes", sa.Integer()),
        ("payload", json_type),
        ("options", json_type),
        ("encrypted", sa.Boolean()),
        ("signed", sa.Boolean()),
    ]


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _table_exists(inspector, _TABLE):
        op.create_table(
            _TABLE,
            sa.Column("export_id", sa.UUID(), nullable=False),
            sa.Column("run_id", sa.UUID(), nullable=False),
            sa.Column("format", sa.String(length=20), nullable=True),
            sa.Column("destination", sa.String(length=100), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=True),
            sa.Column("exported_at", sa.DateTime(), nullable=True),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("bundle_ref", sa.String(length=512), nullable=True),
            sa.Column("manifest_hash", sa.String(length=128), nullable=True),
            sa.Column("file_size_bytes", sa.Integer(), nullable=True),
            sa.Column("payload", _json_type(bind), nullable=True),
            sa.Column("options", _json_type(bind), nullable=True),
            sa.Column("encrypted", sa.Boolean(), nullable=True),
            sa.Column("signed", sa.Boolean(), nullable=True),
            sa.ForeignKeyConstraint(["run_id"], ["trace_runs.run_id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("export_id"),
        )
        inspector = inspect(bind)
    else:
        with op.batch_alter_table(_TABLE) as batch_op:
            for col_name, col_type in _columns(bind):
                if not _column_exists(inspector, _TABLE, col_name):
                    batch_op.add_column(sa.Column(col_name, col_type, nullable=True))
        inspector = inspect(bind)

    if not _index_exists(inspector, _TABLE, "ix_trace_exports_run_id"):
        op.create_index("ix_trace_exports_run_id", _TABLE, ["run_id"])
    if not _index_exists(inspector, _TABLE, "ix_trace_exports_user_id"):
        op.create_index("ix_trace_exports_user_id", _TABLE, ["user_id"])
    if not _index_exists(inspector, _TABLE, "ix_trace_exports_exported_at"):
        op.create_index("ix_trace_exports_exported_at", _TABLE, ["exported_at"])


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    if not _table_exists(inspector, _TABLE):
        return

    for index_name in (
        "ix_trace_exports_exported_at",
        "ix_trace_exports_user_id",
        "ix_trace_exports_run_id",
    ):
        if _index_exists(inspector, _TABLE, index_name):
            op.drop_index(index_name, table_name=_TABLE)

    inspector = inspect(bind)
    with op.batch_alter_table(_TABLE) as batch_op:
        for col_name, _ in reversed(_columns(bind)):
            if _column_exists(inspector, _TABLE, col_name):
                batch_op.drop_column(col_name)
