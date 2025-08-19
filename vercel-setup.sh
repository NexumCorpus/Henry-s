#!/bin/bash

# Henry's SmartStock AI - Vercel Project Setup Script
# This script helps set up the Vercel project with all necessary configurations

set -e

echo "🌐 Setting up Henry's SmartStock AI for Vercel deployment..."

# Check if Vercel CLI is installed
if ! command -v vercel > /dev/null 2>&1; then
    echo "📦 Installing Vercel CLI..."
    npm install -g vercel
    echo "✅ Vercel CLI installed"
fi

# Navigate to frontend directory
cd frontend

echo "🔗 Linking to Vercel project..."

# Check if already linked
if [ -f ".vercel/project.json" ]; then
    echo "ℹ️  Project already linked to Vercel"
    PROJECT_ID=$(cat .vercel/project.json | grep -o '"projectId":"[^"]*' | cut -d'"' -f4)
    echo "   Project ID: $PROJECT_ID"
else
    echo "🆕 Creating new Vercel project..."
    vercel link
fi

echo "⚙️  Setting up environment variables..."

# Function to set environment variable
set_env_var() {
    local var_name=$1
    local var_description=$2
    local default_value=$3
    
    echo ""
    echo "Setting up $var_name"
    echo "Description: $var_description"
    
    if [ -n "$default_value" ]; then
        echo "Suggested value: $default_value"
    fi
    
    # Check if variable already exists
    if vercel env ls | grep -q "$var_name"; then
        echo "✅ $var_name already configured"
    else
        echo "📝 Please enter the value for $var_name:"
        vercel env add "$var_name" production
        echo "✅ $var_name configured"
    fi
}

# Set up environment variables
set_env_var "VITE_API_BASE_URL" "Backend API base URL" "https://your-backend-domain.com/api/v1"
set_env_var "VITE_WS_URL" "WebSocket URL for real-time updates" "wss://your-backend-domain.com/ws"
set_env_var "VITE_ENVIRONMENT" "Environment name" "production"

echo ""
echo "🎯 Optional environment variables (press Enter to skip):"

# Optional variables
if ! vercel env ls | grep -q "VITE_ANALYTICS_ID"; then
    echo "📊 Analytics ID (Google Analytics, etc.):"
    read -p "Enter analytics ID (or press Enter to skip): " analytics_id
    if [ -n "$analytics_id" ]; then
        echo "$analytics_id" | vercel env add "VITE_ANALYTICS_ID" production
        echo "✅ Analytics ID configured"
    fi
fi

if ! vercel env ls | grep -q "VITE_SENTRY_DSN"; then
    echo "🐛 Sentry DSN for error tracking:"
    read -p "Enter Sentry DSN (or press Enter to skip): " sentry_dsn
    if [ -n "$sentry_dsn" ]; then
        echo "$sentry_dsn" | vercel env add "VITE_SENTRY_DSN" production
        echo "✅ Sentry DSN configured"
    fi
fi

echo ""
echo "🏗️  Configuring build settings..."

# Copy Vercel-optimized configuration files
if [ -f "package.json.vercel" ]; then
    echo "📦 Using Vercel-optimized package.json..."
    cp package.json.vercel package.json
fi

if [ -f "vite.config.vercel.ts" ]; then
    echo "⚙️  Using Vercel-optimized Vite config..."
    cp vite.config.vercel.ts vite.config.ts
fi

echo ""
echo "🧪 Testing build process..."
npm install
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Build test successful"
else
    echo "❌ Build test failed - please check your configuration"
    exit 1
fi

echo ""
echo "🚀 Deploying preview version..."
vercel

echo ""
echo "🎉 Vercel setup completed successfully!"
echo ""
echo "📋 Summary:"
echo "   ✅ Vercel CLI installed and configured"
echo "   ✅ Project linked to Vercel"
echo "   ✅ Environment variables configured"
echo "   ✅ Build configuration optimized"
echo "   ✅ Preview deployment created"
echo ""
echo "🔗 Your preview deployment is ready!"
echo ""
echo "📝 Next steps:"
echo "   1. Test your preview deployment thoroughly"
echo "   2. Update your backend CORS settings to include the Vercel domain"
echo "   3. Deploy to production with: vercel --prod"
echo "   4. Set up custom domain (optional): vercel domains add yourdomain.com"
echo ""
echo "🛠️  Useful commands:"
echo "   vercel --prod          # Deploy to production"
echo "   vercel logs            # View deployment logs"
echo "   vercel env ls          # List environment variables"
echo "   vercel domains ls      # List configured domains"
echo "   vercel ls              # List all deployments"
echo ""
echo "📚 Documentation:"
echo "   Vercel Docs: https://vercel.com/docs"
echo "   Project Guide: ../VERCEL_DEPLOYMENT_GUIDE.md"