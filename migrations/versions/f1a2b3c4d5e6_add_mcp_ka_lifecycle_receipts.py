"""Add canonical KA lifecycle and effect receipt evidence to MCP executions.

Revision ID: f1a2b3c4d5e6
Revises: e0f1a2b3c4d5
"""

import sqlalchemy as sa
from alembic import op

revision = "f1a2b3c4d5e6"
down_revision = "e0f1a2b3c4d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "mcp_execution_records",
        sa.Column("ka_lifecycle", sa.JSON(), nullable=True),
    )
    op.add_column(
        "mcp_execution_records",
        sa.Column("effect_receipt", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("mcp_execution_records", "effect_receipt")
    op.drop_column("mcp_execution_records", "ka_lifecycle")
