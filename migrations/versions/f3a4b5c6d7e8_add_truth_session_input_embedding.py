"""Add TruthSession input embedding

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c6d7
Create Date: 2026-05-25

Stores local deterministic query embeddings for DB-P historical drift baselines.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "f3a4b5c6d7e8"
down_revision = "e2f3a4b5c6d7"
branch_labels = None
depends_on = None


def _column_exists(inspector, table, col):
    return any(c["name"] == col for c in inspector.get_columns(table))


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    with op.batch_alter_table("truth_sessions") as batch_op:
        if not _column_exists(inspector, "truth_sessions", "input_embedding"):
            batch_op.add_column(sa.Column("input_embedding", sa.Text(), nullable=True))


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    with op.batch_alter_table("truth_sessions") as batch_op:
        if _column_exists(inspector, "truth_sessions", "input_embedding"):
            batch_op.drop_column("input_embedding")
