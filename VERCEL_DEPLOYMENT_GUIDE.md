# Henry's SmartStock AI - Vercel Deployment Guide

## 🌐 **Vercel Deployment Option**

Vercel is an excellent choice for deploying the frontend of Henry's SmartStock AI, offering:

- ✅ **Instant Global CDN** - Lightning-fast loading worldwide
- ✅ **Automatic HTTPS** - SSL certificates managed automatically
- ✅ **Zero Configuration** - Deploy with a single command
- ✅ **Preview Deployments** - Test changes before going live
- ✅ **Custom Domains** - Easy domain setup and management
- ✅ **Edge Functions** - Serverless functions at the edge
- ✅ **Free Tier Available** - Great for MVP deployment

---

## 🏗️ **Architecture: Vercel + Backend**

```
┌─────────────────────────────────────────────────────────────┐
│                    Vercel Global CDN                       │
│              (Frontend - React App)                        │
│                https://henrys-app.vercel.app               │
└─────────────────────┬───────────────────────────────────────┘
                      │ API Calls & WebSocket
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                 Your Server/VPS                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Backend   │  │ PostgreSQL  │  │    Redis    │        │
│  │  (FastAPI)  │  │ (Database)  │  │   (Cache)   │        │
│  │ Port: 8000  │  │ Port: 5432  │  │ Port: 6379  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

**Benefits of This Setup**:
- **Frontend**: Served globally via Vercel's CDN (fast loading)
- **Backend**: Full control over data and business logic
- **Cost Effective**: Vercel free tier + small VPS for backend
- **Scalable**: Frontend scales automatically, backend scales as needed

---

## 🚀 **Quick Deployment**

### **Option 1: One-Click Deployment**

```bash
# 1. Clone and setup
git clone https://github.com/your-repo/henrys-smartstock-ai.git
cd henrys-smartstock-ai

# 2. Deploy everything (frontend to Vercel + backend to your server)
./deploy-vercel.sh production
```

### **Option 2: Manual Step-by-Step**

#### **Step 1: Deploy Backend Services**
```bash
# Set up backend on your VPS/server
cp .env.production .env
nano .env  # Configure your settings

# Start backend services
docker-compose -f docker-compose.prod.yml up -d postgres redis backend

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

#### **Step 2: Deploy Frontend to Vercel**
```bash
# Install Vercel CLI
npm install -g vercel

# Navigate to frontend
cd frontend

# Deploy to Vercel
vercel

# For production deployment
vercel --prod
```

---

## ⚙️ **Configuration**

### **Frontend Environment Variables (Vercel)**

Set these in your Vercel project dashboard or via CLI:

```bash
# Set environment variables
vercel env add VITE_API_BASE_URL production
vercel env add VITE_WS_URL production
vercel env add VITE_ENVIRONMENT production
```

**Values**:
- `VITE_API_BASE_URL`: `https://your-backend-domain.com/api/v1`
- `VITE_WS_URL`: `wss://your-backend-domain.com/ws`
- `VITE_ENVIRONMENT`: `production`

### **Backend CORS Configuration**

Update your backend to allow requests from Vercel:

```python
# In backend/app/core/config.py
CORS_ORIGINS = [
    "https://your-app.vercel.app",
    "https://your-custom-domain.com",
    "http://localhost:3000",  # For development
]
```

---

## 🌍 **Custom Domain Setup**

### **Option 1: Use Vercel Domain**
Your app will be available at: `https://henrys-smartstock-ai.vercel.app`

### **Option 2: Custom Domain**
```bash
# Add your domain to Vercel
vercel domains add yourdomain.com

# Configure DNS
# Add CNAME record: www -> cname.vercel-dns.com
# Add A record: @ -> 76.76.19.61
```

### **Option 3: Subdomain**
```bash
# Use a subdomain for the app
vercel domains add app.henrysonmarket.com
```

---

## 💰 **Cost Breakdown**

### **Vercel Pricing**
- **Hobby (Free)**: Perfect for MVP
  - 100GB bandwidth/month
  - Unlimited static deployments
  - Custom domains included
  - Automatic HTTPS

- **Pro ($20/month)**: For production
  - 1TB bandwidth/month
  - Password protection
  - Advanced analytics
  - Priority support

### **Backend Hosting**
- **DigitalOcean Droplet**: $40/month (4GB RAM, 2 vCPUs)
- **Linode VPS**: $36/month (4GB RAM, 2 vCPUs)
- **AWS EC2 t3.medium**: ~$30/month (4GB RAM, 2 vCPUs)

### **Total Monthly Cost**
- **MVP**: $0 (Vercel free) + $40 (VPS) = **$40/month**
- **Production**: $20 (Vercel Pro) + $40 (VPS) = **$60/month**

---

## 🔧 **Development Workflow**

### **Local Development**
```bash
# Start backend locally
docker-compose up -d

# Start frontend locally (connects to local backend)
cd frontend
npm run dev
```

### **Preview Deployments**
```bash
# Deploy preview (automatic on git push)
vercel

# Or deploy specific branch
vercel --target preview
```

### **Production Deployment**
```bash
# Deploy to production
vercel --prod

# Or set up automatic deployment from main branch
vercel --prod --confirm
```

---

## 📊 **Monitoring & Analytics**

