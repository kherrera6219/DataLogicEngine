"""Add Phase 7 provider usage and privacy ledger fields.

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-07-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "d3e4f5a6b7c8"
down_revision = "c2d3e4f5a6b7"
branch_labels = None
depends_on = None


def _json_type():
    if op.get_bind().dialect.name == "postgresql":
        return postgresql.JSONB(astext_type=sa.Text())
    return sa.JSON()


def upgrade():
    with op.batch_alter_table("llm_provider_usage") as batch_op:
        batch_op.alter_column("provider_id", existing_type=sa.UUID(), nullable=True)
        batch_op.add_column(sa.Column("provider_type", sa.String(length=32), nullable=False, server_default="unknown"))
        batch_op.add_column(sa.Column("session_id", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("purpose", sa.String(length=64), nullable=False, server_default="answer"))
        batch_op.add_column(sa.Column("request_stage", sa.String(length=64), nullable=False, server_default="provider_execution"))
        batch_op.add_column(sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"))
        batch_op.add_column(sa.Column("retry_index", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("pricing_status", sa.String(length=32), nullable=False, server_default="unknown"))
        batch_op.add_column(sa.Column("status", sa.String(length=32), nullable=False, server_default="completed"))
        batch_op.add_column(sa.Column("error_class", sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column("disclosed_categories", _json_type(), nullable=False, server_default="[]"))
        batch_op.add_column(sa.Column("idempotency_key", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("started_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("ended_at", sa.DateTime(), nullable=True))
        batch_op.create_index("ix_llm_provider_usage_run_stage", ["run_id", "request_stage"])
        batch_op.create_index("ix_llm_provider_usage_session_created", ["session_id", "created_at"])
        batch_op.create_index("ix_llm_provider_usage_status_created", ["status", "created_at"])


def downgrade():
    with op.batch_alter_table("llm_provider_usage") as batch_op:
        batch_op.drop_index("ix_llm_provider_usage_status_created")
        batch_op.drop_index("ix_llm_provider_usage_session_created")
        batch_op.drop_index("ix_llm_provider_usage_run_stage")
        for column in (
            "ended_at",
            "started_at",
            "idempotency_key",
            "disclosed_categories",
            "error_class",
            "status",
            "pricing_status",
            "retry_index",
            "attempt_number",
            "request_stage",
            "purpose",
            "session_id",
            "provider_type",
        ):
            batch_op.drop_column(column)
        batch_op.alter_column("provider_id", existing_type=sa.UUID(), nullable=False)
