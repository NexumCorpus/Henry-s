# Vercel Deployment Troubleshooting Guide

## 🔧 Common Issues and Solutions

### **Build Failures**

#### **Issue: "Build failed with exit code 1"**
```bash
# Check build logs
vercel logs

# Test build locally
cd frontend
npm install
npm run build
```

**Common causes**:
- Missing environment variables
- TypeScript errors
- Missing dependencies
- Incorrect build command

**Solutions**:
```bash
# Fix TypeScript errors
npm run type-check

# Update dependencies
npm update

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### **Issue: "Module not found" errors**
```bash
# Check if all dependencies are in package.json
npm ls

# Install missing dependencies
npm install missing-package-name

# For TypeScript types
npm install --save-dev @types/missing-package-name
```

---

### **Environment Variables**

#### **Issue: Environment variables not working**
```bash
# List current environment variables
vercel env ls

# Remove and re-add variable
vercel env rm VITE_API_BASE_URL production
vercel env add VITE_API_BASE_URL production

# Pull environment variables locally for testing
vercel env pull .env.local
```

**Important**: Vite environment variables must start with `VITE_`

#### **Issue: Backend URL not accessible**
```bash
# Test backend connectivity
curl https://your-backend-domain.com/health

# Check CORS configuration
curl -H "Origin: https://your-app.vercel.app" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS \
     https://your-backend-domain.com/api/v1/health
```

---

### **CORS Issues**

#### **Issue: "CORS policy blocked the request"**

**Backend Fix** (update your backend CORS settings):
```python
# In your FastAPI app
CORS_ORIGINS = [
    "https://your-app.vercel.app",
    "https://your-app-*.vercel.app",  # Preview deployments
    "https://your-custom-domain.com",
    "http://localhost:3000",  # Development
]
```

**Vercel Configuration** (in `vercel.json`):
```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://your-backend-domain.com/api/:path*"
    }
  ]
}
```

---

### **WebSocket Connection Issues**

#### **Issue: WebSocket connections failing**

**Check WebSocket URL**:
```javascript
// In your frontend code
const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';
console.log('WebSocket URL:', wsUrl);
```

**Test WebSocket connection**:
```bash
# Test WebSocket endpoint
wscat -c wss://your-backend-domain.com/ws
```

**Backend WebSocket CORS**:
```python
# Ensure WebSocket endpoint allows Vercel origins
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    origin = websocket.headers.get("origin")
    if origin not in ALLOWED_ORIGINS:
        await websocket.close(code=1008)
        return
    
    await websocket.accept()
    # ... rest of WebSocket logic
```

---

### **Routing Issues**

#### **Issue: "404 Not Found" on page refresh**

**Solution**: Ensure SPA routing is configured in `vercel.json`:
```json
{
  "routes": [
    {
      "handle": "filesystem"
    },
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ]
}
```

#### **Issue: API routes not working**

**Check proxy configuration** in `vercel.json`:
```json
{
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://your-backend-domain.com/api/:path*"
    }
  ]
}
```

---

### **Performance Issues**

#### **Issue: Slow loading times**

**Optimize bundle size**:
```bash
# Analyze bundle
npm run build
npx vite-bundle-analyzer dist

# Check for large dependencies
npm ls --depth=0 --long
```

**Vite optimization** (in `vite.config.ts`):
```typescript
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          redux: ['@reduxjs/toolkit', 'react-redux'],
        }
      }
    }
  }
})
```

#### **Issue: Images loading slowly**

**Use Vercel Image Optimization**:
```jsx
// Instead of <img>
import Image from 'next/image'  // If using Next.js

// Or optimize images manually
<img 
  src="/optimized-image.webp" 
  alt="Description"
  loading="lazy"
  width="300"
  height="200"
/>
```

---

### **Domain and SSL Issues**

#### **Issue: Custom domain not working**

```bash
# Add domain to Vercel
vercel domains add yourdomain.com

# Check domain configuration
vercel domains ls

# Verify DNS settings
dig yourdomain.com
dig www.yourdomain.com
```

**Required DNS records**:
```
Type: A
Name: @
Value: 76.76.19.61

