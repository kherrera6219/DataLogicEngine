"""Generate a frozen Alembic initial schema from the current SQLAlchemy metadata.

This is a maintainer tool, not a startup path. Its output is reviewed and
committed as an immutable revision so production never depends on runtime
``db.create_all()`` or on whatever models happen to exist in a future build.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import textwrap

from alembic.autogenerate import produce_migrations, render_python_code
from alembic.migration import MigrationContext
from sqlalchemy import create_engine

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import models  # noqa: E402


DEFAULT_OUTPUT = ROOT / "migrations/versions/000000000001_initial_production_schema.py"


def generate() -> str:
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as connection:
        context = MigrationContext.configure(connection)
        migration = produce_migrations(context, models.db.metadata)
    upgrade = render_python_code(migration.upgrade_ops)
    downgrade = render_python_code(migration.downgrade_ops)
    return f'''"""Frozen initial production schema

Revision ID: 000000000001
Revises:
Create Date: 2026-07-13

Generated once from the reviewed Phase 4 SQLAlchemy metadata. Do not regenerate
this revision after release; add a new forward migration instead.
"""

from alembic import op
import sqlalchemy as sa


revision = "000000000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
{_indent_body(upgrade)}


def downgrade():
{_indent_body(downgrade)}
'''


def _indent_body(rendered: str) -> str:
    lines = textwrap.dedent(rendered).strip().splitlines()
    if not lines:
        return "    pass"
    return "\n".join(f"    {line}" if line else "" for line in lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(generate(), encoding="utf-8", newline="\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
