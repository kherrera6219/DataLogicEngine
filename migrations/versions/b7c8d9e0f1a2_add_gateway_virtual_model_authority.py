"""Add PostgreSQL authority for Phase 8 gateway virtual models.

Revision ID: b7c8d9e0f1a2
Revises: a6b7c8d9e0f1
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa


revision = "b7c8d9e0f1a2"
down_revision = "a6b7c8d9e0f1"
branch_labels = None
depends_on = None


_POLICY = {
    "provider_selection": "owner_default",
    "model_selection": "owner_default",
    "retrieval": "bounded",
    "validation": "required",
    "tools": "policy_controlled",
}


def upgrade():
    table = op.create_table(
        "gateway_virtual_models",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=False),
        sa.Column("mode", sa.String(length=32), nullable=False),
        sa.Column("max_provider_calls", sa.Integer(), nullable=False),
        sa.Column("provider_backed", sa.Boolean(), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("policy", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_gateway_virtual_models_active",
        "gateway_virtual_models",
        ["is_active"],
        unique=False,
    )
    op.bulk_insert(table, [
        {
            "id": "dle-standard",
            "label": "DataLogicEngine Standard",
            "mode": "standard",
            "max_provider_calls": 1,
            "provider_backed": True,
            "description": "One governed answer-model call with standard validation.",
            "policy": _POLICY,
        },
        {
            "id": "dle-enhanced",
            "label": "DataLogicEngine Enhanced",
            "mode": "enhanced",
            "max_provider_calls": 2,
            "provider_backed": True,
            "description": "One answer call plus at most one governed refinement call.",
            "policy": _POLICY,
        },
        {
            "id": "dle-local-review",
            "label": "DataLogicEngine Local Review",
            "mode": "local_review",
            "max_provider_calls": 0,
            "provider_backed": False,
            "description": "Deterministic local evidence review without a provider answer.",
            "policy": {
                "provider_selection": "none",
                "model_selection": "none",
                "retrieval": "bounded",
                "validation": "required",
                "tools": "disabled",
            },
        },
    ])


def downgrade():
    op.drop_index("ix_gateway_virtual_models_active", table_name="gateway_virtual_models")
    op.drop_table("gateway_virtual_models")
