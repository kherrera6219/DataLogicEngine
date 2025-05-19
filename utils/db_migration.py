import logging
import os
from datetime import datetime
from flask import Flask
from models import db

def run_migrations(app):
    """
    Run database migrations for the UKG system.
    This function is called on application startup to ensure the database schema is up to date.
    
    Args:
        app (Flask): The Flask application instance
        
    Returns:
        bool: True if migrations succeeded, False otherwise
    """
    try:
        with app.app_context():
            # Create all tables
            db.create_all()
            logging.info("Database schema updated successfully")
            
            # Record migration
            record_migration(app)
            
            return True
    except Exception as e:
        logging.error(f"Failed to run migrations: {str(e)}", exc_info=True)
        return False

def record_migration(app):
    """
    Record that a migration has been run in a migrations table.
    
    Args:
        app (Flask): The Flask application instance
    """
    try:
        with app.app_context():
            # Execute raw SQL to create migrations table if it doesn't exist
            db.session.execute(
                """
                CREATE TABLE IF NOT EXISTS migrations (
                    id SERIAL PRIMARY KEY,
                    version VARCHAR(50) NOT NULL,
                    executed_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                    description TEXT
                )
                """
            )
            
            # Insert a record for this migration
            version = datetime.now().strftime("%Y%m%d%H%M%S")
            db.session.execute(
                """
                INSERT INTO migrations (version, description)
                VALUES (:version, :description)
                """,
                {
                    "version": version,
                    "description": "Initial schema creation or update"
                }
            )
            
            db.session.commit()
            logging.info(f"Recorded migration with version: {version}")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Failed to record migration: {str(e)}", exc_info=True)

def check_database_connection(app):
    """
    Check if the database connection is working.
    
    Args:
        app (Flask): The Flask application instance
        
    Returns:
        bool: True if connection is working, False otherwise
    """
    try:
        with app.app_context():
            # Try to execute a simple query
            db.session.execute("SELECT 1")
            return True
    except Exception as e:
        logging.error(f"Database connection failed: {str(e)}", exc_info=True)
        return False

def get_migration_history(app):
    """
    Get the history of migrations that have been applied.
    
    Args:
        app (Flask): The Flask application instance
        
    Returns:
        list: List of migration records
    """
    try:
        with app.app_context():
            # Check if migrations table exists
            result = db.session.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'migrations'
                )
                """
            ).scalar()
            
            if not result:
                return []
            
            # Get migration records
            result = db.session.execute(
                """
                SELECT version, executed_at, description
                FROM migrations
                ORDER BY executed_at DESC
                """
            )
            
            migrations = []
            for row in result:
                migrations.append({
                    "version": row[0],
                    "executed_at": row[1],
                    "description": row[2]
                })
                
            return migrations
    except Exception as e:
        logging.error(f"Failed to get migration history: {str(e)}", exc_info=True)
        return []