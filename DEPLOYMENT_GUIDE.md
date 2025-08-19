# Henry's SmartStock AI - MVP Deployment Guide

This guide covers deploying the Henry's SmartStock AI MVP to production environments.

## 🎯 MVP Features

The MVP includes:
- ✅ **Real-time Inventory Dashboard** - Live stock levels across locations
- ✅ **Manual Inventory Management** - Add, update, and adjust stock levels
- ✅ **Multi-location Support** - Main bar, rooftop, storage tracking
- ✅ **Role-based Access** - Different views for barbacks, bartenders, managers
- ✅ **Stock Alerts** - Low stock notifications
- ✅ **Barcode Lookup** - Scan to identify items
- ✅ **WebSocket Real-time Updates** - Live inventory changes
- ✅ **Responsive Design** - Works on desktop, tablet, and mobile

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (React/Nginx) │◄──►│   (FastAPI)     │◄──►│  (PostgreSQL)   │
│   Port: 80      │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │     Redis       │
                       │   (Cache)       │
                       │   Port: 6379    │
                       └─────────────────┘
```

## 🚀 Deployment Options

### Option 1: Docker Compose (Recommended for MVP)

**Best for**: Small to medium deployments, development, testing

**Pros**:
- Simple setup and management
- All services in one configuration
- Easy to backup and restore
- Cost-effective

**Cons**:
- Single server dependency
- Limited scalability

### Option 2: Cloud Deployment (AWS/Azure/GCP)

**Best for**: Production environments, scalability requirements

**Pros**:
- High availability
- Auto-scaling
- Managed services
- Professional monitoring

**Cons**:
- Higher complexity
- Higher cost
- Requires cloud expertise

### Option 3: VPS Deployment

**Best for**: Budget-conscious deployments, full control

**Pros**:
- Cost-effective
- Full server control
- Predictable costs

**Cons**:
- Manual server management
- Limited scalability
- Single point of failure

## 📋 Prerequisites

### System Requirements

**Minimum**:
- 2 CPU cores
- 4 GB RAM
- 20 GB storage
- Ubuntu 20.04+ or similar Linux distribution

**Recommended**:
- 4 CPU cores
- 8 GB RAM
- 50 GB SSD storage
- Ubuntu 22.04 LTS

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- Git
- curl
- SSL certificates (for HTTPS)

## 🛠️ Installation Steps

### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login to apply Docker group changes
```

### Step 2: Clone Repository

```bash
git clone https://github.com/your-repo/henrys-smartstock-ai.git
cd henrys-smartstock-ai
```

### Step 3: Configure Environment

```bash
# Copy production environment template
cp .env.production .env

# Edit configuration
nano .env
```

**Required Configuration**:
```env
# Database
POSTGRES_PASSWORD=your_secure_password_here
REDIS_PASSWORD=your_redis_password_here

# Security
SECRET_KEY=your_very_secure_secret_key_32_chars_minimum

# Domain (replace with your domain)
CORS_ORIGINS=https://yourdomain.com
VITE_API_BASE_URL=https://yourdomain.com/api/v1
VITE_WS_URL=wss://yourdomain.com/ws

# Email notifications (optional)
SMTP_HOST=smtp.gmail.com
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### Step 4: Deploy Application

```bash
# Make deployment script executable (Linux/Mac)
chmod +x deploy.sh

# Run deployment
./deploy.sh production

# Or on Windows
deploy.bat production
```

### Step 5: Verify Deployment

```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Test endpoints
curl http://localhost:80/health
curl http://localhost:8000/health
```

## 🔒 Security Configuration

### SSL/HTTPS Setup

1. **Obtain SSL Certificate**:
   ```bash
   # Using Let's Encrypt (free)
   sudo apt install certbot
   sudo certbot certonly --standalone -d yourdomain.com
   
   # Copy certificates
   sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
   sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem
   ```

2. **Update Nginx Configuration**:
   ```nginx
   server {
       listen 443 ssl http2;
       ssl_certificate /etc/nginx/ssl/cert.pem;
       ssl_certificate_key /etc/nginx/ssl/key.pem;
       # ... rest of configuration
   }
   ```

### Firewall Configuration

```bash
# Configure UFW firewall
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

### Change Default Passwords

1. **Admin User**: Login and change password immediately
2. **Database**: Use strong passwords in `.env`
3. **Redis**: Configure password authentication

## 📊 Monitoring and Maintenance

### Health Monitoring

```bash
# Run health check
./monitor.sh

# Set up automated monitoring (cron job)
crontab -e
# Add: */5 * * * * /path/to/henrys-smartstock-ai/monitor.sh
```

