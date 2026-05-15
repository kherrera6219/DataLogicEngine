"""Add AuditBundle spec columns to trace_runs

Revision ID: d1e2f3a4b5c6
Revises: c1d2e3f4a5b6
Create Date: 2026-05-14

Adds spec Section 12.1 AuditBundle fields to trace_runs:
tier, coordinate17_id (FK → trace_axis_vectors), evidence_pack_hash,
layers_executed, refinement_cycles, regulatory_pass, security_pass,
truthgate_decision, token_cost, latency_ms.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "d1e2f3a4b5c6"
down_revision = "c1d2e3f4a5b6"
branch_labels = None
depends_on = None

_AUDIT_COLUMNS = [
    ("tier", sa.String(10)),
    ("coordinate17_id", sa.String(36)),   # UUID stored as string for SQLite compat
    ("evidence_pack_hash", sa.String(64)),
    ("layers_executed", sa.JSON()),
    ("refinement_cycles", sa.Integer()),
    ("regulatory_pass", sa.Boolean()),
    ("security_pass", sa.Boolean()),
    ("truthgate_decision", sa.String(16)),
    ("token_cost", sa.Integer()),
    ("latency_ms", sa.Integer()),
]


def _column_exists(inspector, table, col):
    return any(c["name"] == col for c in inspector.get_columns(table))


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    with op.batch_alter_table("trace_runs") as batch_op:
        for col_name, col_type in _AUDIT_COLUMNS:
            if not _column_exists(inspector, "trace_runs", col_name):
                batch_op.add_column(sa.Column(col_name, col_type, nullable=True))


def downgrade():
    with op.batch_alter_table("trace_runs") as batch_op:
        for col_name, _ in _AUDIT_COLUMNS:
            batch_op.drop_column(col_name)
