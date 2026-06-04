"""Database migration helpers with sqlite-friendly defaults for testing."""

import logging
from datetime import datetime
from typing import List, Dict

from flask import Flask
from sqlalchemy import text

from extensions import db


def run_migrations(app: Flask) -> bool:
    """Run database migrations for the UKG system."""
    try:
        with app.app_context():
            db.create_all()
            logging.info("Database schema updated successfully")
            record_migration(app)
            return True
    except Exception as exc:  # pragma: no cover - defensive logging path
        logging.error(f"Failed to run migrations: {exc}", exc_info=True)
        return False


def record_migration(app: Flask) -> None:
    """Record that a migration has been run in a migrations table."""
    try:
        with app.app_context():
            engine_name = db.engine.dialect.name
            if engine_name == "sqlite":
                create_stmt = text(
                    """
                    CREATE TABLE IF NOT EXISTS migrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        version VARCHAR(50) NOT NULL,
                        executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        description TEXT
                    )
                    """
                )
            else:
                create_stmt = text(
                    """
                    CREATE TABLE IF NOT EXISTS migrations (
                        id SERIAL PRIMARY KEY,
                        version VARCHAR(50) NOT NULL,
                        executed_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                        description TEXT
                    )
                    """
                )

            db.session.execute(create_stmt)

            version = datetime.now().strftime("%Y%m%d%H%M%S")
            db.session.execute(
                text(
                    """
                    INSERT INTO migrations (version, description)
                    VALUES (:version, :description)
                    """
                ),
                {
                    "version": version,
                    "description": "Initial schema creation or update",
                },
            )

            db.session.commit()
            logging.info("Recorded migration with version: %s", version)
    except Exception as exc:  # pragma: no cover - defensive logging path
        db.session.rollback()
        logging.error(f"Failed to record migration: {exc}", exc_info=True)


def check_database_connection(app: Flask) -> bool:
    """Check if the database connection is working."""
    try:
        with app.app_context():
            db.session.execute(text("SELECT 1"))
            return True
    except Exception as exc:  # pragma: no cover - defensive logging path
        logging.error(f"Database connection failed: {exc}", exc_info=True)
        return False


def get_migration_history(app: Flask) -> List[Dict[str, str]]:
    """Get the history of migrations that have been applied."""
    try:
        with app.app_context():
            engine_name = db.engine.dialect.name
            if engine_name == "sqlite":
                result = db.session.execute(
                    text(
                        """
                        SELECT count(name) FROM sqlite_master
                        WHERE type='table' AND name='migrations'
                        """
                    )
                ).scalar()
                table_exists = bool(result)
            else:
                result = db.session.execute(
                    text(
                        """
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_name = 'migrations'
                        )
                        """
                    )
                ).scalar()
                table_exists = bool(result)

            if not table_exists:
                return []

            rows = db.session.execute(
                text(
                    """
                    SELECT version, executed_at, description
                    FROM migrations
                    ORDER BY executed_at DESC
                    """
                )
            )

            return [
                {
                    "version": row[0],
                    "executed_at": row[1],
                    "description": row[2],
                }
                for row in rows
            ]
    except Exception as exc:  # pragma: no cover - defensive logging path
        logging.error(f"Failed to get migration history: {exc}", exc_info=True)
        return []
