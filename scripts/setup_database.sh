#!/bin/bash
# Database setup and migration script for DataLogicEngine
# Handles initial setup, migrations, and verification

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================="
echo "DataLogicEngine Database Setup"
echo "========================================="
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}✗ DATABASE_URL not set${NC}"
    echo "Please set DATABASE_URL in your .env file"
    echo "Example: DATABASE_URL=postgresql://user:password@localhost:5432/ukg_db"
    exit 1
fi

echo -e "${GREEN}✓ DATABASE_URL configured${NC}"
echo ""

# Parse DATABASE_URL to extract components
DB_TYPE=$(echo $DATABASE_URL | cut -d: -f1)

if [[ $DB_TYPE == "postgresql" || $DB_TYPE == "postgres" ]]; then
    echo "Database Type: PostgreSQL"
    echo ""

    # Extract database name
    DB_NAME=$(echo $DATABASE_URL | sed 's/.*\/\([^?]*\).*/\1/')

    # Check if PostgreSQL is accessible
    echo "Testing PostgreSQL connection..."
    if command -v psql &> /dev/null; then
        if psql "$DATABASE_URL" -c "SELECT 1" &> /dev/null; then
            echo -e "${GREEN}✓ PostgreSQL connection successful${NC}"
        else
            echo -e "${RED}✗ Cannot connect to PostgreSQL${NC}"
            echo "Please verify:"
            echo "  1. PostgreSQL is running"
            echo "  2. DATABASE_URL is correct"
            echo "  3. Database user has proper permissions"
            exit 1
        fi
    else
        echo -e "${YELLOW}⚠ psql command not found, skipping connection test${NC}"
    fi
elif [[ $DB_TYPE == "sqlite" ]]; then
    echo "Database Type: SQLite"
    echo -e "${YELLOW}⚠ SQLite is not recommended for production${NC}"
else
    echo "Database Type: $DB_TYPE"
fi

echo ""
echo "========================================="
echo "Database Migration"
echo "========================================="
echo ""

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Check if Flask-Migrate is available
if ! python -c "import flask_migrate" 2>/dev/null; then
    echo -e "${YELLOW}⚠ Flask-Migrate not found, installing...${NC}"
    pip install flask-migrate
fi

# Check if migrations directory exists
if [ ! -d "migrations" ]; then
    echo "Initializing Alembic migrations..."
    flask db init
    echo -e "${GREEN}✓ Migrations directory created${NC}"
else
    echo -e "${GREEN}✓ Migrations directory exists${NC}"
fi

echo ""

# Check current database revision
echo "Checking current database revision..."
CURRENT_REV=$(flask db current 2>&1 || echo "none")

if [[ $CURRENT_REV == *"none"* ]] || [[ $CURRENT_REV == *"empty"* ]]; then
    echo -e "${YELLOW}⚠ No migrations applied yet${NC}"

    # Check if there are any migration files
    if [ -d "migrations/versions" ] && [ "$(ls -A migrations/versions)" ]; then
        echo "Found existing migration files"
    else
        echo "Creating initial migration..."
        flask db migrate -m "Initial production schema - 40+ tables"
        echo -e "${GREEN}✓ Initial migration created${NC}"
    fi

    echo ""
    echo "Applying migrations..."
    flask db upgrade
    echo -e "${GREEN}✓ Database schema created${NC}"
else
    echo "Current revision: $CURRENT_REV"
    echo ""
    echo "Checking for pending migrations..."

    # Try to upgrade
    if flask db upgrade; then
        echo -e "${GREEN}✓ Database is up to date${NC}"
    else
        echo -e "${RED}✗ Migration failed${NC}"
        exit 1
    fi
fi

echo ""
echo "========================================="
echo "Database Verification"
echo "========================================="
echo ""

# Verify database tables exist
echo "Verifying database schema..."

python << 'PYEOF'
import sys
from extensions import db
from app import app

with app.app_context():
    try:
        # Check if we can query the database
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        if not tables:
            print("\033[91m✗ No tables found in database\033[0m")
            sys.exit(1)

        print(f"\033[92m✓ Found {len(tables)} tables\033[0m")

        # Check for critical tables
        critical_tables = [
            'users', 'api_keys', 'ukg_nodes', 'ukg_edges',
            'trace_runs', 'trace_stages', 'llm_providers'
        ]

        missing_tables = [t for t in critical_tables if t not in tables]

        if missing_tables:
            print(f"\033[93m⚠ Missing critical tables: {', '.join(missing_tables)}\033[0m")
        else:
            print(f"\033[92m✓ All critical tables present\033[0m")

    except Exception as e:
        print(f"\033[91m✗ Database verification failed: {e}\033[0m")
        sys.exit(1)
PYEOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database verification passed${NC}"
else
    echo -e "${RED}✗ Database verification failed${NC}"
    exit 1
fi

echo ""
echo "========================================="
echo "Seed Data (Optional)"
echo "========================================="
echo ""

read -p "Do you want to seed the database with initial data? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "backend/seed_data.py" ]; then
        echo "Running seed script..."
        python backend/seed_data.py
        echo -e "${GREEN}✓ Database seeded${NC}"
    else
        echo -e "${YELLOW}⚠ Seed script not found at backend/seed_data.py${NC}"
    fi
fi

echo ""
echo "========================================="
echo -e "${GREEN}✓ Database setup complete!${NC}"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Review migration files in migrations/versions/"
echo "  2. Set up automated backups: ./scripts/backup_database.sh"
echo "  3. Test the application: python main.py"
echo ""
