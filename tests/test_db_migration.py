from flask import Flask

from extensions import db
from utils import db_migration


def create_test_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    return app


def test_database_connection_and_migration_history():
    app = create_test_app()

    assert db_migration.check_database_connection(app) is True

    # Running migrations should succeed and create a history entry
    assert db_migration.run_migrations(app) is True
    history = db_migration.get_migration_history(app)
    assert isinstance(history, list)
    assert history
    assert "version" in history[0]



def test_migration_history_empty_when_table_missing():
    app = create_test_app()
    history = db_migration.get_migration_history(app)
    assert history == []