### Backup Strategy

```bash
# Manual backup
./backup.sh

# Automated daily backups (cron job)
crontab -e
# Add: 0 2 * * * /path/to/henrys-smartstock-ai/backup.sh
```

### Log Management

```bash
# View application logs
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend

# Log rotation (add to /etc/logrotate.d/henrys-smartstock)
/path/to/henrys-smartstock-ai/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
}
```

## 🔧 Troubleshooting

### Common Issues

1. **Services Won't Start**:
   ```bash
   # Check Docker daemon
   sudo systemctl status docker
   
   # Check logs
   docker-compose -f docker-compose.prod.yml logs
   ```

2. **Database Connection Issues**:
   ```bash
   # Check database status
   docker-compose -f docker-compose.prod.yml exec postgres pg_isready
   
   # Reset database (WARNING: Data loss)
   docker-compose -f docker-compose.prod.yml down -v
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Frontend Not Loading**:
   ```bash
   # Check Nginx configuration
   docker-compose -f docker-compose.prod.yml exec frontend nginx -t
   
   # Rebuild frontend
   docker-compose -f docker-compose.prod.yml build frontend
   ```

4. **WebSocket Connection Issues**:
   - Check firewall settings
   - Verify WebSocket URL in frontend configuration
   - Check proxy configuration in Nginx

### Performance Optimization

1. **Database Optimization**:
   ```sql
   -- Add indexes for frequently queried columns
   CREATE INDEX idx_inventory_location ON inventory_items(location_id);
   CREATE INDEX idx_stock_levels_item ON stock_levels(item_id);
   ```

2. **Redis Configuration**:
   ```bash
   # Optimize Redis memory usage
   docker-compose -f docker-compose.prod.yml exec redis redis-cli CONFIG SET maxmemory 256mb
   docker-compose -f docker-compose.prod.yml exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
   ```

## 📈 Scaling Considerations

### Horizontal Scaling

When ready to scale beyond single-server deployment:

1. **Load Balancer**: Add Nginx or HAProxy load balancer
2. **Database**: Move to managed PostgreSQL (AWS RDS, etc.)
3. **Cache**: Use managed Redis (AWS ElastiCache, etc.)
4. **File Storage**: Use object storage (AWS S3, etc.)
5. **Container Orchestration**: Migrate to Kubernetes

### Monitoring and Alerting

For production environments, consider:

1. **Application Monitoring**: Datadog, New Relic, or Prometheus
2. **Log Aggregation**: ELK Stack or Splunk
3. **Uptime Monitoring**: Pingdom or UptimeRobot
4. **Error Tracking**: Sentry or Rollbar

## 🎯 MVP Success Metrics

Track these metrics to measure MVP success:

### Technical Metrics
- **Uptime**: Target 99.5%
- **Response Time**: < 2 seconds for dashboard load
- **Error Rate**: < 1% of requests
- **WebSocket Connection**: < 5 second reconnection time

### Business Metrics
- **User Adoption**: % of staff using the system daily
- **Inventory Accuracy**: Reduction in stock discrepancies
- **Time Savings**: Minutes saved per inventory update
- **Alert Effectiveness**: % of low-stock alerts acted upon

### User Experience Metrics
- **Login Success Rate**: > 95%
- **Feature Usage**: Which features are used most
- **Mobile Usage**: % of updates from mobile devices
- **Error Reports**: User-reported issues

## 🚀 Next Phase Planning

Based on MVP feedback, prioritize:

1. **Mobile App** - Native iOS/Android app
2. **POS Integration** - Automatic inventory deduction
3. **Basic Forecasting** - Simple demand prediction
4. **Automated Ordering** - Generate purchase orders
5. **Advanced Analytics** - Trend analysis and reporting

## 📞 Support and Maintenance

### Regular Maintenance Tasks

**Daily**:
- Monitor system health
- Check error logs
- Verify backup completion

**Weekly**:
- Review performance metrics
- Update security patches
- Clean up old logs

**Monthly**:
- Review user feedback
- Plan feature updates
- Security audit

### Emergency Contacts

- **System Administrator**: [Your contact info]
- **Database Issues**: [DBA contact]
- **Network Issues**: [Network admin contact]
- **Business Owner**: Henry's on Market management

---

## 🎉 Congratulations!

You've successfully deployed Henry's SmartStock AI MVP! The system is now ready to help Henry's on Market modernize their inventory management with real-time tracking, automated alerts, and streamlined operations.

Remember to:
1. Change default passwords immediately
2. Set up regular backups
3. Monitor system health
4. Gather user feedback for future improvements

For questions or support, refer to the troubleshooting section or contact the development team.