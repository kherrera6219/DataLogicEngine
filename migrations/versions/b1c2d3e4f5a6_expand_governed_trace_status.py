"""Expand governed trace status storage

Revision ID: b1c2d3e4f5a6
Revises: a9b0c1d2e3f4
Create Date: 2026-07-13

The governed.v1 contract includes ``capability_unavailable`` (22 characters).
The previous 20-character column forced persistence to store a different value
than the API returned.
"""

from alembic import op
import sqlalchemy as sa


revision = "b1c2d3e4f5a6"
down_revision = "a9b0c1d2e3f4"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("trace_runs") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sa.String(length=20),
            type_=sa.String(length=32),
            existing_nullable=True,
        )


def downgrade():
    with op.batch_alter_table("trace_runs") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sa.String(length=32),
            type_=sa.String(length=20),
            existing_nullable=True,
        )
