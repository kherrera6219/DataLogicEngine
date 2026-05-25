"""Add Phase B FROST trace fields

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-05-24

Adds Axis 17 FROST-mode selector outputs to trace_runs.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "e2f3a4b5c6d7"
down_revision = "d1e2f3a4b5c6"
branch_labels = None
depends_on = None

_COLUMNS = [
    ("frost_depth", sa.Integer()),
    ("truth_engine_mode", sa.String(50)),
]


def _column_exists(inspector, table, col):
    return any(c["name"] == col for c in inspector.get_columns(table))


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    with op.batch_alter_table("trace_runs") as batch_op:
        for col_name, col_type in _COLUMNS:
            if not _column_exists(inspector, "trace_runs", col_name):
                batch_op.add_column(sa.Column(col_name, col_type, nullable=True))


def downgrade():
    with op.batch_alter_table("trace_runs") as batch_op:
        for col_name, _ in reversed(_COLUMNS):
            batch_op.drop_column(col_name)
