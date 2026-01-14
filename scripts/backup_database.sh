#!/bin/bash
# Automated database backup script for DataLogicEngine
# Supports PostgreSQL and SQLite with compression and rotation

set -e  # Exit on error

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "========================================="
echo "DataLogicEngine Database Backup"
echo "========================================="
echo ""
echo "Timestamp: $TIMESTAMP"
echo "Backup directory: $BACKUP_DIR"
echo "Retention: $RETENTION_DAYS days"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}✗ DATABASE_URL not set${NC}"
    echo "Please set DATABASE_URL in your .env file"
    exit 1
fi

# Parse database type
DB_TYPE=$(echo $DATABASE_URL | cut -d: -f1)

# Perform backup based on database type
if [[ $DB_TYPE == "postgresql" || $DB_TYPE == "postgres" ]]; then
    echo "Database Type: PostgreSQL"
    echo ""

    # Extract database components
    DB_NAME=$(echo $DATABASE_URL | sed 's/.*\/\([^?]*\).*/\1/')
    BACKUP_FILE="$BACKUP_DIR/ukg_backup_${DB_NAME}_${TIMESTAMP}.dump"

    echo "Creating PostgreSQL backup..."
    echo "Output: $BACKUP_FILE"

    # Use pg_dump with custom format (supports parallel restore and compression)
    if pg_dump -Fc "$DATABASE_URL" -f "$BACKUP_FILE"; then
        echo -e "${GREEN}✓ Backup created successfully${NC}"

        # Get file size
        SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        echo "Backup size: $SIZE"

        # Create checksum
        CHECKSUM=$(sha256sum "$BACKUP_FILE" | cut -d' ' -f1)
        echo "$CHECKSUM  $BACKUP_FILE" > "${BACKUP_FILE}.sha256"
        echo "Checksum: $CHECKSUM"

    else
        echo -e "${RED}✗ Backup failed${NC}"
        exit 1
    fi

elif [[ $DB_TYPE == "sqlite" ]]; then
    echo "Database Type: SQLite"
    echo ""

    # Extract database file path
    DB_FILE=$(echo $DATABASE_URL | sed 's/sqlite:\/\/\///')
    BACKUP_FILE="$BACKUP_DIR/ukg_backup_sqlite_${TIMESTAMP}.db"

    if [ -f "$DB_FILE" ]; then
        echo "Creating SQLite backup..."
        echo "Source: $DB_FILE"
        echo "Output: $BACKUP_FILE"

        # Use SQLite backup command for consistent backup
        sqlite3 "$DB_FILE" ".backup '$BACKUP_FILE'"

        if [ -f "$BACKUP_FILE" ]; then
            # Compress the backup
            gzip "$BACKUP_FILE"
            BACKUP_FILE="${BACKUP_FILE}.gz"

            echo -e "${GREEN}✓ Backup created successfully${NC}"

            SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
            echo "Backup size: $SIZE"

            # Create checksum
            CHECKSUM=$(sha256sum "$BACKUP_FILE" | cut -d' ' -f1)
            echo "$CHECKSUM  $BACKUP_FILE" > "${BACKUP_FILE}.sha256"
            echo "Checksum: $CHECKSUM"
        else
            echo -e "${RED}✗ Backup failed${NC}"
            exit 1
        fi
    else
        echo -e "${RED}✗ Database file not found: $DB_FILE${NC}"
        exit 1
    fi

else
    echo -e "${RED}✗ Unsupported database type: $DB_TYPE${NC}"
    exit 1
fi

echo ""
echo "========================================="
echo "Backup Rotation"
echo "========================================="
echo ""

# Remove old backups
echo "Removing backups older than $RETENTION_DAYS days..."

OLD_BACKUPS=$(find "$BACKUP_DIR" -name "ukg_backup_*" -type f -mtime +$RETENTION_DAYS)

if [ -z "$OLD_BACKUPS" ]; then
    echo "No old backups to remove"
else
    echo "$OLD_BACKUPS" | while read -r file; do
        echo "Removing: $file"
        rm -f "$file"
        rm -f "${file}.sha256"
    done
    echo -e "${GREEN}✓ Old backups removed${NC}"
fi

echo ""
echo "Current backups:"
ls -lh "$BACKUP_DIR"/ukg_backup_* 2>/dev/null | tail -5 || echo "No backups found"

echo ""
echo "========================================="
echo -e "${GREEN}✓ Backup complete!${NC}"
echo "========================================="
echo ""
echo "Backup file: $BACKUP_FILE"
echo ""
echo "To restore this backup:"
if [[ $DB_TYPE == "postgresql" || $DB_TYPE == "postgres" ]]; then
    echo "  pg_restore -d \$DATABASE_URL $BACKUP_FILE"
elif [[ $DB_TYPE == "sqlite" ]]; then
    echo "  gunzip -c $BACKUP_FILE | sqlite3 your_database.db"
fi
echo ""
echo "To verify checksum:"
echo "  sha256sum -c ${BACKUP_FILE}.sha256"
echo ""

# Optional: Upload to cloud storage
if [ ! -z "$BACKUP_S3_BUCKET" ]; then
    echo "========================================="
    echo "Cloud Upload (Optional)"
    echo "========================================="
    echo ""

    if command -v aws &> /dev/null; then
        echo "Uploading to S3: s3://$BACKUP_S3_BUCKET/"
        if aws s3 cp "$BACKUP_FILE" "s3://$BACKUP_S3_BUCKET/" && \
           aws s3 cp "${BACKUP_FILE}.sha256" "s3://$BACKUP_S3_BUCKET/"; then
            echo -e "${GREEN}✓ Uploaded to S3${NC}"
        else
            echo -e "${YELLOW}⚠ S3 upload failed${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ AWS CLI not installed, skipping S3 upload${NC}"
    fi
fi

exit 0
