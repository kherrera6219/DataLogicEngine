#!/usr/bin/env python
"""
Database Migration Runner for DataLogicEngine
Runs database migrations without requiring Flask CLI

Usage:
    python run_migration.py upgrade    # Apply pending migrations
    python run_migration.py downgrade  # Rollback last migration
    python run_migration.py current    # Show current migration version
    python run_migration.py history    # Show migration history
"""

import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db


def show_banner():
    """Display migration banner"""
    print("=" * 70)
    print("DataLogicEngine - Database Migration Runner")
    print("=" * 70)
    print(f"Environment: {os.environ.get('FLASK_ENV', 'production')}")
    print(f"Database: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured')}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 70)
    print()


def run_upgrade():
    """Apply pending database migrations"""
    print("🔄 Applying database migrations...")
    print()

    try:
        from flask_migrate import upgrade, current

        with app.app_context():
            # Show current version before upgrade
            print("Current migration version:")
            current()
            print()

            # Run upgrade
            print("Running upgrade...")
            upgrade()
            print()

            # Show new version
            print("Migration version after upgrade:")
            current()
            print()

            print("✅ Migration completed successfully!")
            print()
            print("Next steps:")
            print("1. Verify schema changes: python -c 'from app import db; print(db.metadata.tables.keys())'")
            print("2. Test application: python main.py")
            print("3. Check logs for any errors")
            print()

    except Exception as e:
        print(f"❌ Migration failed: {str(e)}", file=sys.stderr)
        print()
        print("Troubleshooting steps:")
        print("1. Check database connection")
        print("2. Verify migrations directory exists")
        print("3. Ensure database user has necessary permissions")
        print("4. Review docs/MIGRATION_GUIDE.md for detailed help")
        print()
        sys.exit(1)


def run_downgrade():
    """Rollback last database migration"""
    print("⚠️  Rolling back database migration...")
    print()

    # Confirm in production
    if os.environ.get('FLASK_ENV') == 'production':
        print("WARNING: You are about to rollback a migration in PRODUCTION!")
        print("This will remove database changes and may cause data loss.")
        print()
        response = input("Type 'ROLLBACK' to confirm: ")
        if response != 'ROLLBACK':
            print("❌ Rollback cancelled")
            sys.exit(0)

    try:
        from flask_migrate import downgrade, current

        with app.app_context():
            # Show current version before downgrade
            print("Current migration version:")
            current()
            print()

            # Run downgrade
            print("Running downgrade...")
            downgrade()
            print()

            # Show new version
            print("Migration version after downgrade:")
            current()
            print()

            print("✅ Rollback completed successfully!")
            print()
            print("Next steps:")
            print("1. Verify schema changes reverted")
            print("2. Deploy previous application version if needed")
            print("3. Test application: python main.py")
            print()

    except Exception as e:
        print(f"❌ Rollback failed: {str(e)}", file=sys.stderr)
        print()
        print("Emergency recovery:")
        print("1. Restore from database backup")
        print("2. Review docs/MIGRATION_GUIDE.md for detailed rollback procedures")
        print()
        sys.exit(1)


def show_current():
    """Display current migration version"""
    print("📍 Current migration version:")
    print()

    try:
        from flask_migrate import current

        with app.app_context():
            current()
            print()

    except Exception as e:
        print(f"❌ Failed to get current version: {str(e)}", file=sys.stderr)
        sys.exit(1)


def show_history():
    """Display migration history"""
    print("📜 Migration history:")
    print()

    try:
        from flask_migrate import history

        with app.app_context():
            history()
            print()

    except Exception as e:
        print(f"❌ Failed to get migration history: {str(e)}", file=sys.stderr)
        sys.exit(1)


def show_sql():
    """Show SQL that would be executed (dry run)"""
    print("🔍 Migration SQL (dry run):")
    print()

    try:
        from flask_migrate import upgrade

        with app.app_context():
            # This would normally require alembic command line
            print("For SQL preview, use: flask db upgrade --sql")
            print("Or check: migrations/versions/001_phase1_security_hardening.py")
            print()

    except Exception as e:
        print(f"❌ Failed to generate SQL: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point"""
    show_banner()

    if len(sys.argv) < 2:
        print("Usage: python run_migration.py [upgrade|downgrade|current|history]")
        print()
        print("Commands:")
        print("  upgrade    - Apply pending migrations")
        print("  downgrade  - Rollback last migration")
        print("  current    - Show current migration version")
        print("  history    - Show migration history")
        print()
        print("Examples:")
        print("  python run_migration.py upgrade")
        print("  python run_migration.py current")
        print()
        print("For detailed documentation, see: docs/MIGRATION_GUIDE.md")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == 'upgrade':
        run_upgrade()
    elif command == 'downgrade':
        run_downgrade()
    elif command == 'current':
        show_current()
    elif command == 'history':
        show_history()
    elif command == 'sql':
        show_sql()
    else:
        print(f"❌ Unknown command: {command}")
        print("Valid commands: upgrade, downgrade, current, history")
        sys.exit(1)


if __name__ == '__main__':
    main()
