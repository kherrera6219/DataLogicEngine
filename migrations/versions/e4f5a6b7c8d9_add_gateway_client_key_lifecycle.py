"""Add Phase 8 gateway client-key lifecycle metadata.

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "e4f5a6b7c8d9"
down_revision = "d3e4f5a6b7c8"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("external_api_keys") as batch_op:
        batch_op.add_column(sa.Column("revoked_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("revoked_reason", sa.String(length=240), nullable=True))
        batch_op.add_column(sa.Column(
            "max_concurrent_requests",
            sa.Integer(),
            nullable=False,
            server_default="2",
        ))
        batch_op.add_column(sa.Column("rotated_from_id", sa.UUID(), nullable=True))
        batch_op.create_foreign_key(
            "fk_external_api_keys_rotated_from",
            "external_api_keys",
            ["rotated_from_id"],
            ["id"],
        )
        batch_op.create_index(
            "ix_external_api_keys_rotated_from",
            ["rotated_from_id"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("external_api_keys") as batch_op:
        batch_op.drop_index("ix_external_api_keys_rotated_from")
        batch_op.drop_constraint("fk_external_api_keys_rotated_from", type_="foreignkey")
        batch_op.drop_column("rotated_from_id")
        batch_op.drop_column("max_concurrent_requests")
        batch_op.drop_column("revoked_reason")
        batch_op.drop_column("revoked_at")
