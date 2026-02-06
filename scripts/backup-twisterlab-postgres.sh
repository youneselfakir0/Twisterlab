#!/bin/bash
set -e

BACKUP_DIR="/var/backups/twisterlab/postgres"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
RETENTION_DAYS=7

echo "[$(date)] Starting PostgreSQL backup..."

# Backup using postgres user
kubectl exec -n twisterlab postgres-0 -- sh -c 'PGPASSWORD=$POSTGRES_PASSWORD pg_dumpall -U postgres' | gzip > "$BACKUP_DIR/postgres_$DATE.sql.gz"

if [ -f "$BACKUP_DIR/postgres_$DATE.sql.gz" ]; then
    SIZE=$(du -h "$BACKUP_DIR/postgres_$DATE.sql.gz" | cut -f1)
    echo "[$(date)] Backup successful: postgres_$DATE.sql.gz ($SIZE)"
else
    echo "[$(date)] ERROR: Backup failed!" >&2
    exit 1
fi

# Cleanup old backups
find "$BACKUP_DIR" -name "postgres_*.sql.gz" -mtime +$RETENTION_DAYS -delete
echo "[$(date)] Old backups cleaned (retention: $RETENTION_DAYS days)"

# Log to syslog
logger -t twisterlab-backup "PostgreSQL backup completed: $SIZE"
