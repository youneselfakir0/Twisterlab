# TwisterLab Maintenance Scripts

## Overview

This directory contains automated maintenance scripts for the TwisterLab production environment. These scripts provide comprehensive backup, restore, monitoring, and validation capabilities to ensure system reliability and data safety.

## Scripts Overview

### 1. `backup.ps1` - Automated Backup Script

Creates comprehensive backups of the TwisterLab system including database, volumes, and configuration files.

**Features:**
- Database dumps (PostgreSQL)
- Volume backups (PostgreSQL data, Redis data)
- Configuration file backups
- Compression support
- Automatic cleanup of old backups

**Usage:**

```powershell
# Quick database backup
.\backup.ps1

# Full system backup with compression
.\backup.ps1 -Full -Compress

# Custom retention period
.\backup.ps1 -Full -Compress -RetentionDays 14
```

**Parameters:**
- `-Full`: Include volumes and configuration (default: database only)
- `-Compress`: Compress backup files
- `-RetentionDays`: Days to keep backups (default: 7)

### 2. `restore.ps1` - Automated Restore Script

Restores TwisterLab system from backup files with safety checks and validation.

**Features:**
- Selective restore (database, volumes, or configuration)
- Dry-run mode for testing
- Automatic service management during restore
- Compressed backup support

**Usage:**

```powershell
# Restore specific backup
.\restore.ps1 -BackupName "twisterlab_backup_20251115_143022"

# Dry run to test restore
.\restore.ps1 -BackupName "twisterlab_backup_20251115_143022" -DryRun

# Restore only database
.\restore.ps1 -BackupName "twisterlab_backup_20251115_143022" -DatabaseOnly
```

**Parameters:**
- `-BackupName`: Name of backup to restore (required)
- `-DatabaseOnly`: Restore only database
- `-VolumesOnly`: Restore only volumes
- `-ConfigOnly`: Restore only configuration
- `-DryRun`: Test restore without making changes

### 3. `monitor.ps1` - System Monitoring Script

Monitors system health, services, and performance with automated alerts and rollback capabilities.

**Features:**
- Service health checks
- API endpoint monitoring
- Database connectivity tests
- Resource usage monitoring
- Automated alerts and notifications
- Rollback triggers for critical failures

**Usage:**

```powershell
# Run monitoring check
.\monitor.ps1
```

### 4. `validate.ps1` - System Validation Script

Comprehensive system validation testing all components and generating detailed health reports.

**Features:**
- Docker service validation
- API endpoint testing
- Database connectivity checks
- Monitoring stack verification
- SSL configuration testing
- System resource monitoring
- JSON report generation

**Usage:**

```powershell
# Standard validation
.\validate.ps1

# Quick validation (skip agent tests)
.\validate.ps1 -Quick

# Full validation with all tests
.\validate.ps1 -Full

# Silent mode (no console output)
.\validate.ps1 -Silent
```

**Parameters:**
- `-Quick`: Skip time-consuming tests
- `-Full`: Run all available tests
- `-Silent`: Suppress console output
- `-Timeout`: Request timeout in seconds (default: 30)
- `-ReportPath`: Custom report directory

### 5. `maintenance.ps1` - Maintenance Orchestrator

Master script that coordinates all maintenance operations and provides comprehensive system management.

**Features:**
- Unified interface for all maintenance operations
- Automated maintenance workflows
- Pre/post operation validation
- Comprehensive reporting
- Error handling and rollback

**Usage:**

```powershell
# Create system backup
.\maintenance.ps1 -Action backup -Full -Compress

# Restore from backup
.\maintenance.ps1 -Action restore -BackupName "twisterlab_backup_20251115_143022"

# Run system validation
.\maintenance.ps1 -Action validate -Full

# Check system monitoring
.\maintenance.ps1 -Action monitor

# Run full maintenance cycle
.\maintenance.ps1 -Action maintenance

# Complete system health check
.\maintenance.ps1 -Action full-check
```

**Actions:**
- `backup`: Create system backup
- `restore`: Restore from backup
- `validate`: Run system validation
- `monitor`: Check system monitoring
- `maintenance`: Full maintenance cycle
- `full-check`: Complete system health assessment

## Directory Structure

```
infrastructure/scripts/
├── backup.ps1          # Backup operations
├── restore.ps1         # Restore operations
├── monitor.ps1         # Monitoring and alerts
├── validate.ps1        # System validation
├── maintenance.ps1     # Master orchestrator
└── README.md          # This documentation
```

## Backup Storage

