"""Add tracing tables

Revision ID: b0d09ef7daef
Revises: 000000000001
Create Date: 2026-01-08 14:12:49.884355

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b0d09ef7daef"
down_revision = "000000000001"
branch_labels = None
depends_on = None


def _json_type(bind):
    if bind.dialect.name == "postgresql":
        return postgresql.JSONB(astext_type=sa.Text())
    return sa.JSON()


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
    json_type = _json_type(bind)

    if not _table_exists(inspector, "trace_runs"):
        op.create_table(
            "trace_runs",
            sa.Column("run_id", sa.UUID(), nullable=False),
            sa.Column("session_id", sa.UUID(), nullable=True),
            sa.Column("tenant_id", sa.String(length=100), nullable=True),
            sa.Column("workspace_id", sa.String(length=100), nullable=True),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("model_name", sa.String(length=100), nullable=True),
            sa.Column("model_version", sa.String(length=50), nullable=True),
            sa.Column("policy_pack_id", sa.String(length=100), nullable=True),
            sa.Column("policy_pack_version", sa.String(length=50), nullable=True),
            sa.Column("data_snapshot", json_type, nullable=True),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column("entropy", sa.Float(), nullable=True),
            sa.Column("bias_risk", sa.Float(), nullable=True),
            sa.Column("input_message", sa.Text(), nullable=True),
            sa.Column("final_answer", sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("run_id"),
        )
        inspector = inspect(bind)

    if not _table_exists(inspector, "trace_axis_vectors"):
        op.create_table(
            "trace_axis_vectors",
            sa.Column("vector_id", sa.UUID(), nullable=False),
            sa.Column("run_id", sa.UUID(), nullable=False),
            sa.Column("axes", json_type, nullable=False),
            sa.Column("coordinate_hash", sa.String(length=100), nullable=True),
            sa.ForeignKeyConstraint(["run_id"], ["trace_runs.run_id"]),
            sa.PrimaryKeyConstraint("vector_id"),
            sa.UniqueConstraint("run_id"),
        )
        inspector = inspect(bind)

    if not _table_exists(inspector, "trace_claims"):
        op.create_table(
            "trace_claims",
            sa.Column("claim_id", sa.UUID(), nullable=False),
            sa.Column("run_id", sa.UUID(), nullable=False),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("answer_span_start", sa.Integer(), nullable=True),
            sa.Column("answer_span_end", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=True),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column("evidence_ids", json_type, nullable=True),
            sa.Column("stage_ids", json_type, nullable=True),
            sa.ForeignKeyConstraint(["run_id"], ["trace_runs.run_id"]),
            sa.PrimaryKeyConstraint("claim_id"),
        )
        inspector = inspect(bind)

    if not _table_exists(inspector, "trace_evidence"):
        op.create_table(
            "trace_evidence",
            sa.Column("evidence_id", sa.UUID(), nullable=False),
            sa.Column("run_id", sa.UUID(), nullable=False),
            sa.Column("source_type", sa.String(length=50), nullable=True),
            sa.Column("source_id", sa.String(length=255), nullable=True),
            sa.Column("source_title", sa.String(length=500), nullable=True),
            sa.Column("authority", sa.String(length=20), nullable=True),
            sa.Column("locator", json_type, nullable=True),
            sa.Column("snippet", sa.Text(), nullable=True),
            sa.Column("content_hash", sa.String(length=100), nullable=True),
            sa.Column("retrieval_method", sa.String(length=50), nullable=True),
            sa.Column("relevance_score", sa.Float(), nullable=True),
            sa.Column("axis_match_score", sa.Float(), nullable=True),
            sa.Column("used_by_claims", json_type, nullable=True),
            sa.Column("used_by_personas", json_type, nullable=True),
            sa.Column("used_by_stages", json_type, nullable=True),
            sa.Column("conflicts_with", json_type, nullable=True),
            sa.ForeignKeyConstraint(["run_id"], ["trace_runs.run_id"]),
            sa.PrimaryKeyConstraint("evidence_id"),
        )
        inspector = inspect(bind)

    if not _table_exists(inspector, "trace_personas"):
        op.create_table(
            "trace_personas",
            sa.Column("persona_id", sa.UUID(), nullable=False),
            sa.Column("run_id", sa.UUID(), nullable=False),
            sa.Column("persona_type", sa.String(length=50), nullable=False),
            sa.Column("persona_name", sa.String(length=100), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=True),
            sa.Column("evidence_ids", json_type, nullable=True),
            sa.Column("context_scope", sa.Text(), nullable=True),
            sa.Column("draft_text", sa.Text(), nullable=True),
            sa.Column("confidence", sa.Float(), nullable=True),
            sa.Column("objections", json_type, nullable=True),
            sa.Column("consensus_impact", json_type, nullable=True),
            sa.ForeignKeyConstraint(["run_id"], ["trace_runs.run_id"]),
            sa.PrimaryKeyConstraint("persona_id"),
        )
        inspector = inspect(bind)

    if not _table_exists(inspector, "trace_stages"):
        op.create_table(
            "trace_stages",
            sa.Column("stage_id", sa.UUID(), nullable=False),
            sa.Column("run_id", sa.UUID(), nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("stage_type", sa.String(length=20), nullable=True),
            sa.Column("layer_index", sa.Integer(), nullable=True),
            sa.Column("step_index", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=True),
            sa.Column("start_time", sa.DateTime(), nullable=True),
            sa.Column("end_time", sa.DateTime(), nullable=True),
            sa.Column("duration_ms", sa.Integer(), nullable=True),
            sa.Column("inputs", json_type, nullable=True),
            sa.Column("outputs", json_type, nullable=True),
            sa.Column("decisions", json_type, nullable=True),
            sa.Column("metrics", json_type, nullable=True),
            sa.ForeignKeyConstraint(["run_id"], ["trace_runs.run_id"]),
            sa.PrimaryKeyConstraint("stage_id"),
        )
        inspector = inspect(bind)

    if not _table_exists(inspector, "trace_artifacts"):
        op.create_table(
            "trace_artifacts",
            sa.Column("artifact_id", sa.UUID(), nullable=False),
            sa.Column("run_id", sa.UUID(), nullable=False),
            sa.Column("stage_id", sa.UUID(), nullable=True),
            sa.Column("artifact_type", sa.String(length=50), nullable=True),
            sa.Column("label", sa.String(length=200), nullable=True),
            sa.Column("content", json_type, nullable=True),
            sa.Column("content_ref", sa.String(length=500), nullable=True),
            sa.Column("content_hash", sa.String(length=100), nullable=True),
            sa.Column("redactions", json_type, nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["run_id"], ["trace_runs.run_id"]),
            sa.ForeignKeyConstraint(["stage_id"], ["trace_stages.stage_id"]),
            sa.PrimaryKeyConstraint("artifact_id"),
        )
        inspector = inspect(bind)

    if not _table_exists(inspector, "trace_ka_invocations"):
        op.create_table(
            "trace_ka_invocations",
            sa.Column("invocation_id", sa.UUID(), nullable=False),
            sa.Column("run_id", sa.UUID(), nullable=False),
            sa.Column("stage_id", sa.UUID(), nullable=True),
            sa.Column("ka_id", sa.String(length=100), nullable=False),
            sa.Column("ka_name", sa.String(length=200), nullable=True),
            sa.Column("ka_version", sa.String(length=50), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=True),
            sa.Column("duration_ms", sa.Integer(), nullable=True),
            sa.Column("inputs", json_type, nullable=True),
            sa.Column("outputs", json_type, nullable=True),
            sa.Column("routing", json_type, nullable=True),
            sa.Column("side_effects", json_type, nullable=True),
            sa.ForeignKeyConstraint(["run_id"], ["trace_runs.run_id"]),
            sa.ForeignKeyConstraint(["stage_id"], ["trace_stages.stage_id"]),
            sa.PrimaryKeyConstraint("invocation_id"),
        )
        inspector = inspect(bind)

    if not _table_exists(inspector, "trace_memory_events"):
        op.create_table(
            "trace_memory_events",
            sa.Column("event_id", sa.UUID(), nullable=False),
            sa.Column("run_id", sa.UUID(), nullable=False),
            sa.Column("stage_id", sa.UUID(), nullable=True),
            sa.Column("event_type", sa.String(length=50), nullable=False),
            sa.Column("target", sa.String(length=20), nullable=True),
            sa.Column("items", json_type, nullable=True),
            sa.Column("gating", json_type, nullable=True),
            sa.Column("timestamp", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["run_id"], ["trace_runs.run_id"]),
            sa.ForeignKeyConstraint(["stage_id"], ["trace_stages.stage_id"]),
            sa.PrimaryKeyConstraint("event_id"),
        )
        inspector = inspect(bind)

    if not _table_exists(inspector, "trace_policy_decisions"):
        op.create_table(
            "trace_policy_decisions",
            sa.Column("decision_id", sa.UUID(), nullable=False),
            sa.Column("run_id", sa.UUID(), nullable=False),
            sa.Column("stage_id", sa.UUID(), nullable=True),
            sa.Column("policy_rule_id", sa.String(length=100), nullable=True),
            sa.Column("decision_type", sa.String(length=20), nullable=False),
            sa.Column("reason", sa.Text(), nullable=True),
            sa.Column("affected", json_type, nullable=True),
            sa.Column("actor", sa.String(length=50), nullable=True),
            sa.Column("timestamp", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["run_id"], ["trace_runs.run_id"]),
            sa.ForeignKeyConstraint(["stage_id"], ["trace_stages.stage_id"]),
            sa.PrimaryKeyConstraint("decision_id"),
        )
        inspector = inspect(bind)

    if _table_exists(inspector, "kg_edges"):
        edge_type_idx = "ix_kg_edges_edge_type"
        source_idx = "ix_kg_edges_source_id"
        target_idx = "ix_kg_edges_target_id"
        with op.batch_alter_table("kg_edges", schema=None) as batch_op:
            if not _index_exists(inspector, "kg_edges", edge_type_idx):
                batch_op.create_index(edge_type_idx, ["edge_type"], unique=False)
            if not _index_exists(inspector, "kg_edges", source_idx):
                batch_op.create_index(source_idx, ["source_id"], unique=False)
            if not _index_exists(inspector, "kg_edges", target_idx):
                batch_op.create_index(target_idx, ["target_id"], unique=False)

    if _table_exists(inspector, "kg_nodes"):
        axis_idx = "ix_kg_nodes_axis_number"
        node_type_idx = "ix_kg_nodes_node_type"
        with op.batch_alter_table("kg_nodes", schema=None) as batch_op:
            if not _index_exists(inspector, "kg_nodes", axis_idx):
                batch_op.create_index(axis_idx, ["axis_number"], unique=False)
            if not _index_exists(inspector, "kg_nodes", node_type_idx):
                batch_op.create_index(node_type_idx, ["node_type"], unique=False)


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    if _table_exists(inspector, "kg_nodes"):
        axis_idx = "ix_kg_nodes_axis_number"
        node_type_idx = "ix_kg_nodes_node_type"
        with op.batch_alter_table("kg_nodes", schema=None) as batch_op:
            if _index_exists(inspector, "kg_nodes", node_type_idx):
                batch_op.drop_index(node_type_idx)
            if _index_exists(inspector, "kg_nodes", axis_idx):
                batch_op.drop_index(axis_idx)

    if _table_exists(inspector, "kg_edges"):
        edge_type_idx = "ix_kg_edges_edge_type"
        source_idx = "ix_kg_edges_source_id"
        target_idx = "ix_kg_edges_target_id"
        with op.batch_alter_table("kg_edges", schema=None) as batch_op:
            if _index_exists(inspector, "kg_edges", target_idx):
                batch_op.drop_index(target_idx)
            if _index_exists(inspector, "kg_edges", source_idx):
                batch_op.drop_index(source_idx)
            if _index_exists(inspector, "kg_edges", edge_type_idx):
                batch_op.drop_index(edge_type_idx)

    tables = [
        "trace_policy_decisions",
        "trace_memory_events",
        "trace_ka_invocations",
        "trace_artifacts",
        "trace_stages",
        "trace_personas",
        "trace_evidence",
        "trace_claims",
        "trace_axis_vectors",
        "trace_runs",
    ]
    for table_name in tables:
        if _table_exists(inspector, table_name):
            op.drop_table(table_name)
            inspector = inspect(bind)
