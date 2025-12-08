#!/usr/bin/env python3
"""
Database management script for DataLogicEngine

Usage:
    python manage_db.py init       # Initialize migrations
    python manage_db.py migrate    # Create a new migration
    python manage_db.py upgrade    # Apply migrations
    python manage_db.py downgrade  # Rollback migrations
"""

import sys
import os

# Ensure the app is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from flask_migrate import init, migrate, upgrade, downgrade, Migrate

# Initialize Flask-Migrate
migrate_obj = Migrate(app, db)

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    with app.app_context():
        if command == 'init':
            print("Initializing migrations directory...")
            try:
                init()
                print("✓ Migrations directory initialized")
            except Exception as e:
                print(f"✗ Error: {e}")
        
        elif command == 'migrate':
            message = sys.argv[2] if len(sys.argv) > 2 else "Auto-generated migration"
            print(f"Creating migration: {message}")
            try:
                migrate(message=message)
                print("✓ Migration created")
            except Exception as e:
                print(f"✗ Error: {e}")
        
        elif command == 'upgrade':
            print("Applying migrations...")
            try:
                upgrade()
                print("✓ Migrations applied")
            except Exception as e:
                print(f"✗ Error: {e}")
        
        elif command == 'downgrade':
            print("Rolling back migrations...")
            try:
                downgrade()
                print("✓ Migration rolled back")
            except Exception as e:
                print(f"✗ Error: {e}")
        
        else:
            print(f"Unknown command: {command}")
            print(__doc__)
            sys.exit(1)

if __name__ == '__main__':
    main()
