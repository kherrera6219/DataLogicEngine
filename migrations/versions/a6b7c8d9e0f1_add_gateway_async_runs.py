"""Add durable Phase 8 asynchronous gateway runs.

Revision ID: a6b7c8d9e0f1
Revises: f5a6b7c8d9e0
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "a6b7c8d9e0f1"
down_revision = "f5a6b7c8d9e0"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("external_api_keys") as batch_op:
        batch_op.add_column(sa.Column("deleted_at", sa.DateTime(), nullable=True))

    op.create_table(
        "gateway_async_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("request_id", sa.String(length=128), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("request_sha256", sa.String(length=64), nullable=False),
        sa.Column("api_key_id", sa.UUID(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="queued"),
        sa.Column("virtual_model", sa.String(length=64), nullable=False),
        sa.Column("request_encryption", sa.String(length=32), nullable=False),
        sa.Column("request_ciphertext", sa.Text(), nullable=False),
        sa.Column("response_encryption", sa.String(length=32), nullable=True),
        sa.Column("response_ciphertext", sa.Text(), nullable=True),
        sa.Column(
            "response_storage",
            sa.String(length=32),
            nullable=False,
            server_default="postgresql_ciphertext",
        ),
        sa.Column("response_object_bucket", sa.String(length=100), nullable=True),
        sa.Column("response_object_key", sa.String(length=500), nullable=True),
        sa.Column("response_sha256", sa.String(length=64), nullable=True),
        sa.Column("response_size_bytes", sa.Integer(), nullable=True),
        sa.Column("response_status", sa.Integer(), nullable=True),
        sa.Column("run_id", sa.String(length=36), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("cancellation_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["api_key_id"], ["external_api_keys.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "api_key_id",
            "idempotency_key",
            name="uq_gateway_async_run_client_idempotency",
        ),
    )
    op.create_index(
        "ix_gateway_async_run_state_created",
        "gateway_async_runs",
        ["status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_gateway_async_run_request_id",
        "gateway_async_runs",
        ["request_id"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_gateway_async_run_request_id", table_name="gateway_async_runs")
    op.drop_index("ix_gateway_async_run_state_created", table_name="gateway_async_runs")
    op.drop_table("gateway_async_runs")
    with op.batch_alter_table("external_api_keys") as batch_op:
        batch_op.drop_column("deleted_at")
