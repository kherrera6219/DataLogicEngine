"""Add durable Phase 8 gateway idempotency authority.

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "f5a6b7c8d9e0"
down_revision = "e4f5a6b7c8d9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "gateway_idempotency_records",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("api_key_id", sa.UUID(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("request_sha256", sa.String(length=64), nullable=False),
        sa.Column("request_id", sa.String(length=128), nullable=False),
        sa.Column("state", sa.String(length=24), nullable=False, server_default="pending"),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("response_payload", sa.JSON(), nullable=True),
        sa.Column("run_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["api_key_id"], ["external_api_keys.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "api_key_id",
            "idempotency_key",
            name="uq_gateway_idempotency_client_key",
        ),
    )
    op.create_index(
        "ix_gateway_idempotency_state_expiry",
        "gateway_idempotency_records",
        ["state", "expires_at"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_gateway_idempotency_state_expiry",
        table_name="gateway_idempotency_records",
    )
    op.drop_table("gateway_idempotency_records")
