# ruff: noqa: E402
"""Unambiguously-importable shared test helpers.

These functions live in a regular module (not in a ``conftest.py``) so test
modules can import them by a stable, collision-free name:

    from tests._helpers import authenticate_client_session, drop_all_test_tables

Importing them via ``from conftest import ...`` is unreliable: every test
directory's ``conftest.py`` is loaded under the same top-level module name
``conftest`` on ``sys.path``, so the import resolves to whichever ``conftest``
was imported first (e.g. ``tests/unit/conftest.py``, which does not define these
helpers) and raises ``ImportError`` when ``tests/unit`` and ``tests/compliance``
are collected together. See the A18 test-isolation audit.

The repository root is placed on ``sys.path`` by the root ``tests/conftest.py``
(which pytest always loads before any test module), so ``tests._helpers``
resolves regardless of collection order. The root ``tests/conftest.py``
re-exports these names for backward compatibility.
"""

from extensions import db


def drop_all_test_tables() -> None:
    """Drop test tables while tolerating SQLite foreign-key cycles."""
    db.session.remove()
    if db.engine.dialect.name == "sqlite":
        with db.engine.connect() as connection:
            connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
            db.metadata.drop_all(bind=connection)
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        return

    db.drop_all()


def authenticate_client_session(client, user_id):
    """Mark a Flask test client as logged in via Flask-Login session keys."""
    with client.session_transaction() as session:
        session["_user_id"] = str(user_id)
        session["_fresh"] = True
    return client
