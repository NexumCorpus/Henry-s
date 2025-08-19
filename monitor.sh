#!/bin/bash

# Henry's SmartStock AI - Monitoring Script
# Usage: ./monitor.sh

COMPOSE_FILE="docker-compose.prod.yml"
LOG_FILE="./logs/monitor.log"

# Create logs directory if it doesn't exist
mkdir -p ./logs

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

# Function to check service health
check_service() {
    local service=$1
    local url=$2
    
    if curl -f -s --max-time 10 "$url" > /dev/null; then
        log "✅ $service is healthy"
        return 0
    else
        log "❌ $service is unhealthy"
        return 1
    fi
}

# Function to check container status
check_container() {
    local container=$1
    
    if docker-compose -f $COMPOSE_FILE ps $container | grep -q "Up"; then
        log "✅ Container $container is running"
        return 0
    else
        log "❌ Container $container is not running"
        return 1
    fi
}

# Function to check disk space
check_disk_space() {
    local threshold=80
    local usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ $usage -lt $threshold ]; then
        log "✅ Disk usage: ${usage}% (OK)"
        return 0
    else
        log "⚠️  Disk usage: ${usage}% (WARNING: Above ${threshold}%)"
        return 1
    fi
}

# Function to check memory usage
check_memory() {
    local threshold=80
    local usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    
    if [ $usage -lt $threshold ]; then
        log "✅ Memory usage: ${usage}% (OK)"
        return 0
    else
        log "⚠️  Memory usage: ${usage}% (WARNING: Above ${threshold}%)"
        return 1
    fi
}

log "🔍 Starting health check..."

# Check containers
check_container "postgres"
check_container "redis" 
check_container "backend"
check_container "frontend"

# Check services
check_service "Frontend" "http://localhost:80/health"
check_service "Backend API" "http://localhost:8000/health"
check_service "Backend Docs" "http://localhost:8000/docs"

# Check system resources
check_disk_space
check_memory

# Check database connectivity
log "🗄️  Checking database connectivity..."
if docker-compose -f $COMPOSE_FILE exec -T postgres pg_isready -U henrys_user -d henrys_smartstock > /dev/null 2>&1; then
    log "✅ Database connectivity OK"
else
    log "❌ Database connectivity failed"
fi

# Check Redis connectivity
log "📦 Checking Redis connectivity..."
if docker-compose -f $COMPOSE_FILE exec -T redis redis-cli ping > /dev/null 2>&1; then
    log "✅ Redis connectivity OK"
else
    log "❌ Redis connectivity failed"
fi

# Show recent logs for any failed services
log "📋 Recent application logs:"
docker-compose -f $COMPOSE_FILE logs --tail=5 backend

log "🏁 Health check completed"

# Optional: Send alert if any checks failed
# You can integrate with email, Slack, or other notification systems here