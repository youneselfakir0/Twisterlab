#!/bin/bash
set -e

BACKUP_DIR="/var/backups/twisterlab/redis"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
REDIS_POD=$(kubectl get pods -n twisterlab -l component=cache -o jsonpath='{.items[0].metadata.name}')

echo "[$(date)] Starting Redis backup from pod: $REDIS_POD"

# Save RDB
kubectl exec -n twisterlab $REDIS_POD -- redis-cli SAVE

# Copy dump.rdb
kubectl exec -n twisterlab $REDIS_POD -- cat /data/dump.rdb > "$BACKUP_DIR/redis_$DATE.rdb"

SIZE=$(du -h "$BACKUP_DIR/redis_$DATE.rdb" | cut -f1)
echo "[$(date)] Redis backup successful: $SIZE"

# Cleanup old backups
find "$BACKUP_DIR" -name "redis_*.rdb" -mtime +7 -delete
logger -t twisterlab-backup "Redis backup completed: $SIZE"
