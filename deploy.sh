#!/bin/bash

# Henry's SmartStock AI - Production Deployment Script
# Usage: ./deploy.sh [environment]
# Example: ./deploy.sh production

set -e  # Exit on any error

ENVIRONMENT=${1:-production}
COMPOSE_FILE="docker-compose.prod.yml"

echo "🚀 Starting deployment for Henry's SmartStock AI - $ENVIRONMENT environment"

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

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f $COMPOSE_FILE down --remove-orphans

# Pull latest images
echo "📥 Pulling latest images..."
docker-compose -f $COMPOSE_FILE pull

# Build and start services
echo "🏗️  Building and starting services..."
docker-compose -f $COMPOSE_FILE up -d --build

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 30

# Check service health
echo "🏥 Checking service health..."

# Check database
if docker-compose -f $COMPOSE_FILE exec -T postgres pg_isready -U ${POSTGRES_USER:-henrys_user} -d ${POSTGRES_DB:-henrys_smartstock}; then
    echo "✅ Database is healthy"
else
    echo "❌ Database health check failed"
    exit 1
fi

# Check Redis
if docker-compose -f $COMPOSE_FILE exec -T redis redis-cli ping; then
    echo "✅ Redis is healthy"
else
    echo "❌ Redis health check failed"
    exit 1
fi

# Check backend
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    exit 1
fi

# Check frontend
if curl -f http://localhost:80/health > /dev/null 2>&1; then
    echo "✅ Frontend is healthy"
else
    echo "❌ Frontend health check failed"
    exit 1
fi

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose -f $COMPOSE_FILE exec backend alembic upgrade head

# Create initial admin user (if needed)
echo "👤 Creating initial admin user..."
docker-compose -f $COMPOSE_FILE exec backend python -c "
from app.core.database import get_db
from app.models.user import User
from app.core.security import get_password_hash
from sqlalchemy.orm import Session
import os

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
"

# Show deployment status
echo "📊 Deployment Status:"
docker-compose -f $COMPOSE_FILE ps

echo "🎉 Deployment completed successfully!"
echo ""
echo "📱 Application URLs:"
echo "   Frontend: http://localhost:80"
echo "   Backend API: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"
echo ""
echo "🔐 Default Admin Credentials:"
echo "   Email: admin@henrysonmarket.com"
echo "   Password: admin123"
echo "   ⚠️  Please change the default password immediately!"
echo ""
echo "📝 Next Steps:"
echo "   1. Change the default admin password"
echo "   2. Configure SSL certificates for HTTPS"
echo "   3. Set up domain name and DNS"
echo "   4. Configure backup schedule"
echo "   5. Set up monitoring and alerts"
echo ""
echo "📚 View logs: docker-compose -f $COMPOSE_FILE logs -f [service_name]"
echo "🛑 Stop services: docker-compose -f $COMPOSE_FILE down"