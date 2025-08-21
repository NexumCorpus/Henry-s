#!/bin/bash

# Henry's SmartStock AI - Complete Docker Compose Deployment
# This script deploys frontend + backend + database all together using Docker Compose

set -e

ENVIRONMENT=${1:-production}
COMPOSE_FILE="docker-compose.complete.yml"

echo "🐳 Starting complete Docker Compose deployment for Henry's SmartStock AI"
echo "📋 Environment: $ENVIRONMENT"

# Check if required files exist
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found. Please copy .env.production to .env and configure it."
    exit 1
fi

if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ Error: $COMPOSE_FILE not found."
    exit 1
fi

# Load environment variables
source .env

echo "📋 Pre-deployment checks..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    echo "❌ Error: docker-compose is not installed."
    exit 1
fi

echo "✅ Pre-deployment checks passed"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs/nginx
mkdir -p nginx/ssl
mkdir -p backups
mkdir -p data/postgres
mkdir -p data/redis
mkdir -p scripts

echo "🛑 Stopping existing containers..."
docker-compose -f $COMPOSE_FILE down --remove-orphans

echo "📥 Pulling latest images..."
docker-compose -f $COMPOSE_FILE pull

echo "🏗️  Building and starting all services..."
docker-compose -f $COMPOSE_FILE up -d --build

echo "⏳ Waiting for services to be healthy..."
echo "   This may take 2-3 minutes for all services to start..."

# Wait for database to be ready
echo "🗄️  Waiting for database..."
timeout=120
counter=0
while ! docker-compose -f $COMPOSE_FILE exec -T postgres pg_isready -U ${POSTGRES_USER:-henrys_user} -d ${POSTGRES_DB:-henrys_smartstock} > /dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        echo "❌ Database failed to start within $timeout seconds"
        exit 1
    fi
    sleep 2
    counter=$((counter + 2))
    echo -n "."
done
echo " ✅ Database is ready"

# Wait for Redis
echo "📦 Waiting for Redis..."
timeout=60
counter=0
while ! docker-compose -f $COMPOSE_FILE exec -T redis redis-cli ping > /dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        echo "❌ Redis failed to start within $timeout seconds"
        exit 1
    fi
    sleep 2
    counter=$((counter + 2))
    echo -n "."
done
echo " ✅ Redis is ready"

# Wait for backend
echo "🔧 Waiting for backend..."
timeout=120
counter=0
while ! curl -f http://localhost:8000/health > /dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        echo "❌ Backend failed to start within $timeout seconds"
        exit 1
    fi
    sleep 2
    counter=$((counter + 2))
    echo -n "."
done
echo " ✅ Backend is ready"

# Wait for frontend
echo "🌐 Waiting for frontend..."
timeout=60
counter=0
while ! curl -f http://localhost:3000/health > /dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        echo "❌ Frontend failed to start within $timeout seconds"
        exit 1
    fi
    sleep 2
    counter=$((counter + 2))
    echo -n "."
done
echo " ✅ Frontend is ready"

# Wait for Nginx
echo "🔀 Waiting for Nginx reverse proxy..."
timeout=60
counter=0
while ! curl -f http://localhost:80/health > /dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        echo "❌ Nginx failed to start within $timeout seconds"
        exit 1
    fi
    sleep 2
    counter=$((counter + 2))
    echo -n "."
done
echo " ✅ Nginx is ready"

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose -f $COMPOSE_FILE exec backend alembic upgrade head

# Create initial admin user
echo "👤 Creating initial admin user..."
docker-compose -f $COMPOSE_FILE exec backend python -c "
import os
import sys
sys.path.append('/app')

try:
    from app.core.database import get_db
    from app.models.user import User
    from app.core.security import get_password_hash
    from sqlalchemy.orm import Session

    db = next(get_db())
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@henrysonmarket.com')
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')

    # Check if admin user exists
    existing_admin = db.query(User).filter(User.email == admin_email).first()
    if not existing_admin:
        admin_user = User(
            email=admin_email,
            name='System Administrator',
            hashed_password=get_password_hash(admin_password),
            role='admin',
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print(f'✅ Admin user created: {admin_email}')
    else:
        print(f'ℹ️  Admin user already exists: {admin_email}')
except Exception as e:
    print(f'⚠️  Could not create admin user: {e}')
    print('You can create it manually later through the API')
"

# Test the complete application
echo "🧪 Testing complete application..."

# Test API
if curl -f http://localhost:80/api/v1/health > /dev/null 2>&1; then
    echo "✅ API accessible through Nginx"
else
    echo "⚠️  API test failed - check configuration"
fi

# Test frontend
if curl -f http://localhost:80/ > /dev/null 2>&1; then
    echo "✅ Frontend accessible through Nginx"
else
    echo "⚠️  Frontend test failed - check configuration"
fi

# Show deployment status
echo ""
echo "📊 Deployment Status:"
docker-compose -f $COMPOSE_FILE ps

echo ""
echo "🎉 Complete Docker Compose deployment successful!"
echo ""
echo "📱 Application URLs:"
echo "   Main Application: http://localhost:80"
echo "   Direct Frontend: http://localhost:3000"
echo "   Direct Backend: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"
echo "   Database: localhost:5432"
echo "   Redis: localhost:6379"
echo ""
echo "🔐 Default Admin Credentials:"
echo "   Email: admin@henrysonmarket.com"
echo "   Password: admin123"
echo "   ⚠️  Please change the default password immediately!"
echo ""
echo "🐳 Docker Compose Management:"
echo "   View logs: docker-compose -f $COMPOSE_FILE logs -f [service]"
echo "   Stop all: docker-compose -f $COMPOSE_FILE down"
echo "   Restart service: docker-compose -f $COMPOSE_FILE restart [service]"
echo "   Scale service: docker-compose -f $COMPOSE_FILE up -d --scale backend=2"
echo ""
echo "📊 Service Status:"
echo "   All services: docker-compose -f $COMPOSE_FILE ps"
echo "   Resource usage: docker stats"
echo "   Service logs: docker-compose -f $COMPOSE_FILE logs [service]"
echo ""
echo "💾 Data Management:"
echo "   Database backup: docker-compose -f $COMPOSE_FILE exec postgres pg_dump -U henrys_user henrys_smartstock > backup.sql"
echo "   View data volumes: docker volume ls"
echo "   Backup location: ./backups/"
echo ""
echo "🔧 Troubleshooting:"
echo "   Check service health: docker-compose -f $COMPOSE_FILE ps"
echo "   View all logs: docker-compose -f $COMPOSE_FILE logs"
echo "   Restart everything: docker-compose -f $COMPOSE_FILE restart"
echo ""
echo "🎯 Next Steps:"
echo "   1. Change the default admin password"
echo "   2. Configure SSL certificates (optional)"
echo "   3. Set up domain name and DNS"
echo "   4. Configure automated backups"
echo "   5. Set up monitoring and alerts"
echo "   6. Train your staff using the Quick Start Guide"