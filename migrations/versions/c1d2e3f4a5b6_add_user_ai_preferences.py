"""Add user_ai_preferences table

Revision ID: c1d2e3f4a5b6
Revises: b0d09ef7daef
Create Date: 2026-05-12 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

revision = "c1d2e3f4a5b6"
down_revision = "b0d09ef7daef"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_ai_preferences",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("preferred_provider", sa.String(64), nullable=True),
        sa.Column("preferred_model", sa.String(128), nullable=True),
        sa.Column("ai_processing_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("store_chat_history", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_user_ai_preferences_user_id"),
    )
    op.create_index("ix_user_ai_preferences_user_id", "user_ai_preferences", ["user_id"])


def downgrade():
    op.drop_index("ix_user_ai_preferences_user_id", table_name="user_ai_preferences")
    op.drop_table("user_ai_preferences")