### **Vercel Analytics**
- **Web Vitals**: Core performance metrics
- **Audience**: Geographic distribution
- **Top Pages**: Most visited pages
- **Devices**: Desktop vs mobile usage

### **Backend Monitoring**
```bash
# Health checks
curl https://your-backend-domain.com/health

# View logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Monitor resources
docker stats
```

---

## 🚀 **Deployment Scenarios**

### **Scenario 1: MVP Launch (Recommended)**
- **Frontend**: Vercel (Free tier)
- **Backend**: DigitalOcean Droplet ($40/month)
- **Domain**: Use Vercel subdomain or custom domain
- **SSL**: Automatic via Vercel
- **Total Cost**: $40/month

### **Scenario 2: Production Ready**
- **Frontend**: Vercel Pro ($20/month)
- **Backend**: Managed cloud services
- **Monitoring**: Advanced analytics and alerts
- **Custom Domain**: Professional domain setup
- **Total Cost**: $100-200/month

### **Scenario 3: Enterprise Scale**
- **Frontend**: Vercel Enterprise
- **Backend**: Multi-region deployment
- **Database**: Managed database services
- **CDN**: Global content delivery
- **Total Cost**: $500+/month

---

## 🔒 **Security Considerations**

### **Frontend Security (Vercel)**
- ✅ **Automatic HTTPS** with SSL certificates
- ✅ **Security Headers** configured in vercel.json
- ✅ **Content Security Policy** for XSS protection
- ✅ **DDoS Protection** via Vercel's infrastructure

### **Backend Security**
- ✅ **CORS Configuration** to allow only Vercel domain
- ✅ **JWT Authentication** for API access
- ✅ **Rate Limiting** on API endpoints
- ✅ **Input Validation** and sanitization

### **Environment Variables**
- ✅ **Encrypted Storage** in Vercel dashboard
- ✅ **Build-time Injection** for frontend variables
- ✅ **No Secrets in Frontend** code

---

## 🛠️ **Troubleshooting**

### **Common Issues**

#### **CORS Errors**
```bash
# Update backend CORS settings
# Add your Vercel domain to CORS_ORIGINS
```

#### **WebSocket Connection Issues**
```bash
# Ensure WebSocket URL is correct
VITE_WS_URL=wss://your-backend-domain.com/ws

# Check backend WebSocket endpoint
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Key: test" -H "Sec-WebSocket-Version: 13" \
  https://your-backend-domain.com/ws
```

#### **Build Failures**
```bash
# Check build logs in Vercel dashboard
vercel logs

# Test build locally
cd frontend
npm run build
```

#### **Environment Variables Not Working**
```bash
# List current environment variables
vercel env ls

# Update environment variable
vercel env rm VITE_API_BASE_URL production
vercel env add VITE_API_BASE_URL production
```

---

## 📈 **Performance Optimization**

### **Frontend Optimization (Vercel)**
- ✅ **Automatic Code Splitting** via Vite
- ✅ **Image Optimization** with Vercel Image API
- ✅ **Edge Caching** for static assets
- ✅ **Compression** (Gzip/Brotli) automatic

### **Backend Optimization**
- ✅ **Database Connection Pooling**
- ✅ **Redis Caching** for frequent queries
- ✅ **API Response Compression**
- ✅ **WebSocket Connection Management**

---

## 🎯 **Best Practices**

### **Deployment Best Practices**
1. **Use Environment Variables** for all configuration
2. **Test Preview Deployments** before production
3. **Monitor Performance** with Vercel Analytics
4. **Set Up Alerts** for backend health
5. **Regular Backups** of backend data

### **Development Best Practices**
1. **Branch Protection** on main branch
2. **Automatic Deployments** from git
3. **Preview URLs** for feature testing
4. **Environment Parity** between dev/prod

---

## 🎉 **Ready to Deploy with Vercel?**

Vercel offers the perfect balance of simplicity and power for Henry's SmartStock AI frontend:

### **Advantages**
- ✅ **Zero Configuration** deployment
- ✅ **Global CDN** for fast loading
- ✅ **Automatic HTTPS** and security
- ✅ **Preview Deployments** for testing
- ✅ **Custom Domains** included
- ✅ **Free Tier** perfect for MVP

### **Quick Start**
```bash
# 1. Clone repository
git clone https://github.com/your-repo/henrys-smartstock-ai.git
cd henrys-smartstock-ai

# 2. Deploy with one command
./deploy-vercel.sh production

# 3. Your app is live!
# Frontend: https://henrys-smartstock-ai.vercel.app
# Backend: https://your-backend-domain.com
```

**Total deployment time**: 15 minutes
**Monthly cost**: $40 (free Vercel + $40 VPS)
**Global performance**: Excellent
**Maintenance**: Minimal

**Vercel + VPS backend is an excellent choice for Henry's SmartStock AI MVP!** 🚀

---

## 📞 **Support**

### **Vercel Resources**
- 📖 **Documentation**: https://vercel.com/docs
- 💬 **Community**: https://github.com/vercel/vercel/discussions
- 📧 **Support**: support@vercel.com

### **Project Support**
- 📖 **Deployment Guide**: See main deployment documentation
- 🎬 **Demo Script**: Test your deployment
- ✅ **Checklist**: Verify everything works
- 📧 **Project Support**: [Your support contact]