Type: CNAME
Name: www
Value: cname.vercel-dns.com
```

#### **Issue: SSL certificate problems**

```bash
# Check SSL status
curl -I https://yourdomain.com

# Force SSL renewal (if needed)
vercel certs ls
vercel certs rm yourdomain.com
vercel certs add yourdomain.com
```

---

### **Deployment Issues**

#### **Issue: Deployment stuck or taking too long**

```bash
# Cancel current deployment
vercel cancel

# Check deployment status
vercel ls

# Redeploy
vercel --prod
```

#### **Issue: Preview deployments not working**

```bash
# Check Git integration
vercel git ls

# Manually create preview
vercel --target preview

# Check branch settings in Vercel dashboard
```

---

### **Database Connection Issues**

#### **Issue: Backend can't connect to database**

**Check backend logs**:
```bash
# On your VPS/server
docker-compose -f docker-compose.prod.yml logs backend

# Check database connectivity
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.core.database import engine
try:
    with engine.connect() as conn:
        print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
"
```

**Common fixes**:
```bash
# Restart database
docker-compose -f docker-compose.prod.yml restart postgres

# Check database logs
docker-compose -f docker-compose.prod.yml logs postgres

# Verify environment variables
docker-compose -f docker-compose.prod.yml exec backend env | grep DATABASE
```

---

## 🛠️ Debugging Tools

### **Vercel CLI Commands**
```bash
# View all deployments
vercel ls

# View deployment logs
vercel logs [deployment-url]

# View environment variables
vercel env ls

# Pull environment variables locally
vercel env pull .env.local

# View project settings
vercel project ls

# View domains
vercel domains ls

# View certificates
vercel certs ls
```

### **Local Testing**
```bash
# Test production build locally
cd frontend
npm run build
npm run preview

# Test with production environment variables
vercel env pull .env.local
npm run dev
```

### **Network Testing**
```bash
# Test API connectivity
curl -v https://your-backend-domain.com/api/v1/health

# Test WebSocket
wscat -c wss://your-backend-domain.com/ws

# Test CORS
curl -H "Origin: https://your-app.vercel.app" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS \
     https://your-backend-domain.com/api/v1/health
```

---

## 📞 Getting Help

### **Vercel Support**
- 📖 **Documentation**: https://vercel.com/docs
- 💬 **Community**: https://github.com/vercel/vercel/discussions
- 📧 **Support**: support@vercel.com (Pro plans)
- 🐛 **Bug Reports**: https://github.com/vercel/vercel/issues

### **Project-Specific Help**
- 📖 **Deployment Guide**: [VERCEL_DEPLOYMENT_GUIDE.md](VERCEL_DEPLOYMENT_GUIDE.md)
- 🎬 **Demo Script**: [DEMO_SCRIPT.md](DEMO_SCRIPT.md)
- ✅ **Checklist**: [PRODUCTION_CHECKLIST.md](PRODUCTION_CHECKLIST.md)

### **Emergency Rollback**
```bash
# List recent deployments
vercel ls

# Promote previous deployment to production
vercel promote [previous-deployment-url] --scope=production

# Or rollback via dashboard
# Go to vercel.com → Your Project → Deployments → Promote
```

---

## 🎯 Prevention Tips

### **Before Deploying**
1. ✅ Test build locally: `npm run build`
2. ✅ Test preview locally: `npm run preview`
3. ✅ Verify environment variables: `vercel env ls`
4. ✅ Check backend connectivity: `curl backend-url/health`
5. ✅ Test CORS configuration

### **Regular Maintenance**
1. 🔄 Keep dependencies updated: `npm update`
2. 📊 Monitor performance: Vercel Analytics
3. 🔍 Check logs regularly: `vercel logs`
4. 🔒 Review security headers: `curl -I your-domain.com`
5. 💾 Backup configurations: Save `vercel.json` and env vars

### **Monitoring**
1. 📈 Set up Vercel Analytics
2. 🚨 Configure uptime monitoring (UptimeRobot, Pingdom)
3. 📧 Set up error tracking (Sentry)
4. 📊 Monitor Core Web Vitals
5. 🔍 Regular performance audits

---

**Remember**: Most issues are configuration-related. Double-check environment variables, CORS settings, and API URLs first! 🔧