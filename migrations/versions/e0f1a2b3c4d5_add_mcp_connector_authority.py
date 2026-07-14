"""Add Phase 11 durable MCP connector authority.

Revision ID: e0f1a2b3c4d5
Revises: d9e0f1a2b3c4
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "e0f1a2b3c4d5"
down_revision = "d9e0f1a2b3c4"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("mcp_servers") as batch:
        batch.alter_column(
            "protocol_version",
            existing_type=sa.String(32),
            server_default="2025-11-25",
        )
        batch.add_column(sa.Column("transport", sa.String(32), nullable=False, server_default="stdio"))
        batch.add_column(sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column("consent_state", sa.String(32), nullable=False, server_default="pending"))
        batch.add_column(sa.Column("requested_scopes", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("approved_scopes", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("command_fingerprint", sa.String(64), nullable=True))
        batch.add_column(sa.Column("containment_status", sa.String(32), nullable=False, server_default="not_qualified"))
        batch.add_column(sa.Column("health_status", sa.String(32), nullable=False, server_default="not_started"))
        batch.add_column(sa.Column("last_error_code", sa.String(100), nullable=True))
        batch.add_column(sa.Column("last_error_message", sa.String(500), nullable=True))
        batch.add_column(sa.Column("config_revision", sa.Integer(), nullable=False, server_default="1"))
        batch.add_column(sa.Column("credential_blobs", sa.JSON(), nullable=True))
        batch.create_index("ix_mcp_servers_command_fingerprint", ["command_fingerprint"])
    op.execute(
        sa.text(
            "UPDATE mcp_servers SET protocol_version = '2025-11-25' "
            "WHERE protocol_version IS NULL OR protocol_version = '2024-11-05'"
        )
    )

    op.create_table(
        "mcp_consent_grants",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("server_id", sa.Integer(), nullable=False),
        sa.Column("principal_id", sa.String(64), nullable=False),
        sa.Column("command_fingerprint", sa.String(64), nullable=False),
        sa.Column("requested_scopes", sa.JSON(), nullable=False),
        sa.Column("approved_scopes", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="approved"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["server_id"], ["mcp_servers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mcp_consent_grants_principal_id", "mcp_consent_grants", ["principal_id"])
    op.create_index("ix_mcp_consent_grants_command_fingerprint", "mcp_consent_grants", ["command_fingerprint"])
    op.create_index("ix_mcp_consent_server_status", "mcp_consent_grants", ["server_id", "status"])

    op.create_table(
        "mcp_lifecycle_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("server_id", sa.Integer(), nullable=False),
        sa.Column("principal_id", sa.String(64), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["server_id"], ["mcp_servers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mcp_lifecycle_events_principal_id", "mcp_lifecycle_events", ["principal_id"])
    op.create_index("ix_mcp_lifecycle_server_created", "mcp_lifecycle_events", ["server_id", "created_at"])

    op.create_table(
        "mcp_execution_records",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("execution_id", sa.String(36), nullable=False),
        sa.Column("server_id", sa.Integer(), nullable=False),
        sa.Column("tool_id", sa.Integer(), nullable=True),
        sa.Column("principal_id", sa.String(64), nullable=False),
        sa.Column("operation", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="running"),
        sa.Column("required_scopes", sa.JSON(), nullable=True),
        sa.Column("request_sha256", sa.String(64), nullable=False),
        sa.Column("result_sha256", sa.String(64), nullable=True),
        sa.Column("result_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("result_content", sa.Text(), nullable=True),
        sa.Column("result_trust", sa.String(64), nullable=True),
        sa.Column("artifact_object_key", sa.String(1024), nullable=True),
        sa.Column("prompt_injection_risk", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("error_code", sa.String(100), nullable=True),
        sa.Column("error_message", sa.String(500), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("trace_id", sa.String(36), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["server_id"], ["mcp_servers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tool_id"], ["mcp_tools.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("execution_id"),
    )
    op.create_index("ix_mcp_execution_records_execution_id", "mcp_execution_records", ["execution_id"])
    op.create_index("ix_mcp_execution_records_principal_id", "mcp_execution_records", ["principal_id"])
    op.create_index("ix_mcp_execution_records_trace_id", "mcp_execution_records", ["trace_id"])
    op.create_index("ix_mcp_execution_server_status", "mcp_execution_records", ["server_id", "status"])
    op.create_index("ix_mcp_execution_server_started", "mcp_execution_records", ["server_id", "started_at"])


def downgrade():
    op.drop_index("ix_mcp_execution_server_started", table_name="mcp_execution_records")
    op.drop_index("ix_mcp_execution_server_status", table_name="mcp_execution_records")
    op.drop_index("ix_mcp_execution_records_trace_id", table_name="mcp_execution_records")
    op.drop_index("ix_mcp_execution_records_principal_id", table_name="mcp_execution_records")
    op.drop_index("ix_mcp_execution_records_execution_id", table_name="mcp_execution_records")
    op.drop_table("mcp_execution_records")
    op.drop_index("ix_mcp_lifecycle_server_created", table_name="mcp_lifecycle_events")
    op.drop_index("ix_mcp_lifecycle_events_principal_id", table_name="mcp_lifecycle_events")
    op.drop_table("mcp_lifecycle_events")
    op.drop_index("ix_mcp_consent_server_status", table_name="mcp_consent_grants")
    op.drop_index("ix_mcp_consent_grants_command_fingerprint", table_name="mcp_consent_grants")
    op.drop_index("ix_mcp_consent_grants_principal_id", table_name="mcp_consent_grants")
    op.drop_table("mcp_consent_grants")

    with op.batch_alter_table("mcp_servers") as batch:
        batch.drop_index("ix_mcp_servers_command_fingerprint")
        for column in (
            "credential_blobs",
            "config_revision",
            "last_error_message",
            "last_error_code",
            "health_status",
            "containment_status",
            "command_fingerprint",
            "approved_scopes",
            "requested_scopes",
            "consent_state",
            "enabled",
            "transport",
        ):
            batch.drop_column(column)
        batch.alter_column(
            "protocol_version",
            existing_type=sa.String(32),
            server_default="2024-11-05",
        )
