# Henry's SmartStock AI - Docker Compose Complete Guide

## 🐳 **What is Docker Compose?**

Docker Compose is a tool that lets you define and run multi-container applications. Instead of managing individual containers, you define all your services in a single `docker-compose.yml` file and manage them together.

### **Why Docker Compose for Henry's SmartStock AI?**

✅ **Single Command Deployment** - Start everything with `docker-compose up`
✅ **Service Orchestration** - Automatic dependency management
✅ **Network Isolation** - Services communicate securely
✅ **Volume Management** - Persistent data storage
✅ **Environment Management** - Consistent configurations
✅ **Easy Scaling** - Scale services independently

---

## 🏗️ **Henry's Architecture with Docker Compose**

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Host Server                      │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Nginx     │  │   React     │  │   FastAPI   │        │
│  │ (Reverse    │  │ (Frontend)  │  │  (Backend)  │        │
│  │  Proxy)     │  │ Port: 3000  │  │ Port: 8000  │        │
│  │ Port: 80    │  └─────────────┘  └─────────────┘        │
│  └─────────────┘         │                │               │
│         │                │                │               │
│         └────────────────┼────────────────┘               │
│                          │                                │
│  ┌─────────────┐  ┌─────────────┐                        │
│  │ PostgreSQL  │  │    Redis    │                        │
│  │ (Database)  │  │   (Cache)   │                        │
│  │ Port: 5432  │  │ Port: 6379  │                        │
│  └─────────────┘  └─────────────┘                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**All services run on one server, communicate through Docker networks, and are managed together.**

---

## 🚀 **Complete Docker Compose Setup**

### **Current Services in Your Setup**

1. **PostgreSQL Database** - Stores all application data
2. **Redis Cache** - Handles sessions and real-time data
3. **FastAPI Backend** - API server and business logic
4. **React Frontend** - User interface served by Nginx
5. **Nginx Reverse Proxy** - Routes traffic and handles SSL

### **How They Work Together**

```yaml
# Simplified view of your docker-compose.prod.yml
services:
  postgres:     # Database
    image: postgres:15-alpine
    ports: ["5432:5432"]
    
  redis:        # Cache
    image: redis:7-alpine
    ports: ["6379:6379"]
    
  backend:      # API Server
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [postgres, redis]
    
  frontend:     # Web Interface
    build: ./frontend
    ports: ["80:80", "443:443"]
    depends_on: [backend]
```

---

## 🔧 **Optimized Docker Compose Configuration**

Let me show you an enhanced version that's even better for production:

---

## 🚀 **Complete Docker Compose Deployment**

### **One Command Deployment**

```bash
# Deploy everything together
./deploy-docker-complete.sh production
```

**What this gives you**:
- ✅ **Frontend + Backend + Database** - Everything on one server
- ✅ **Nginx Reverse Proxy** - Professional routing and SSL
- ✅ **Automatic Health Checks** - Services restart if they fail
- ✅ **Persistent Data** - Database survives container restarts
- ✅ **Logging & Monitoring** - Centralized log management
- ✅ **Backup System** - Automated database backups

### **Architecture Overview**

```
Internet → Nginx (Port 80/443) → Frontend (Port 3000)
                                → Backend (Port 8000) → PostgreSQL (Port 5432)
                                                      → Redis (Port 6379)
```

**All services communicate through a private Docker network for security.**

---

## 💰 **Cost Comparison: Docker Compose vs Vercel**

| Aspect | Docker Compose | Vercel + VPS |
|--------|----------------|---------------|
| **Monthly Cost** | $40-60 | $40 |
| **Setup Time** | 30 minutes | 15 minutes |
| **Global CDN** | ❌ No | ✅ Yes |
| **Auto HTTPS** | ⚙️ Manual | ✅ Automatic |
| **Maintenance** | Medium | Low |
| **Control** | ✅ Complete | ✅ Backend only |
| **Scaling** | Manual | ✅ Frontend auto |
| **Best For** | Full control | Global performance |

---

## 🔧 **Docker Compose Advantages**

### **✅ Complete Control**
- **All services on your server** - No external dependencies
- **Custom configurations** - Modify anything you want
- **Data ownership** - Everything stays on your infrastructure
- **Network isolation** - Services communicate securely

### **✅ Simple Management**
- **Single command deployment** - `docker-compose up`
- **Unified logging** - All logs in one place
- **Easy scaling** - Scale individual services
- **Consistent environments** - Same setup everywhere

### **✅ Cost Effective**
- **No external service fees** - Just your server cost
- **Predictable pricing** - Fixed monthly VPS cost
- **Resource efficiency** - Optimize for your needs

