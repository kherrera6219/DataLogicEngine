import importlib
from datetime import datetime

import pytest
from flask import Flask
from sqlalchemy import text

from extensions import db
from utils import db_migration


@pytest.fixture
def flask_app(tmp_path):
    app = Flask(__name__)
    db_path = tmp_path / "test.db"
    app.config.update(
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_path}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    db.init_app(app)

    with app.app_context():
        db.create_all()
    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture(autouse=True)
def reload_db_migration():
    yield
    importlib.reload(db_migration)


def test_run_migrations_creates_history(flask_app):
    assert db_migration.run_migrations(flask_app) is True

    with flask_app.app_context():
        rows = db.session.execute(text("SELECT version, description FROM migrations"))
        persisted = rows.fetchall()

    assert len(persisted) == 1
    assert persisted[0][1] == "Initial schema creation or update"


def test_record_migration_is_idempotent(flask_app):
    db_migration.run_migrations(flask_app)

    with flask_app.app_context():
        before_second_record, *_ = db.session.execute(
            text("SELECT COUNT(*) FROM migrations")
        ).fetchone()

    db_migration.record_migration(flask_app)
    with flask_app.app_context():
        after_second_record, *_ = db.session.execute(
            text("SELECT COUNT(*) FROM migrations")
        ).fetchone()

    assert after_second_record == before_second_record + 1


def test_check_database_connection_reports_health(flask_app):
    assert db_migration.check_database_connection(flask_app) is True


def test_get_migration_history_returns_latest_first(flask_app):
    db_migration.run_migrations(flask_app)

    with flask_app.app_context():
        version = datetime.now().strftime("%Y%m%d%H%M%S")
        db.session.execute(
            text(
                """
                INSERT INTO migrations (version, description, executed_at)
                VALUES (:version, :description, :executed_at)
                """
            ),
            {
                "version": version,
                "description": "Manual migration",
                "executed_at": datetime(2099, 1, 1),
            },
        )
        db.session.commit()

    history = db_migration.get_migration_history(flask_app)

    assert history[0]["version"] == version
    assert history[1]["description"] == "Initial schema creation or update"