**Default Locations:**
- Backups: `%USERPROFILE%\TwisterLab_Backups\`
- Validation Reports: `%USERPROFILE%\TwisterLab_Validation_Reports\`
- Maintenance Logs: `%USERPROFILE%\TwisterLab_Maintenance_Reports\`

**Backup Contents:**
- Database dumps (SQL format)
- Docker volumes (tar.gz archives)
- Configuration files
- Compressed archives (when `-Compress` used)

## Automated Maintenance Workflows

### Daily Maintenance

```powershell
# Run daily system check
.\maintenance.ps1 -Action full-check

# Create daily backup
.\maintenance.ps1 -Action backup -Compress
```

### Weekly Maintenance

```powershell
# Full system maintenance
.\maintenance.ps1 -Action maintenance

# Extended retention for weekly backups
.\maintenance.ps1 -Action backup -Full -Compress -RetentionDays 30
```

### Emergency Recovery

```powershell
# Validate system status
.\maintenance.ps1 -Action validate -Full

# Test restore procedure
.\maintenance.ps1 -Action restore -BackupName "backup_name" -DryRun

# Perform actual restore
.\maintenance.ps1 -Action restore -BackupName "backup_name"
```

## Monitoring and Alerts

The monitoring system provides:
- Real-time service health checks
- Resource usage alerts (CPU, memory, disk)
- API endpoint monitoring
- Database connectivity validation
- Automated rollback triggers
- Email/SMS notifications (configurable)

## Error Handling

All scripts include comprehensive error handling:
- Detailed logging to timestamped files
- Graceful failure recovery
- Service rollback on critical errors
- JSON reports for all operations

## Retention Worker & Backup Agent Management

The `RealBackupAgent` includes a background retention worker to automatically remove expired backups using a configurable retention policy. The worker can be controlled via env vars and API endpoints.

Environment variables:
- `TWISTERLAB_START_RETENTION` (bool): if true, the `RealBackupAgent` retention worker is started at agent/orchestrator initialization.
- `TWISTERLAB_RETENTION_INTERVAL` (int seconds): interval in seconds between retention runs (default: 3600).

Management API endpoints (admin-only):
- `GET /api/v1/autonomous/agents/{agent_name}/management/status`: returns agent status plus `retention_running` flag and manifest count.
- `POST /api/v1/autonomous/agents/{agent_name}/management/retention/start`: payload {"interval_seconds": 3600} to start worker.
- `POST /api/v1/autonomous/agents/{agent_name}/management/retention/stop`: stop the worker gracefully.
- `POST /api/v1/autonomous/agents/{agent_name}/management/retention/apply`: trigger a one-off retention application.
- `GET /api/v1/autonomous/agents/{agent_name}/management/backups`: list existing backups.
- `POST /api/v1/autonomous/agents/{agent_name}/management/backups/verify`: payload {"backup_id": "..."} to verify backup integrity.
- `POST /api/v1/autonomous/agents/{agent_name}/management/backups/restore`: payload {"backup_id": "..."} to restore a backup.

Prometheus metrics to monitor retention operations:
- `backup_retention_runs_total`: number of retention worker runs.
- `backup_retention_removed_total`: total number of backups removed by retention.

Example curl command to start the retention worker (admin user):

```powershell
curl -X POST \
  http://localhost:8000/api/v1/autonomous/agents/RealBackupAgent/management/retention/start \
  -H "Content-Type: application/json" \
  -d '{"interval_seconds": 3600}'
```

- Exit codes for automation integration

## Security Considerations

- Backups contain sensitive data (encrypt if needed)
- Scripts require appropriate Docker permissions
- Database credentials accessed via environment variables
- No hardcoded secrets in scripts
- Audit logging for all operations

## Integration with CI/CD

These scripts can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: System Validation
  run: |
    .\infrastructure\scripts\maintenance.ps1 -Action validate -Full

- name: Create Backup
  run: |
    .\infrastructure\scripts\maintenance.ps1 -Action backup -Full -Compress
```

## Troubleshooting

### Common Issues

**Backup fails with permission errors:**
- Ensure Docker daemon is running
- Check user permissions for backup directory
- Verify database credentials in environment

**Restore fails with connection errors:**
- Ensure services are running before restore
- Check database container accessibility
- Verify backup file integrity

**Validation reports timeouts:**
- Increase timeout parameter: `-Timeout 60`
- Check network connectivity to services
- Verify services are responding

### Log Files

All operations generate detailed logs:
- `backup.log`: Backup operation details
- `restore.log`: Restore operation details
- `maintenance_*.log`: Orchestrator operations

### Support

For issues with maintenance scripts:
1. Check log files in the reports directory
2. Run validation: `.\validate.ps1 -Full`
3. Review system status: `.\maintenance.ps1 -Action full-check`
4. Check Docker services: `docker service ls`

## Version History

- **v1.0.0** (2025-11-15): Initial release with all core maintenance scripts
  - Automated backup and restore
  - System monitoring and validation
  - Maintenance orchestration
  - Comprehensive error handling and reporting
