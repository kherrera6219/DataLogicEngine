"""Drop MFA columns from users (auth-deprecation Phase E)

Revision ID: b4c5d6e7f8a9
Revises: a4b5c6d7e8f9
Create Date: 2026-06-19

Removes the per-user MFA fields (mfa_enabled, mfa_secret, backup_codes) from the
users table. MFA is obsolete under the single-mode / OS-level auth architecture
(the backend.security.mfa module and User.verify_totp were already removed). See
docs/audits/DataLogicEngine_Auth_Deprecation_Plan.md (Phase E).

Idempotent + reversible: guards on column existence so it is safe on databases
that never had the columns (fresh local SQLite created from the slimmed model).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "b4c5d6e7f8a9"
down_revision = "a4b5c6d7e8f9"
branch_labels = None
depends_on = None

# (name, type, kwargs) — type/kwargs only used by downgrade to recreate the columns.
_COLUMNS = [
    ("mfa_enabled", sa.Boolean(), {"nullable": True, "server_default": sa.false()}),
    ("mfa_secret", sa.String(length=255), {"nullable": True}),
    ("backup_codes", sa.JSON(), {"nullable": True}),
]


def _column_exists(inspector, table, col):
    return any(c["name"] == col for c in inspector.get_columns(table))


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    with op.batch_alter_table("users") as batch_op:
        for col_name, _type, _kwargs in _COLUMNS:
            if _column_exists(inspector, "users", col_name):
                batch_op.drop_column(col_name)


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)
    with op.batch_alter_table("users") as batch_op:
        for col_name, col_type, kwargs in reversed(_COLUMNS):
            if not _column_exists(inspector, "users", col_name):
                batch_op.add_column(sa.Column(col_name, col_type, **kwargs))
