#!/bin/bash

# Henry's SmartStock AI - Vercel Frontend + Backend Deployment Script
# Usage: ./deploy-vercel.sh [environment]

set -e

ENVIRONMENT=${1:-production}

echo "🚀 Starting Vercel + Backend deployment for Henry's SmartStock AI"

# Check if Vercel CLI is installed
if ! command -v vercel > /dev/null 2>&1; then
    echo "📦 Installing Vercel CLI..."
    npm install -g vercel
fi

# Check if required files exist
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found for backend. Please copy .env.production to .env and configure it."
    exit 1
fi

echo "📋 Pre-deployment checks..."

# Check if Docker is running (for backend)
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker for backend deployment."
    exit 1
fi

echo "✅ Pre-deployment checks passed"

echo "🏗️  Step 1: Deploying Backend Services..."

# Deploy backend services (database, cache, API)
echo "🗄️  Starting backend services..."
docker-compose -f docker-compose.prod.yml up -d postgres redis backend

# Wait for backend to be healthy
echo "⏳ Waiting for backend services to be healthy..."
sleep 30

# Check backend health
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    exit 1
fi

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

echo "🌐 Step 2: Deploying Frontend to Vercel..."

# Navigate to frontend directory
cd frontend

# Set up environment variables for Vercel (if not already set)
echo "⚙️  Configuring Vercel environment variables..."

# Check if this is the first deployment
if [ ! -f ".vercel/project.json" ]; then
    echo "🆕 First time deployment - running Vercel setup..."
    
    # Run the setup script
    ../vercel-setup.sh
else
    echo "ℹ️  Vercel project already configured"
fi

# Use Vercel-optimized configurations if available
if [ -f "package.json.vercel" ]; then
    echo "📦 Using Vercel-optimized package.json..."
    cp package.json.vercel package.json
fi

if [ -f "vite.config.vercel.ts" ]; then
    echo "⚙️  Using Vercel-optimized Vite config..."
    cp vite.config.vercel.ts vite.config.ts
fi

# Install dependencies and build
echo "📦 Installing dependencies..."
npm ci

echo "🏗️  Testing build..."
npm run build

# Deploy to Vercel
echo "🚀 Deploying frontend to Vercel..."
if [ "$ENVIRONMENT" = "production" ]; then
    vercel --prod --yes
else
    vercel --yes
fi

# Get deployment URL
DEPLOYMENT_URL=$(vercel ls | grep "henrys-smartstock" | head -1 | awk '{print $2}')

# Update CORS settings
echo "🔧 Updating backend CORS settings..."
cd ..
./update-cors.sh

echo "🎉 Deployment completed successfully!"
echo ""
echo "📱 Application URLs:"
echo "   Frontend (Vercel): https://$DEPLOYMENT_URL"
echo "   Backend API: http://localhost:8000"
echo "   API Documentation: http://localhost:8000/docs"
echo ""
echo "🔐 Default Admin Credentials:"
echo "   Email: admin@henrysonmarket.com"
echo "   Password: admin123"
echo "   ⚠️  Please change the default password immediately!"
echo ""
echo "📝 Next Steps:"
echo "   1. Update CORS settings in backend to include Vercel domain"
echo "   2. Set up custom domain in Vercel (optional)"
echo "   3. Configure SSL certificate (automatic with Vercel)"
echo "   4. Update environment variables with production URLs"
echo "   5. Test the full application flow"
echo ""
echo "🔧 Backend Management:"
echo "   View logs: docker-compose -f docker-compose.prod.yml logs -f backend"
echo "   Stop backend: docker-compose -f docker-compose.prod.yml down"
echo "   Backup database: ./backup.sh"
echo ""
echo "🌐 Vercel Management:"
echo "   View deployments: vercel ls"
echo "   View logs: vercel logs"
echo "   Manage domains: vercel domains"