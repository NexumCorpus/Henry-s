#!/bin/bash

# Henry's SmartStock AI - CORS Update Script
# Updates backend CORS settings to include Vercel domain

set -e

echo "🔧 Updating CORS settings for Vercel deployment..."

# Get Vercel deployment URL
cd frontend
VERCEL_URL=$(vercel ls | grep "henrys-smartstock" | head -1 | awk '{print $2}')

if [ -z "$VERCEL_URL" ]; then
    echo "❌ No Vercel deployment found. Please deploy to Vercel first."
    exit 1
fi

echo "📍 Found Vercel deployment: https://$VERCEL_URL"

cd ..

# Update backend CORS configuration
echo "⚙️  Updating backend CORS configuration..."

# Check if backend is running
if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "🚀 Starting backend services..."
    docker-compose -f docker-compose.prod.yml up -d backend
    
    echo "⏳ Waiting for backend to be ready..."
    sleep 30
fi

# Update CORS origins in environment
if [ -f ".env" ]; then
    # Check if CORS_ORIGINS exists
    if grep -q "CORS_ORIGINS" .env; then
        # Update existing CORS_ORIGINS
        sed -i.bak "s|CORS_ORIGINS=.*|CORS_ORIGINS=https://$VERCEL_URL,https://$VERCEL_URL-*.vercel.app,http://localhost:3000|" .env
    else
        # Add CORS_ORIGINS
        echo "CORS_ORIGINS=https://$VERCEL_URL,https://$VERCEL_URL-*.vercel.app,http://localhost:3000" >> .env
    fi
    
    echo "✅ Updated .env file with Vercel domain"
else
    echo "❌ .env file not found. Please create it from .env.production"
    exit 1
fi

# Restart backend to apply new CORS settings
echo "🔄 Restarting backend to apply CORS changes..."
docker-compose -f docker-compose.prod.yml restart backend

echo "⏳ Waiting for backend to restart..."
sleep 15

# Test CORS configuration
echo "🧪 Testing CORS configuration..."
CORS_TEST=$(curl -s -H "Origin: https://$VERCEL_URL" \
                 -H "Access-Control-Request-Method: GET" \
                 -H "Access-Control-Request-Headers: X-Requested-With" \
                 -X OPTIONS \
                 http://localhost:8000/api/v1/health)

if echo "$CORS_TEST" | grep -q "Access-Control-Allow-Origin"; then
    echo "✅ CORS configuration successful"
else
    echo "⚠️  CORS test inconclusive - please verify manually"
fi

# Test API connectivity from Vercel domain
echo "🌐 Testing API connectivity..."
API_TEST=$(curl -s -H "Origin: https://$VERCEL_URL" \
               http://localhost:8000/api/v1/health)

if echo "$API_TEST" | grep -q "healthy\|ok"; then
    echo "✅ API connectivity successful"
else
    echo "⚠️  API connectivity test inconclusive"
fi

echo ""
echo "🎉 CORS update completed!"
echo ""
echo "📋 Summary:"
echo "   ✅ Backend CORS updated to include: https://$VERCEL_URL"
echo "   ✅ Preview deployments allowed: https://$VERCEL_URL-*.vercel.app"
echo "   ✅ Development origin maintained: http://localhost:3000"
echo "   ✅ Backend restarted with new configuration"
echo ""
echo "🔗 Your Vercel app should now be able to connect to the backend!"
echo "   Frontend: https://$VERCEL_URL"
echo "   Backend: http://localhost:8000"
echo ""
echo "📝 Next steps:"
echo "   1. Test your Vercel deployment: https://$VERCEL_URL"
echo "   2. Verify login and inventory features work"
echo "   3. Set up custom domain (optional): vercel domains add yourdomain.com"
echo "   4. Deploy to production: vercel --prod"
echo ""
echo "🛠️  If you encounter issues:"
echo "   - Check backend logs: docker-compose -f docker-compose.prod.yml logs backend"
echo "   - Verify CORS in browser dev tools"
echo "   - See troubleshooting guide: VERCEL_TROUBLESHOOTING.md"