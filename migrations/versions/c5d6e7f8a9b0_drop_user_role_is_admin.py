"""Drop role/is_admin columns from users (auth-deprecation Phase E-2c)

Revision ID: c5d6e7f8a9b0
Revises: b4c5d6e7f8a9
Create Date: 2026-06-19

Removes the multi-user authorization columns (role, is_admin) and their indexes
(ix_users_role, ix_users_role_active) from the users table. Under single-mode /
OS-level auth there is one owner with full access; all authorization gates were
collapsed to a single-owner check, so these columns are inert. See
docs/audits/DataLogicEngine_Auth_Deprecation_Plan.md (Phase E).

Idempotent + reversible: guards on existence so it is safe on databases that
never had the columns (fresh SQLite created from the slimmed model).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "c5d6e7f8a9b0"
down_revision = "b4c5d6e7f8a9"
branch_labels = None
depends_on = None

# (name, type, kwargs) — type/kwargs only used by downgrade to recreate the columns.
_COLUMNS = [
    ("is_admin", sa.Boolean(), {"nullable": True, "server_default": sa.false()}),
    ("role", sa.String(length=20), {"nullable": True, "server_default": "user"}),
]
_INDEXES = [
    ("ix_users_role", ["role"]),
    ("ix_users_role_active", ["role", "active"]),
]


def _column_exists(inspector, table, col):
    return any(c["name"] == col for c in inspector.get_columns(table))


def _index_names(inspector, table):
    return {idx["name"] for idx in inspector.get_indexes(table)}


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    existing_indexes = _index_names(inspector, "users")
    for index_name, _cols in _INDEXES:
        if index_name in existing_indexes:
            op.drop_index(index_name, table_name="users")

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

    inspector = inspect(bind)
    existing_indexes = _index_names(inspector, "users")
    for index_name, cols in _INDEXES:
        if index_name not in existing_indexes:
            op.create_index(index_name, "users", cols)
