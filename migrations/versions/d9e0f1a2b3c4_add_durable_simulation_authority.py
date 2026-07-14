"""Add Phase 10 durable simulation workflow authorities.

Revision ID: d9e0f1a2b3c4
Revises: c8d9e0f1a2b3
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "d9e0f1a2b3c4"
down_revision = "c8d9e0f1a2b3"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("simulation_sessions") as batch:
        batch.add_column(sa.Column("contract_version", sa.String(32), nullable=False, server_default="dle-simulation.v1"))
        batch.add_column(sa.Column("engine_id", sa.String(64), nullable=False, server_default="multi-agent-debate"))
        batch.add_column(sa.Column("engine_version", sa.String(32), nullable=False, server_default="3.0.0"))
        batch.add_column(sa.Column("scenario_revision", sa.String(64), nullable=True))
        batch.add_column(sa.Column("seed", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("plan", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("budget", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("provider_call_count", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("tool_call_count", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("checkpoint_sequence", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("revision", sa.Integer(), nullable=False, server_default="1"))
        batch.add_column(sa.Column("trace_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("last_error_code", sa.String(100), nullable=True))
        batch.add_column(sa.Column("last_error_message", sa.String(500), nullable=True))
        batch.add_column(sa.Column("pause_requested_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("cancellation_requested_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("artifact_state", sa.String(32), nullable=False, server_default="pending"))

    op.create_table(
        "simulation_steps",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("step_key", sa.String(64), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("input_hash", sa.String(64), nullable=False),
        sa.Column("output_hash", sa.String(64), nullable=True),
        sa.Column("output_summary", sa.Text(), nullable=True),
        sa.Column("validation", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["simulation_sessions.session_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "sequence", "attempt_number", name="uq_simulation_step_attempt"),
    )
    op.create_index("ix_simulation_steps_session_status", "simulation_steps", ["session_id", "status"])
    op.create_index("ix_simulation_steps_session_sequence", "simulation_steps", ["session_id", "sequence"])

    op.create_table(
        "simulation_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("step_key", sa.String(64), nullable=True),
        sa.Column("progress_current", sa.Integer(), nullable=True),
        sa.Column("progress_total", sa.Integer(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["simulation_sessions.session_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "sequence", name="uq_simulation_event_sequence"),
    )
    op.create_index("ix_simulation_events_session_created", "simulation_events", ["session_id", "created_at"])

    op.create_table(
        "simulation_provider_calls",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("step_id", sa.UUID(), nullable=True),
        sa.Column("call_index", sa.Integer(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("purpose", sa.String(64), nullable=False),
        sa.Column("persona_id", sa.String(64), nullable=True),
        sa.Column("provider_type", sa.String(32), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("tokens_in", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokens_out", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_cost_usd", sa.Numeric(12, 8), nullable=True),
        sa.Column("pricing_status", sa.String(32), nullable=False, server_default="unknown"),
        sa.Column("disclosed_categories", sa.JSON(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(100), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["simulation_sessions.session_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["step_id"], ["simulation_steps.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "session_id",
            "call_index",
            "attempt_number",
            name="uq_simulation_provider_call_attempt",
        ),
    )
    op.create_index("ix_simulation_provider_calls_session_status", "simulation_provider_calls", ["session_id", "status"])

    op.create_table(
        "simulation_evidence",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("step_id", sa.UUID(), nullable=True),
        sa.Column("evidence_type", sa.String(64), nullable=False),
        sa.Column("source_uid", sa.String(255), nullable=False),
        sa.Column("source_revision", sa.String(64), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("validation_state", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["simulation_sessions.session_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["step_id"], ["simulation_steps.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_simulation_evidence_session_step", "simulation_evidence", ["session_id", "step_id"])
    op.create_index("ix_simulation_evidence_source", "simulation_evidence", ["source_uid", "source_revision"])

    op.create_table(
        "simulation_checkpoints",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("step_key", sa.String(64), nullable=True),
        sa.Column("state_hash", sa.String(64), nullable=False),
        sa.Column("state", sa.JSON(), nullable=False),
        sa.Column("object_key", sa.String(1024), nullable=True),
        sa.Column("object_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["simulation_sessions.session_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "sequence", name="uq_simulation_checkpoint_sequence"),
    )
    op.create_index("ix_simulation_checkpoints_session_created", "simulation_checkpoints", ["session_id", "created_at"])

    op.create_table(
        "simulation_artifacts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("artifact_type", sa.String(64), nullable=False),
        sa.Column("schema_version", sa.String(64), nullable=False),
        sa.Column("revision", sa.String(64), nullable=False),
        sa.Column("object_key", sa.String(1024), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("state", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["simulation_sessions.session_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "artifact_type", "revision", name="uq_simulation_artifact_revision"),
    )
    op.create_index("ix_simulation_artifacts_session_state", "simulation_artifacts", ["session_id", "state"])


def downgrade():
    op.drop_index("ix_simulation_artifacts_session_state", table_name="simulation_artifacts")
    op.drop_table("simulation_artifacts")
    op.drop_index("ix_simulation_checkpoints_session_created", table_name="simulation_checkpoints")
    op.drop_table("simulation_checkpoints")
    op.drop_index("ix_simulation_evidence_source", table_name="simulation_evidence")
    op.drop_index("ix_simulation_evidence_session_step", table_name="simulation_evidence")
    op.drop_table("simulation_evidence")
    op.drop_index("ix_simulation_provider_calls_session_status", table_name="simulation_provider_calls")
    op.drop_table("simulation_provider_calls")
    op.drop_index("ix_simulation_events_session_created", table_name="simulation_events")
    op.drop_table("simulation_events")
    op.drop_index("ix_simulation_steps_session_sequence", table_name="simulation_steps")
    op.drop_index("ix_simulation_steps_session_status", table_name="simulation_steps")
    op.drop_table("simulation_steps")

    with op.batch_alter_table("simulation_sessions") as batch:
        for column in (
            "artifact_state",
            "cancellation_requested_at",
            "pause_requested_at",
            "last_error_message",
            "last_error_code",
            "trace_id",
            "revision",
            "checkpoint_sequence",
            "tool_call_count",
            "provider_call_count",
            "budget",
            "plan",
            "seed",
            "scenario_revision",
            "engine_version",
            "engine_id",
            "contract_version",
        ):
            batch.drop_column(column)
