"""Add durable cross-store outbox and materialization state

Revision ID: f8a9b0c1d2e3
Revises: e7f8a9b0c1d2
Create Date: 2026-07-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision = "f8a9b0c1d2e3"
down_revision = "e7f8a9b0c1d2"
branch_labels = None
depends_on = None


def _json_type(bind):
    if bind.dialect.name == "postgresql":
        return postgresql.JSONB(astext_type=sa.Text())
    return sa.JSON()


def _table_exists(inspector, table_name):
    return table_name in inspector.get_table_names()


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    if not _table_exists(inspector, "cross_store_outbox_events"):
        op.create_table(
            "cross_store_outbox_events",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("entity_type", sa.String(length=120), nullable=False),
            sa.Column("entity_id", sa.String(length=255), nullable=False),
            sa.Column("destination", sa.String(length=32), nullable=False),
            sa.Column("operation", sa.String(length=80), nullable=False),
            sa.Column("schema_version", sa.String(length=80), nullable=False),
            sa.Column("source_revision", sa.String(length=255), nullable=False),
            sa.Column("correlation_id", sa.String(length=128), nullable=False),
            sa.Column("payload", _json_type(bind), nullable=False),
            sa.Column("payload_sha256", sa.String(length=64), nullable=False),
            sa.Column("status", sa.String(length=24), nullable=False),
            sa.Column("attempts", sa.Integer(), nullable=False),
            sa.Column("available_at", sa.DateTime(), nullable=True),
            sa.Column("locked_at", sa.DateTime(), nullable=True),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("safe_reason", sa.String(length=120), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "entity_type",
                "entity_id",
                "destination",
                "operation",
                "source_revision",
                name="uq_cross_store_outbox_source_delivery",
            ),
        )
        op.create_index(
            "ix_cross_store_outbox_pending",
            "cross_store_outbox_events",
            ["status", "available_at"],
        )
        op.create_index(
            "ix_cross_store_outbox_destination",
            "cross_store_outbox_events",
            ["destination", "status"],
        )
        op.create_index(
            "ix_cross_store_outbox_entity",
            "cross_store_outbox_events",
            ["entity_type", "entity_id"],
        )

    inspector = inspect(bind)
    if not _table_exists(inspector, "cross_store_materialization_states"):
        op.create_table(
            "cross_store_materialization_states",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("entity_type", sa.String(length=120), nullable=False),
            sa.Column("entity_id", sa.String(length=255), nullable=False),
            sa.Column("destination", sa.String(length=32), nullable=False),
            sa.Column("schema_version", sa.String(length=80), nullable=False),
            sa.Column("source_revision", sa.String(length=255), nullable=False),
            sa.Column("observed_revision", sa.String(length=255), nullable=True),
            sa.Column("payload_sha256", sa.String(length=64), nullable=False),
            sa.Column("state", sa.String(length=24), nullable=False),
            sa.Column("attempts", sa.Integer(), nullable=False),
            sa.Column("safe_reason", sa.String(length=120), nullable=True),
            sa.Column("last_attempt_at", sa.DateTime(), nullable=True),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "entity_type",
                "entity_id",
                "destination",
                name="uq_cross_store_materialization_entity_destination",
            ),
        )
        op.create_index(
            "ix_cross_store_materialization_state",
            "cross_store_materialization_states",
            ["destination", "state"],
        )


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    if _table_exists(inspector, "cross_store_materialization_states"):
        op.drop_index(
            "ix_cross_store_materialization_state",
            table_name="cross_store_materialization_states",
        )
        op.drop_table("cross_store_materialization_states")
    inspector = inspect(bind)
    if _table_exists(inspector, "cross_store_outbox_events"):
        for index_name in (
            "ix_cross_store_outbox_entity",
            "ix_cross_store_outbox_destination",
            "ix_cross_store_outbox_pending",
        ):
            op.drop_index(index_name, table_name="cross_store_outbox_events")
        op.drop_table("cross_store_outbox_events")
