# 🐳 PoseWeaver Docker Production Deployment

This guide covers deploying PoseWeaver using Docker containers for production.

## 📋 Prerequisites

- Docker and Docker Compose installed
- At least 4GB RAM available
- Ports 80 and 443 available

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone https://github.com/lcanady/poseweaver.git
cd poseweaver
```

### 2. Configure Environment
```bash
# Copy and edit environment file
cp .env.production .env
nano .env

# Create backend environment file
cp backend/.env.example backend/.env
nano backend/.env
```

### 3. Deploy
```bash
# Run the production deployment script
./deploy-production.sh
```

## 🔧 Manual Deployment

If you prefer manual control:

```bash
# Build images
docker build -t poseweaver-backend:latest ./backend
docker build -t poseweaver-frontend:latest ./frontend

# Deploy with docker-compose
docker-compose -f docker-compose.prod.yml up -d
```

## 📊 Container Architecture

```
┌─────────────────┐    ┌─────────────────┐
│     Nginx       │    │    Frontend     │
│  (Port 80/443)  │────│   (Next.js)     │
│                 │    │   (Port 3000)   │
└─────────────────┘    └─────────────────┘
         │                       │
         │              ┌─────────────────┐
         └──────────────│     Backend     │
                        │    (Flask)      │
                        │   (Port 5000)   │
                        └─────────────────┘
                                 │
                        ┌─────────────────┐
                        │    MongoDB      │
                        │   (Port 27017)  │
                        └─────────────────┘
```

## 🔐 Environment Variables

### Required Backend Variables (.env and backend/.env)
```bash
# Database
MONGO_PASSWORD=your_secure_password

# Venice AI
VENICE_API_KEY=your_venice_api_key

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Application
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret
FRONTEND_URL=https://your-domain.com
NEXT_PUBLIC_API_URL=https://your-domain.com
```

## 🌐 Production URLs

After deployment, your application will be available at:
- **Frontend**: http://localhost (or your domain)
- **Backend API**: http://localhost/api/
- **Health Check**: http://localhost/health

## 🔧 Management Commands

```bash
# View container status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs frontend

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Stop all services
docker-compose -f docker-compose.prod.yml down

# Update and redeploy
git pull origin main
./deploy-production.sh
```

## 🔒 SSL/HTTPS Setup

### Using Let's Encrypt with Certbot

1. **Install Certbot in Nginx container**:
```bash
docker-compose -f docker-compose.prod.yml exec nginx sh
apk add certbot certbot-nginx
```

2. **Generate certificates**:
```bash
certbot --nginx -d your-domain.com
```

3. **Update nginx configuration** to use SSL (uncomment HTTPS section in nginx/conf.d/poseweaver.conf)

### Using Custom SSL Certificates

1. Place your certificates in `nginx/ssl/`:
   - `cert.pem` (certificate)
   - `key.pem` (private key)

2. Uncomment the HTTPS server block in `nginx/conf.d/poseweaver.conf`

3. Restart nginx:
```bash
docker-compose -f docker-compose.prod.yml restart nginx
```

## 📈 Monitoring and Logs

### Container Health Checks
All containers include health checks that run every 30 seconds:
- MongoDB: Database ping
- Backend: API health endpoint
- Frontend: HTTP response check
- Nginx: Configuration validation

### Log Locations
- Nginx logs: `nginx_logs` volume
- Application logs: `docker-compose logs`
- MongoDB logs: Container logs

### Monitoring Commands
```bash
# Real-time logs
docker-compose -f docker-compose.prod.yml logs -f

# Container resource usage
docker stats

# Health status
docker-compose -f docker-compose.prod.yml ps
```

## 🔄 Backup and Recovery

### Database Backup
```bash
# Create backup
docker-compose -f docker-compose.prod.yml exec mongodb mongodump --out /data/backup

# Restore backup
docker-compose -f docker-compose.prod.yml exec mongodb mongorestore /data/backup
```

### Full Application Backup
```bash
# Backup volumes
docker run --rm -v poseweaver_mongodb_data:/data -v $(pwd):/backup alpine tar czf /backup/mongodb-backup.tar.gz -C /data .
```

## 🚨 Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 80 and 443 are not in use
2. **Memory issues**: Ensure at least 4GB RAM available
3. **Environment variables**: Check all required variables are set
4. **Docker permissions**: Ensure user has Docker permissions

### Debug Commands
```bash
# Check container logs
docker-compose -f docker-compose.prod.yml logs [service-name]

# Execute commands in containers
docker-compose -f docker-compose.prod.yml exec backend bash
docker-compose -f docker-compose.prod.yml exec frontend sh

# Check network connectivity
docker-compose -f docker-compose.prod.yml exec backend curl http://frontend:3000
```

## 🔧 Performance Optimization

### Production Optimizations Included
- Multi-stage Docker builds
- Nginx gzip compression
- Static file caching
- Connection keep-alive
- Health checks and auto-restart
- Resource limits and reservations

### Additional Optimizations
- Use Docker Swarm or Kubernetes for scaling
- Implement Redis for session storage
- Use CDN for static assets
- Set up monitoring with Prometheus/Grafana

## 📞 Support

If you encounter issues:
1. Check the logs: `docker-compose -f docker-compose.prod.yml logs`
2. Verify environment variables are set correctly
3. Ensure all required ports are available
4. Check Docker and Docker Compose versions

---

**🚀 Your PoseWeaver application is now ready for production deployment with Docker!**
