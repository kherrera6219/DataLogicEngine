#!/bin/bash
# Verify or install cron job for automated backups

set -e

CRON_SCHEDULE_DEFAULT="0 2 * * *"
BACKUP_SCRIPT_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/backup_database.sh"
INSTALL=false
CUSTOM_SCHEDULE=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --install)
            INSTALL=true
            shift
            ;;
        --schedule)
            CUSTOM_SCHEDULE="$2"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1"
            exit 1
            ;;
    esac
done

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

SCHEDULE=${CUSTOM_SCHEDULE:-${BACKUP_CRON_SCHEDULE:-$CRON_SCHEDULE_DEFAULT}}

if ! command -v crontab &> /dev/null; then
    echo "crontab command not available. Please install cron on this system."
    exit 1
fi

CRON_ENTRY="$SCHEDULE $BACKUP_SCRIPT_PATH >> ./logs/backup_cron.log 2>&1"

if crontab -l 2>/dev/null | rg -n "backup_database\.sh" > /dev/null; then
    echo "✓ Backup cron job detected:"
    crontab -l | rg -n "backup_database\.sh"
    exit 0
fi

if [ "$INSTALL" = true ]; then
    echo "Installing backup cron job:"
    echo "$CRON_ENTRY"
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    echo "✓ Cron job installed"
    exit 0
fi

echo "⚠ No backup cron job found."
echo "To install automatically, run:"
echo "  ./scripts/verify_backup_cron.sh --install"
echo ""
echo "Or add this entry to your crontab:"
echo "  $CRON_ENTRY"
