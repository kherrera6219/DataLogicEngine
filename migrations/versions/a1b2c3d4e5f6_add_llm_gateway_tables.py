"""Add LLM Gateway tables

Revision ID: a1b2c3d4e5f6
Revises: b0d09ef7daef
Create Date: 2026-01-08 15:06:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "b0d09ef7daef"
branch_labels = None
depends_on = None


def _table_exists(inspector, table_name):
    return table_name in inspector.get_table_names()


def _index_exists(inspector, table_name, index_name):
    try:
        return any(idx.get("name") == index_name for idx in inspector.get_indexes(table_name))
    except Exception:
        return False


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _table_exists(inspector, "llm_providers"):
        op.create_table(
            "llm_providers",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("provider_type", sa.String(50), nullable=False),
            sa.Column("api_key_encrypted", sa.LargeBinary(), nullable=True),
            sa.Column("endpoint", sa.String(500), nullable=True),
            sa.Column("model_id", sa.String(100), nullable=True),
            sa.Column("deployment_name", sa.String(100), nullable=True),
            sa.Column("api_version", sa.String(20), nullable=True),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("is_default", sa.Boolean(), default=False),
            sa.Column("priority", sa.Integer(), default=100),
            sa.Column("rate_limit_rpm", sa.Integer(), nullable=True),
            sa.Column("rate_limit_tpm", sa.Integer(), nullable=True),
            sa.Column("timeout_seconds", sa.Integer(), default=30),
            sa.Column("max_retries", sa.Integer(), default=3),
            sa.Column("config", postgresql.JSONB(), nullable=True),
            sa.Column("tenant_id", sa.String(100), nullable=True),
            sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.Column("last_used_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        inspector = inspect(bind)

    if _table_exists(inspector, "llm_providers"):
        idx_name = "ix_llm_providers_name"
        idx_type = "ix_llm_providers_provider_type"
        idx_active = "ix_llm_providers_is_active"
        if not _index_exists(inspector, "llm_providers", idx_name):
            op.create_index(idx_name, "llm_providers", ["name"])
        if not _index_exists(inspector, "llm_providers", idx_type):
            op.create_index(idx_type, "llm_providers", ["provider_type"])
        if not _index_exists(inspector, "llm_providers", idx_active):
            op.create_index(idx_active, "llm_providers", ["is_active"])

    if not _table_exists(inspector, "llm_provider_usage"):
        op.create_table(
            "llm_provider_usage",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("provider_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("llm_providers.id"), nullable=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("api_key_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("external_api_keys.id"), nullable=True),
            sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("model", sa.String(100), nullable=True),
            sa.Column("tokens_in", sa.Integer(), default=0),
            sa.Column("tokens_out", sa.Integer(), default=0),
            sa.Column("latency_ms", sa.Integer(), nullable=True),
            sa.Column("success", sa.Boolean(), default=True),
            sa.Column("error_code", sa.String(50), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        inspector = inspect(bind)

    if _table_exists(inspector, "llm_provider_usage"):
        idx_provider = "ix_llm_provider_usage_provider_id"
        idx_created = "ix_llm_provider_usage_created_at"
        if not _index_exists(inspector, "llm_provider_usage", idx_provider):
            op.create_index(idx_provider, "llm_provider_usage", ["provider_id"])
        if not _index_exists(inspector, "llm_provider_usage", idx_created):
            op.create_index(idx_created, "llm_provider_usage", ["created_at"])

    if not _table_exists(inspector, "external_api_keys"):
        op.create_table(
            "external_api_keys",
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("key_prefix", sa.String(10), nullable=False),
            sa.Column("key_hash", sa.String(256), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("tenant_id", sa.String(100), nullable=True),
            sa.Column("permissions", postgresql.JSONB(), nullable=True),
            sa.Column("allowed_providers", postgresql.JSONB(), nullable=True),
            sa.Column("allowed_models", postgresql.JSONB(), nullable=True),
            sa.Column("rate_limit_rpm", sa.Integer(), default=60),
            sa.Column("rate_limit_daily", sa.Integer(), nullable=True),
            sa.Column("max_tokens_per_request", sa.Integer(), nullable=True),
            sa.Column("is_active", sa.Boolean(), default=True),
            sa.Column("expires_at", sa.DateTime(), nullable=True),
            sa.Column("total_requests", sa.Integer(), default=0),
            sa.Column("total_tokens", sa.Integer(), default=0),
            sa.Column("last_used_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        inspector = inspect(bind)

    if _table_exists(inspector, "external_api_keys"):
        idx_prefix = "ix_external_api_keys_key_prefix"
        idx_user = "ix_external_api_keys_user_id"
        idx_active = "ix_external_api_keys_is_active"
        if not _index_exists(inspector, "external_api_keys", idx_prefix):
            op.create_index(idx_prefix, "external_api_keys", ["key_prefix"])
        if not _index_exists(inspector, "external_api_keys", idx_user):
            op.create_index(idx_user, "external_api_keys", ["user_id"])
        if not _index_exists(inspector, "external_api_keys", idx_active):
            op.create_index(idx_active, "external_api_keys", ["is_active"])


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    if _table_exists(inspector, "llm_provider_usage"):
        op.drop_table("llm_provider_usage")
        inspector = inspect(bind)
    if _table_exists(inspector, "external_api_keys"):
        op.drop_table("external_api_keys")
        inspector = inspect(bind)
    if _table_exists(inspector, "llm_providers"):
        op.drop_table("llm_providers")
