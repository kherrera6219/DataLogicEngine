"""Add durable canonical KA product workflow runs.

Revision ID: 0a1b2c3d4e5f
Revises: f1a2b3c4d5e6
"""

import sqlalchemy as sa
from alembic import op

revision = "0a1b2c3d4e5f"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ka_product_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("request_id", sa.String(length=128), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("request_sha256", sa.String(length=64), nullable=False),
        sa.Column("canonical_id", sa.String(length=50), nullable=False),
        sa.Column("manifest_version", sa.String(length=80), nullable=False),
        sa.Column("principal_key", sa.String(length=64), nullable=False),
        sa.Column("api_key_id", sa.UUID(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("mode", sa.String(length=24), nullable=False),
        sa.Column("risk_tier", sa.String(length=24), nullable=False),
        sa.Column("confirmation_required", sa.Boolean(), nullable=False),
        sa.Column("confirmation_digest", sa.String(length=64), nullable=True),
        sa.Column("confirmation_expires_at", sa.DateTime(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("plan_payload", sa.JSON(), nullable=False),
        sa.Column("request_encryption", sa.String(length=32), nullable=False),
        sa.Column("request_ciphertext", sa.Text(), nullable=False),
        sa.Column("result_encryption", sa.String(length=32), nullable=True),
        sa.Column("result_ciphertext", sa.Text(), nullable=True),
        sa.Column("result_sha256", sa.String(length=64), nullable=True),
        sa.Column("result_size_bytes", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("cancellation_requested", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["api_key_id"],
            ["external_api_keys.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "principal_key",
            "idempotency_key",
            name="uq_ka_product_run_principal_idempotency",
        ),
    )
    op.create_index(
        "ix_ka_product_run_request_id",
        "ka_product_runs",
        ["request_id"],
        unique=False,
    )
    op.create_index(
        "ix_ka_product_run_state_created",
        "ka_product_runs",
        ["status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_ka_product_run_user_created",
        "ka_product_runs",
        ["user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_ka_product_run_user_created",
        table_name="ka_product_runs",
    )
    op.drop_index(
        "ix_ka_product_run_state_created",
        table_name="ka_product_runs",
    )
    op.drop_index(
        "ix_ka_product_run_request_id",
        table_name="ka_product_runs",
    )
    op.drop_table("ka_product_runs")