### **✅ Development Friendly**
- **Local development** - Same setup as production
- **Easy debugging** - Direct access to all services
- **Fast iteration** - No deployment delays

---

## 🏗️ **Service Breakdown**

### **1. PostgreSQL Database**
```yaml
postgres:
  image: postgres:15-alpine
  environment:
    POSTGRES_DB: henrys_smartstock
    POSTGRES_USER: henrys_user
    POSTGRES_PASSWORD: your_secure_password
  volumes:
    - postgres_data:/var/lib/postgresql/data
  healthcheck:
    test: ["CMD-SHELL", "pg_isready"]
```

**What it does**:
- Stores all application data (users, inventory, transactions)
- Automatic health checks and restarts
- Persistent data storage with Docker volumes
- Optimized for production workloads

### **2. Redis Cache**
```yaml
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes --requirepass password
  volumes:
    - redis_data:/data
```

**What it does**:
- Handles user sessions and authentication
- Caches frequently accessed data
- Manages WebSocket connections
- Persistent storage for reliability

### **3. FastAPI Backend**
```yaml
backend:
  build: ./backend
  environment:
    - DATABASE_URL=postgresql://user:pass@postgres:5432/db
    - REDIS_URL=redis://:pass@redis:6379/0
  depends_on:
    - postgres
    - redis
```

**What it does**:
- Provides REST API for all operations
- Handles authentication and authorization
- Manages WebSocket connections for real-time updates
- Processes business logic and data validation

### **4. React Frontend**
```yaml
frontend:
  build: ./frontend
  environment:
    - VITE_API_BASE_URL=http://localhost:8000/api/v1
    - VITE_WS_URL=ws://localhost:8000/ws
```

**What it does**:
- Serves the user interface
- Built as static files and served by Nginx
- Optimized for production with code splitting
- Mobile-responsive for bar environments

### **5. Nginx Reverse Proxy**
```yaml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx/nginx-complete.conf:/etc/nginx/nginx.conf
```

**What it does**:
- Routes traffic to appropriate services
- Handles SSL termination
- Serves static files efficiently
- Provides rate limiting and security headers
- Load balances requests

---

## 🚀 **Deployment Process**

### **Step 1: Prepare Environment (5 minutes)**
```bash
# Clone repository
git clone https://github.com/your-repo/henrys-smartstock-ai.git
cd henrys-smartstock-ai

# Configure environment
cp .env.production .env
nano .env  # Add your secure passwords
```

### **Step 2: Deploy Everything (10 minutes)**
```bash
# Make script executable
chmod +x deploy-docker-complete.sh

# Deploy all services
./deploy-docker-complete.sh production
```

### **Step 3: Verify Deployment (5 minutes)**
```bash
# Check all services are running
docker-compose -f docker-compose.complete.yml ps

# Test the application
curl http://localhost:80/health
curl http://localhost:80/api/v1/health
```

**Total Time**: 20 minutes to fully operational system

---

## 📊 **Service Management**

### **Common Commands**
```bash
# View all services
docker-compose -f docker-compose.complete.yml ps

# View logs for all services
docker-compose -f docker-compose.complete.yml logs -f

# View logs for specific service
docker-compose -f docker-compose.complete.yml logs -f backend

# Restart a service
docker-compose -f docker-compose.complete.yml restart backend

# Scale a service
docker-compose -f docker-compose.complete.yml up -d --scale backend=2

# Stop all services
docker-compose -f docker-compose.complete.yml down

# Stop and remove all data (⚠️ DESTRUCTIVE)
docker-compose -f docker-compose.complete.yml down -v
```

### **Health Monitoring**
```bash
# Check service health
docker-compose -f docker-compose.complete.yml ps

# View resource usage
docker stats

# Check individual service health
curl http://localhost:80/health      # Nginx
curl http://localhost:3000/health    # Frontend
curl http://localhost:8000/health    # Backend
```

---

## 💾 **Data Management**

### **Backup Strategy**
```bash
# Manual database backup
docker-compose -f docker-compose.complete.yml exec postgres \
  pg_dump -U henrys_user henrys_smartstock > backup_$(date +%Y%m%d).sql

# Automated backups (included in docker-compose.complete.yml)
docker-compose -f docker-compose.complete.yml up -d backup
```

### **Data Persistence**
- **PostgreSQL data**: Stored in `./data/postgres`
- **Redis data**: Stored in `./data/redis`
- **Application logs**: Stored in `./logs`
- **Backups**: Stored in `./backups`

