"""Add Phase 9 PostgreSQL ingestion job and corpus authorities.

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "c8d9e0f1a2b3"
down_revision = "b7c8d9e0f1a2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("tenant_id", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("source_label", sa.String(length=200), nullable=True),
        sa.Column("source_digest", sa.String(length=64), nullable=False),
        sa.Column("recursive", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("chunk_size", sa.Integer(), nullable=False),
        sa.Column("max_file_bytes", sa.Integer(), nullable=False),
        sa.Column("max_total_bytes", sa.Integer(), nullable=False),
        sa.Column("max_files", sa.Integer(), nullable=False),
        sa.Column("max_pages", sa.Integer(), nullable=False, server_default="500"),
        sa.Column("max_archive_entries", sa.Integer(), nullable=False, server_default="10000"),
        sa.Column("max_decompressed_bytes", sa.Integer(), nullable=False, server_default=str(100 * 1024 * 1024)),
        sa.Column("max_archive_depth", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("parser_timeout_seconds", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("files_scanned", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("files_ingested", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("files_rejected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chunks_created", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chunks_indexed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("materializations_pending", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cancellation_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("pause_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("current_checkpoint", sa.String(length=80), nullable=False, server_default="queued"),
        sa.Column("last_error_code", sa.String(length=120), nullable=True),
        sa.Column("last_error_message", sa.String(length=240), nullable=True),
        sa.Column("result_summary", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_ingestion_jobs_status_created",
        "ingestion_jobs",
        ["status", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_ingestion_jobs_user_created",
        "ingestion_jobs",
        ["user_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "ingestion_files",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("relative_path", sa.String(length=1000), nullable=False),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("document_uid", sa.String(length=80), nullable=True),
        sa.Column("source_revision", sa.String(length=100), nullable=True),
        sa.Column("source_sha256", sa.String(length=64), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("detected_type", sa.String(length=32), nullable=True),
        sa.Column("parser_result", sa.JSON(), nullable=True),
        sa.Column("defense_result", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="acquired"),
        sa.Column("error_code", sa.String(length=120), nullable=True),
        sa.Column("content_sha256", sa.String(length=64), nullable=True),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("object_bucket", sa.String(length=100), nullable=True),
        sa.Column("object_key", sa.String(length=500), nullable=True),
        sa.Column("object_sha256", sa.String(length=64), nullable=True),
        sa.Column("object_status", sa.String(length=24), nullable=True),
        sa.Column("normalized_object_bucket", sa.String(length=100), nullable=True),
        sa.Column("normalized_object_key", sa.String(length=500), nullable=True),
        sa.Column("normalized_object_sha256", sa.String(length=64), nullable=True),
        sa.Column("normalized_object_status", sa.String(length=24), nullable=True),
        sa.Column("embedding_revision", sa.String(length=255), nullable=True),
        sa.Column("last_retrieved_at", sa.DateTime(), nullable=True),
        sa.Column("last_retrieval_trace_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["job_id"], ["ingestion_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "relative_path", name="uq_ingestion_file_job_path"),
    )
    op.create_index(
        "ix_ingestion_files_document_status",
        "ingestion_files",
        ["document_uid", "status"],
        unique=False,
    )
    op.create_index(
        "ix_ingestion_files_job_status",
        "ingestion_files",
        ["job_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_ingestion_files_source_sha",
        "ingestion_files",
        ["source_sha256"],
        unique=False,
    )

    op.create_table(
        "ingestion_chunks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("file_id", sa.UUID(), nullable=False),
        sa.Column("node_uid", sa.String(length=80), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("chunk_sha256", sa.String(length=64), nullable=False),
        sa.Column("source_revision", sa.String(length=255), nullable=False),
        sa.Column("materialization_state", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["file_id"], ["ingestion_files.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["ingestion_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("file_id", "chunk_index", name="uq_ingestion_chunk_file_index"),
    )
    op.create_index(
        "ix_ingestion_chunks_job_materialization",
        "ingestion_chunks",
        ["job_id", "materialization_state"],
        unique=False,
    )
    op.create_index(
        "ix_ingestion_chunks_node_uid",
        "ingestion_chunks",
        ["node_uid"],
        unique=False,
    )

    op.create_table(
        "ingestion_attempts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("job_id", sa.UUID(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="running"),
        sa.Column("worker_instance_id", sa.String(length=100), nullable=True),
        sa.Column("checkpoint", sa.String(length=80), nullable=False, server_default="acquisition"),
        sa.Column("error_code", sa.String(length=120), nullable=True),
        sa.Column("error_message", sa.String(length=240), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["ingestion_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "attempt_number", name="uq_ingestion_attempt_number"),
    )
    op.create_index(
        "ix_ingestion_attempts_job_status",
        "ingestion_attempts",
        ["job_id", "status"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_ingestion_attempts_job_status", table_name="ingestion_attempts")
    op.drop_table("ingestion_attempts")
    op.drop_index("ix_ingestion_chunks_node_uid", table_name="ingestion_chunks")
    op.drop_index("ix_ingestion_chunks_job_materialization", table_name="ingestion_chunks")
    op.drop_table("ingestion_chunks")
    op.drop_index("ix_ingestion_files_source_sha", table_name="ingestion_files")
    op.drop_index("ix_ingestion_files_job_status", table_name="ingestion_files")
    op.drop_index("ix_ingestion_files_document_status", table_name="ingestion_files")
    op.drop_table("ingestion_files")
    op.drop_index("ix_ingestion_jobs_user_created", table_name="ingestion_jobs")
    op.drop_index("ix_ingestion_jobs_status_created", table_name="ingestion_jobs")
    op.drop_table("ingestion_jobs")
