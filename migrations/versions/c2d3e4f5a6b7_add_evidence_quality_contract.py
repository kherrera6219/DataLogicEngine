"""Add typed evidence quality, citation, validator, and decision storage.

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-07-13
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "c2d3e4f5a6b7"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def _json_type():
    if op.get_bind().dialect.name == "postgresql":
        return postgresql.JSONB(astext_type=sa.Text())
    return sa.JSON()


def upgrade():
    json_type = _json_type()
    with op.batch_alter_table("trace_evidence") as batch_op:
        batch_op.add_column(sa.Column("origin", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("author_publisher", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("captured_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("effective_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("retrieved_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("permissions", json_type, nullable=True))
        batch_op.add_column(sa.Column("transformation_chain", json_type, nullable=True))
        batch_op.add_column(sa.Column("embedding_revision", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("quality_score", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("freshness_score", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("provenance_completeness", sa.Float(), nullable=True))

    with op.batch_alter_table("trace_claims") as batch_op:
        batch_op.add_column(sa.Column("claim_type", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("citation_ids", json_type, nullable=True))

    with op.batch_alter_table("claim_evidence_links") as batch_op:
        batch_op.alter_column(
            "confidence",
            existing_type=sa.Float(),
            existing_nullable=True,
            server_default=None,
        )
        batch_op.add_column(
            sa.Column("relationship", sa.String(length=32), nullable=False, server_default="insufficient")
        )
        batch_op.add_column(sa.Column("validator_id", sa.String(length=100), nullable=True))

    op.create_table(
        "trace_citations",
        sa.Column("citation_id", sa.String(length=100), nullable=False),
        sa.Column("run_id", sa.UUID(), nullable=False),
        sa.Column("claim_id", sa.UUID(), nullable=True),
        sa.Column("evidence_id", sa.UUID(), nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=False),
        sa.Column("label", sa.String(length=32), nullable=False),
        sa.Column("answer_span_start", sa.Integer(), nullable=True),
        sa.Column("answer_span_end", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["trace_runs.run_id"]),
        sa.ForeignKeyConstraint(["claim_id"], ["trace_claims.claim_id"]),
        sa.ForeignKeyConstraint(["evidence_id"], ["trace_evidence.evidence_id"]),
        sa.PrimaryKeyConstraint("citation_id"),
    )
    op.create_index("ix_trace_citations_run_id", "trace_citations", ["run_id"])

    op.create_table(
        "trace_validators",
        sa.Column("validator_id", sa.String(length=100), nullable=False),
        sa.Column("run_id", sa.UUID(), nullable=False),
        sa.Column("claim_id", sa.UUID(), nullable=True),
        sa.Column("validator_type", sa.String(length=64), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("inputs", json_type, nullable=True),
        sa.Column("outputs", json_type, nullable=True),
        sa.Column("missing_inputs", json_type, nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["trace_runs.run_id"]),
        sa.ForeignKeyConstraint(["claim_id"], ["trace_claims.claim_id"]),
        sa.PrimaryKeyConstraint("validator_id"),
    )
    op.create_index("ix_trace_validators_run_id", "trace_validators", ["run_id"])

    op.create_table(
        "trace_quality_decisions",
        sa.Column("decision_id", sa.UUID(), nullable=False),
        sa.Column("run_id", sa.UUID(), nullable=False),
        sa.Column("decision_type", sa.String(length=32), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("components", json_type, nullable=True),
        sa.Column("missing_inputs", json_type, nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("iteration", sa.Integer(), nullable=True),
        sa.Column("terminal", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["trace_runs.run_id"]),
        sa.PrimaryKeyConstraint("decision_id"),
    )
    op.create_index("ix_trace_quality_decisions_run_id", "trace_quality_decisions", ["run_id"])


def downgrade():
    op.drop_index("ix_trace_quality_decisions_run_id", table_name="trace_quality_decisions")
    op.drop_table("trace_quality_decisions")
    op.drop_index("ix_trace_validators_run_id", table_name="trace_validators")
    op.drop_table("trace_validators")
    op.drop_index("ix_trace_citations_run_id", table_name="trace_citations")
    op.drop_table("trace_citations")

    with op.batch_alter_table("claim_evidence_links") as batch_op:
        batch_op.drop_column("validator_id")
        batch_op.drop_column("relationship")
    with op.batch_alter_table("trace_claims") as batch_op:
        batch_op.drop_column("citation_ids")
        batch_op.drop_column("claim_type")
    with op.batch_alter_table("trace_evidence") as batch_op:
        for column in (
            "provenance_completeness",
            "freshness_score",
            "quality_score",
            "embedding_revision",
            "transformation_chain",
            "permissions",
            "retrieved_at",
            "effective_at",
            "captured_at",
            "author_publisher",
            "origin",
        ):
            batch_op.drop_column(column)