### **Restore from Backup**
```bash
# Restore database from backup
docker-compose -f docker-compose.complete.yml exec -T postgres \
  psql -U henrys_user -d henrys_smartstock < backup_20231201.sql
```

---

## 🔒 **Security Features**

### **Network Security**
- **Isolated Docker network** - Services communicate privately
- **No external database access** - Database only accessible from backend
- **Rate limiting** - Nginx prevents API abuse
- **Security headers** - XSS, CSRF, clickjacking protection

### **Application Security**
- **JWT authentication** - Secure token-based auth
- **Password hashing** - bcrypt encryption
- **Input validation** - SQL injection prevention
- **CORS configuration** - Controlled cross-origin requests

### **SSL/HTTPS Setup**
```bash
# Generate self-signed certificate (for testing)
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem

# Or use Let's Encrypt (for production)
certbot certonly --standalone -d yourdomain.com
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem
```

---

## 📈 **Performance Optimization**

### **Database Optimization**
```yaml
postgres:
  environment:
    - POSTGRES_SHARED_PRELOAD_LIBRARIES=pg_stat_statements
    - POSTGRES_MAX_CONNECTIONS=100
    - POSTGRES_SHARED_BUFFERS=256MB
    - POSTGRES_EFFECTIVE_CACHE_SIZE=1GB
```

### **Redis Optimization**
```yaml
redis:
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

### **Nginx Optimization**
- **Gzip compression** - Reduces bandwidth usage
- **Static file caching** - Improves load times
- **Connection pooling** - Reduces backend load
- **Rate limiting** - Prevents abuse

---

## 🔧 **Troubleshooting**

### **Common Issues**

#### **Services Won't Start**
```bash
# Check Docker daemon
sudo systemctl status docker

# Check logs
docker-compose -f docker-compose.complete.yml logs

# Check disk space
df -h

# Check memory usage
free -h
```

#### **Database Connection Issues**
```bash
# Check database status
docker-compose -f docker-compose.complete.yml exec postgres pg_isready

# Check database logs
docker-compose -f docker-compose.complete.yml logs postgres

# Reset database (⚠️ DESTRUCTIVE)
docker-compose -f docker-compose.complete.yml down -v
docker-compose -f docker-compose.complete.yml up -d
```

#### **Frontend Not Loading**
```bash
# Check Nginx configuration
docker-compose -f docker-compose.complete.yml exec nginx nginx -t

# Check frontend logs
docker-compose -f docker-compose.complete.yml logs frontend

# Rebuild frontend
docker-compose -f docker-compose.complete.yml build frontend
docker-compose -f docker-compose.complete.yml up -d frontend
```

---

## 🎯 **When to Choose Docker Compose**

### **✅ Choose Docker Compose If:**
- You want **complete control** over all components
- You prefer **single-server deployment**
- You need **custom configurations**
- You want **predictable costs**
- You're comfortable with **server administration**
- You need **data to stay on-premises**

### **❌ Consider Alternatives If:**
- You need **global CDN performance**
- You want **zero maintenance**
- You need **automatic scaling**
- You prefer **managed services**
- You want **fastest deployment**

---

## 🎉 **Docker Compose Success Story**

With Docker Compose, Henry's SmartStock AI gives you:

### **Complete System**
- ✅ **All services integrated** - Frontend, backend, database, cache
- ✅ **Professional routing** - Nginx reverse proxy
- ✅ **Persistent data** - Survives restarts and updates
- ✅ **Automated backups** - Daily database backups
- ✅ **Health monitoring** - Automatic service recovery

### **Operational Benefits**
- ✅ **Single server management** - Everything in one place
- ✅ **Consistent environments** - Same setup dev to prod
- ✅ **Easy scaling** - Scale services independently
- ✅ **Cost effective** - No external service fees

### **Perfect For**
- 🏠 **Single location bars** - Complete control
- 🔧 **Tech-savvy owners** - Comfortable with servers
- 💰 **Budget conscious** - Predictable costs
- 🛠️ **Custom requirements** - Full configuration control

---

## 🚀 **Ready to Deploy with Docker Compose?**

```bash
# Get started now
git clone https://github.com/your-repo/henrys-smartstock-ai.git
cd henrys-smartstock-ai
cp .env.production .env
nano .env  # Configure your settings
./deploy-docker-complete.sh production

# Your complete system will be running at:
# http://localhost:80 - Main application
# http://localhost:8000/docs - API documentation
```

**Docker Compose gives you a complete, professional inventory management system with full control and predictable costs!** 🐳