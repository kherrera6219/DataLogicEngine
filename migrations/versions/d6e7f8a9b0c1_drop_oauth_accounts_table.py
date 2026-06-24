"""Drop the oauth_accounts table (ORPH-4)

Revision ID: d6e7f8a9b0c1
Revises: c5d6e7f8a9b0
Create Date: 2026-06-24

Removes the oauth_accounts table backing the OAuthAccount ORM model. The model's
only consumer (backend/mcp_server/oauth_manager.py — connector OAuth token
lifecycle) was removed in ORPH-3 as part of the single-mode / OS-level auth
pivot, leaving the model and table orphaned (referenced only by model-surface
tests). See docs/audits/DataLogicEngine_Complete_Audit_Plan_v2.md (ORPH-4).

Idempotent + reversible: guards on table existence so it is safe on databases
that never had the table (fresh SQLite created from the slimmed model), and the
downgrade recreates the table with its original schema.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "d6e7f8a9b0c1"
down_revision = "c5d6e7f8a9b0"
branch_labels = None
depends_on = None

_TABLE = "oauth_accounts"


def _table_exists(inspector, table):
    return table in inspector.get_table_names()


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    if _table_exists(inspector, _TABLE):
        op.drop_table(_TABLE)


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    if not _table_exists(inspector, _TABLE):
        op.create_table(
            _TABLE,
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "user_id",
                sa.Integer(),
                sa.ForeignKey("users.id"),
                nullable=False,
                index=True,
            ),
            sa.Column("provider", sa.String(length=50), nullable=False),
            sa.Column("provider_user_id", sa.String(length=255), nullable=False),
            sa.Column("token", sa.JSON()),
            sa.Column("refresh_token", sa.String(length=512)),
            sa.Column("token_expires_at", sa.DateTime()),
            sa.Column("created_at", sa.DateTime()),
            sa.Column("updated_at", sa.DateTime()),
            sa.UniqueConstraint(
                "provider", "provider_user_id", name="uq_provider_user"
            ),
        )
