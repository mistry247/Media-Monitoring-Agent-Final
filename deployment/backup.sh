#!/bin/bash

# Media Monitoring Agent Backup Script
# This script creates backups of the database and configuration files

set -e

# Configuration
APP_DIR="/opt/media-monitoring-agent"
BACKUP_DIR="/var/backups/media-monitoring"
RETENTION_DAYS=30

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/media_monitoring_backup_$TIMESTAMP.tar.gz"

log_info "Starting backup process..."

# Create backup
cd "$APP_DIR"
tar -czf "$BACKUP_FILE" \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='logs/*.log' \
    .

if [ $? -eq 0 ]; then
    log_info "Backup created successfully: $BACKUP_FILE"
    
    # Set appropriate permissions
    chmod 600 "$BACKUP_FILE"
    
    # Show backup size
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log_info "Backup size: $BACKUP_SIZE"
else
    log_error "Backup creation failed"
    exit 1
fi

# Clean up old backups
log_info "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "media_monitoring_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

# List current backups
log_info "Current backups:"
ls -lh "$BACKUP_DIR"/media_monitoring_backup_*.tar.gz 2>/dev/null || log_warn "No backups found"

log_info "Backup process completed successfully"