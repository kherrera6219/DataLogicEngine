"""Add DB-O audit artifact reference fields

Revision ID: a4b5c6d7e8f9
Revises: f3a4b5c6d7e8
Create Date: 2026-05-27

Adds queryable object-store and blockchain anchor fields for TruthAuditEvent.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "a4b5c6d7e8f9"
down_revision = "f3a4b5c6d7e8"
branch_labels = None
depends_on = None

_COLUMNS = [
    ("object_store_bucket", sa.String(length=128)),
    ("object_store_key", sa.String(length=512)),
    ("merkle_root", sa.String(length=64)),
    ("blockchain_anchor_tx", sa.String(length=128)),
    ("blockchain_anchor_status", sa.String(length=32)),
]


def _column_exists(inspector, table, col):
    return any(c["name"] == col for c in inspector.get_columns(table))


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    with op.batch_alter_table("truth_audit_events") as batch_op:
        for col_name, col_type in _COLUMNS:
            if not _column_exists(inspector, "truth_audit_events", col_name):
                batch_op.add_column(sa.Column(col_name, col_type, nullable=True))

    inspector = inspect(bind)
    existing_indexes = {idx["name"] for idx in inspector.get_indexes("truth_audit_events")}
    if "ix_truth_audit_events_object_store_key" not in existing_indexes:
        op.create_index(
            "ix_truth_audit_events_object_store_key",
            "truth_audit_events",
            ["object_store_key"],
        )
    if "ix_truth_audit_events_merkle_root" not in existing_indexes:
        op.create_index(
            "ix_truth_audit_events_merkle_root",
            "truth_audit_events",
            ["merkle_root"],
        )


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_indexes = {idx["name"] for idx in inspector.get_indexes("truth_audit_events")}

    if "ix_truth_audit_events_merkle_root" in existing_indexes:
        op.drop_index("ix_truth_audit_events_merkle_root", table_name="truth_audit_events")
    if "ix_truth_audit_events_object_store_key" in existing_indexes:
        op.drop_index("ix_truth_audit_events_object_store_key", table_name="truth_audit_events")

    inspector = inspect(bind)
    with op.batch_alter_table("truth_audit_events") as batch_op:
        for col_name, _ in reversed(_COLUMNS):
            if _column_exists(inspector, "truth_audit_events", col_name):
                batch_op.drop_column(col_name)
