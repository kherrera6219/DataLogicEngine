#!/bin/bash
# PostgreSQL Backup Script for DataLogicEngine
# Run via cron: 0 2 * * * /path/to/backup_database.sh

set -e

# Configuration
BACKUP_DIR="${BACKUP_DIR:-/var/backups/datalogicengine}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DB_NAME="${PGDATABASE:-ukg_database}"
DB_HOST="${PGHOST:-localhost}"
DB_USER="${PGUSER:-postgres}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.sql.gz"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

log "Starting backup of database: $DB_NAME"

# Perform backup
if pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" | gzip > "$BACKUP_FILE"; then
    log "Backup created: $BACKUP_FILE"
    log "Backup size: $(du -h "$BACKUP_FILE" | cut -f1)"
else
    error "Backup failed!"
    exit 1
fi

# Verify backup
if gzip -t "$BACKUP_FILE"; then
    log "Backup integrity verified"
else
    error "Backup file is corrupted!"
    exit 1
fi

# Calculate checksum
CHECKSUM=$(sha256sum "$BACKUP_FILE" | cut -d' ' -f1)
echo "$CHECKSUM  $BACKUP_FILE" > "${BACKUP_FILE}.sha256"
log "Checksum saved: ${BACKUP_FILE}.sha256"

# Cleanup old backups
log "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.sha256" -type f -mtime +$RETENTION_DAYS -delete

# List current backups
log "Current backups:"
ls -lh "$BACKUP_DIR"/*.sql.gz 2>/dev/null || log "No backups found"

log "Backup completed successfully!"

# Optional: Upload to cloud storage
# Uncomment and configure for your cloud provider

# AWS S3
# aws s3 cp "$BACKUP_FILE" "s3://your-bucket/backups/"
# aws s3 cp "${BACKUP_FILE}.sha256" "s3://your-bucket/backups/"

# Azure Blob Storage
# az storage blob upload --container-name backups --file "$BACKUP_FILE" --name "$(basename $BACKUP_FILE)"

# Google Cloud Storage
# gsutil cp "$BACKUP_FILE" "gs://your-bucket/backups/"
