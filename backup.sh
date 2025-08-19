#!/bin/bash

# Henry's SmartStock AI - Backup Script
# Usage: ./backup.sh

set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
COMPOSE_FILE="docker-compose.prod.yml"

echo "💾 Starting backup process..."

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Load environment variables
if [ -f ".env" ]; then
    source .env
else
    echo "❌ Error: .env file not found"
    exit 1
fi

# Database backup
echo "🗄️  Backing up PostgreSQL database..."
docker-compose -f $COMPOSE_FILE exec -T postgres pg_dump \
    -U ${POSTGRES_USER:-henrys_user} \
    -d ${POSTGRES_DB:-henrys_smartstock} \
    --no-owner --no-privileges \
    > "$BACKUP_DIR/database_backup_$TIMESTAMP.sql"

# Redis backup
echo "📦 Backing up Redis data..."
docker-compose -f $COMPOSE_FILE exec -T redis redis-cli --rdb - > "$BACKUP_DIR/redis_backup_$TIMESTAMP.rdb"

# Application logs backup
echo "📋 Backing up application logs..."
if [ -d "logs" ]; then
    tar -czf "$BACKUP_DIR/logs_backup_$TIMESTAMP.tar.gz" logs/
fi

# Configuration backup
echo "⚙️  Backing up configuration files..."
tar -czf "$BACKUP_DIR/config_backup_$TIMESTAMP.tar.gz" \
    .env \
    docker-compose.prod.yml \
    nginx/ \
    --exclude=nginx/ssl/

# Cleanup old backups (keep last 30 days)
echo "🧹 Cleaning up old backups..."
find $BACKUP_DIR -name "*_backup_*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*_backup_*.rdb" -mtime +30 -delete
find $BACKUP_DIR -name "*_backup_*.tar.gz" -mtime +30 -delete

echo "✅ Backup completed successfully!"
echo "📁 Backup files saved to: $BACKUP_DIR"
ls -la $BACKUP_DIR/*$TIMESTAMP*