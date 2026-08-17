"""Advance stored provider records to the current supported model defaults.

Revision ID: b2c3d4e5f6a7
Revises: 0a1b2c3d4e5f
"""

import sqlalchemy as sa
from alembic import op


revision = "b2c3d4e5f6a7"
down_revision = "0a1b2c3d4e5f"
branch_labels = None
depends_on = None


def _replace_model(old_model: str, new_model: str, provider_type: str) -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "UPDATE llm_providers "
            "SET model_id = :new_model "
            "WHERE lower(provider_type) = :provider_type AND model_id = :old_model"
        ),
        {
            "new_model": new_model,
            "provider_type": provider_type,
            "old_model": old_model,
        },
    )
    bind.execute(
        sa.text(
            "UPDATE user_ai_preferences "
            "SET preferred_model = :new_model "
            "WHERE lower(preferred_provider) = :provider_type "
            "AND preferred_model = :old_model"
        ),
        {
            "new_model": new_model,
            "provider_type": provider_type,
            "old_model": old_model,
        },
    )


def upgrade() -> None:
    _replace_model("gpt-5.5", "gpt-5.6-sol", "openai")
    _replace_model("gemini-3.1-pro-preview", "gemini-3.7-flash", "google")


def downgrade() -> None:
    _replace_model("gpt-5.6-sol", "gpt-5.5", "openai")
    _replace_model("gemini-3.7-flash", "gemini-3.1-pro-preview", "google")
