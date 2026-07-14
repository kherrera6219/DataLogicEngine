"""Add cross-store deletion tombstones

Revision ID: a9b0c1d2e3f4
Revises: f8a9b0c1d2e3
Create Date: 2026-07-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision = "a9b0c1d2e3f4"
down_revision = "f8a9b0c1d2e3"
branch_labels = None
depends_on = None


def _json_type(bind):
    if bind.dialect.name == "postgresql":
        return postgresql.JSONB(astext_type=sa.Text())
    return sa.JSON()


def upgrade():
    bind = op.get_bind()
    if "data_deletion_tombstones" in inspect(bind).get_table_names():
        return
    op.create_table(
        "data_deletion_tombstones",
        sa.Column("deletion_id", sa.UUID(), nullable=False),
        sa.Column("subject_type", sa.String(length=40), nullable=False),
        sa.Column("subject_digest", sa.String(length=64), nullable=False),
        sa.Column("policy_version", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("store_status", _json_type(bind), nullable=False),
        sa.Column("safe_reason", sa.String(length=120), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("deletion_id"),
    )
    op.create_index(
        "ix_data_deletion_tombstone_status",
        "data_deletion_tombstones",
        ["status", "requested_at"],
    )
    op.create_index(
        op.f("ix_data_deletion_tombstones_subject_digest"),
        "data_deletion_tombstones",
        ["subject_digest"],
    )


def downgrade():
    bind = op.get_bind()
    if "data_deletion_tombstones" not in inspect(bind).get_table_names():
        return
    op.drop_index(
        op.f("ix_data_deletion_tombstones_subject_digest"),
        table_name="data_deletion_tombstones",
    )
    op.drop_index(
        "ix_data_deletion_tombstone_status",
        table_name="data_deletion_tombstones",
    )
    op.drop_table("data_deletion_tombstones")
