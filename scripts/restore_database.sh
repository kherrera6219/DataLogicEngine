#!/bin/bash
# Database restore script for DataLogicEngine
# Supports PostgreSQL and SQLite backups created by scripts/backup_database.sh

set -e

BACKUP_FILE="$1"
TARGET_DB="$2"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$BACKUP_FILE" ]; then
    echo -e "${RED}✗ Backup file path is required${NC}"
    echo "Usage: $0 <backup_file> [target_db_path]"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}✗ Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}✗ DATABASE_URL not set${NC}"
    echo "Please set DATABASE_URL in your .env file"
    exit 1
fi

DB_TYPE=$(echo $DATABASE_URL | cut -d: -f1)

echo "========================================="
echo "DataLogicEngine Database Restore"
echo "========================================="
echo ""
echo "Backup file: $BACKUP_FILE"
echo "Database type: $DB_TYPE"
echo ""

if [[ $DB_TYPE == "postgresql" || $DB_TYPE == "postgres" ]]; then
    if ! command -v pg_restore &> /dev/null; then
        echo -e "${RED}✗ pg_restore is not installed${NC}"
        exit 1
    fi

    echo "Restoring PostgreSQL backup..."
    echo "Target: $DATABASE_URL"

    if pg_restore --clean --if-exists --no-owner --no-privileges -d "$DATABASE_URL" "$BACKUP_FILE"; then
        echo -e "${GREEN}✓ PostgreSQL restore complete${NC}"
    else
        echo -e "${RED}✗ PostgreSQL restore failed${NC}"
        exit 1
    fi

elif [[ $DB_TYPE == "sqlite" ]]; then
    DB_FILE=$(echo $DATABASE_URL | sed 's/sqlite:\/\///')
    TARGET_DB=${TARGET_DB:-$DB_FILE}

    if [ -z "$TARGET_DB" ]; then
        echo -e "${RED}✗ SQLite target database path not provided${NC}"
        exit 1
    fi

    if [ -f "$TARGET_DB" ]; then
        BACKUP_EXISTING="${TARGET_DB}.bak_$(date +%Y%m%d_%H%M%S)"
        echo -e "${YELLOW}⚠ Existing database found. Creating backup: $BACKUP_EXISTING${NC}"
        cp "$TARGET_DB" "$BACKUP_EXISTING"
    fi

    echo "Restoring SQLite backup..."
    if [[ $BACKUP_FILE == *.gz ]]; then
        gunzip -c "$BACKUP_FILE" > "$TARGET_DB"
    else
        cp "$BACKUP_FILE" "$TARGET_DB"
    fi

    if [ -f "$TARGET_DB" ]; then
        echo -e "${GREEN}✓ SQLite restore complete${NC}"
    else
        echo -e "${RED}✗ SQLite restore failed${NC}"
        exit 1
    fi

else
    echo -e "${RED}✗ Unsupported database type: $DB_TYPE${NC}"
    exit 1
fi

echo ""
echo "========================================="
echo -e "${GREEN}✓ Restore finished successfully${NC}"
echo "========================================="
