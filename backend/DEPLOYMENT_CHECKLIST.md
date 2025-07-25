# PoseWeaver Backend VPS Deployment Checklist

## Pre-Deployment Requirements

### ✅ 1. DigitalOcean VPS Setup
- [ ] Create DigitalOcean Droplet (Ubuntu 22.04 LTS)
- [ ] Minimum: 2GB RAM, 1 vCPU ($12/month)
- [ ] Configure SSH access
- [ ] Note down server IP address

### ✅ 2. Domain Configuration (Optional but Recommended)
- [ ] Purchase domain name
- [ ] Point A record to VPS IP address
- [ ] Wait for DNS propagation (up to 24 hours)

### ✅ 3. Required Service Accounts
- [ ] **MongoDB Atlas**: Database connection string
- [ ] **Venice AI**: API key for AI functionality
- [ ] **Stripe**: Secret key, publishable key, webhook secret
- [ ] **Frontend URL**: Your Vercel deployment URL

## Deployment Process

### Step 1: Initial Server Setup
```bash
# SSH into your server
ssh root@YOUR_SERVER_IP

# Download and run deployment script
curl -O https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/backend/deploy_vps.sh
chmod +x deploy_vps.sh
sudo ./deploy_vps.sh
```

### Step 2: Configure Environment Variables
```bash
# Edit environment file
sudo nano /home/poseweaver/poseweaver/backend/.env
```

**Required Variables:**
```bash
# Venice AI Configuration
VENICE_API_KEY=your_venice_api_key_here
VENICE_TIMEOUT=120

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False

# Application Configuration
SECRET_KEY=your_production_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here

# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/poseweaver?retryWrites=true&w=majority
MONGODB_DB=poseweaver

# Stripe Configuration
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key_here
STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# CORS Configuration
FRONTEND_URL=https://poseweaver.com

# Server Configuration
PORT=5001
```

### Step 3: Start Services
```bash
# Restart application with new configuration
sudo supervisorctl restart poseweaver

# Check application status
sudo supervisorctl status poseweaver

# View logs
sudo tail -f /var/log/poseweaver.log
```

### Step 4: SSL Certificate (Recommended)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your_domain.com -d www.your_domain.com
```

### Step 5: Test Deployment
```bash
# Test API health endpoint
curl https://your_domain.com/api/health

# Expected response:
# {"status": "healthy", "timestamp": "..."}
```

## Frontend Configuration Update

### Update Vercel Environment Variables
1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Update `NEXT_PUBLIC_API_URL`:
   ```
   NEXT_PUBLIC_API_URL=https://your_domain.com
   ```
3. Redeploy frontend:
   ```bash
   vercel --prod
   ```

## Post-Deployment Verification

### ✅ Backend Health Checks
- [ ] API health endpoint responds: `https://your_domain.com/api/health`
- [ ] WebSocket connection works: `wss://your_domain.com/socket.io/`
- [ ] CORS headers allow frontend domain
- [ ] SSL certificate is valid (if using HTTPS)

### ✅ Frontend Integration
- [ ] Frontend can connect to backend API
- [ ] WebSocket connections succeed
- [ ] Authentication flow works
- [ ] Pose enhancement functionality works
- [ ] Description writer functionality works

### ✅ Database Connectivity
- [ ] MongoDB connection successful
- [ ] User authentication works
- [ ] Character management works
- [ ] Subscription/payment processing works

## Monitoring and Maintenance

### Daily Checks
```bash
# Check application status
sudo supervisorctl status poseweaver

# Check recent logs
sudo tail -20 /var/log/poseweaver.log

# Check system resources
htop
df -h
```

### Weekly Maintenance
```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Update application
/home/poseweaver/poseweaver/update.sh

# Check SSL certificate expiry
sudo certbot certificates
```

## Troubleshooting

### Common Issues

#### 1. WebSocket Connection Failed
```bash
# Check if application is running
sudo supervisorctl status poseweaver

# Check nginx configuration
sudo nginx -t

# Restart services
sudo supervisorctl restart poseweaver
sudo systemctl restart nginx
```

#### 2. CORS Errors
- Verify `FRONTEND_URL` in `.env` matches your frontend domain
- Check nginx CORS headers configuration
- Ensure frontend is using correct backend URL

#### 3. Database Connection Issues
- Verify `MONGODB_URI` in `.env`
- Check MongoDB Atlas IP whitelist
- Test connection: `mongo "your_connection_string"`

#### 4. SSL Certificate Issues
```bash
# Renew certificate
sudo certbot renew

# Check certificate status
sudo certbot certificates
```

### Log Locations
- **Application logs**: `/var/log/poseweaver.log`
- **Nginx logs**: `/var/log/nginx/access.log`, `/var/log/nginx/error.log`
- **System logs**: `/var/log/syslog`

## Security Checklist

### ✅ Server Security
- [ ] Firewall configured (only ports 22, 80, 443 open)
- [ ] SSH key authentication enabled
- [ ] Root login disabled
- [ ] Regular security updates applied

### ✅ Application Security
- [ ] Environment variables secured (not in version control)
- [ ] HTTPS enabled with valid SSL certificate
- [ ] CORS properly configured
- [ ] Database connection encrypted
- [ ] API rate limiting enabled

### ✅ Monitoring
- [ ] Application health monitoring
- [ ] Log monitoring for errors
- [ ] Resource usage monitoring
- [ ] Security event monitoring

## Performance Optimization

### ✅ Server Optimization
- [ ] Gunicorn worker count optimized for CPU cores
- [ ] Nginx caching configured for static assets
- [ ] Database queries optimized
- [ ] Connection pooling configured

### ✅ Monitoring Tools
- [ ] Application performance monitoring (APM)
- [ ] Server monitoring (CPU, memory, disk)
- [ ] Database performance monitoring
- [ ] Error tracking and alerting

## Backup Strategy

### ✅ Database Backups
- [ ] MongoDB Atlas automated backups enabled
- [ ] Regular backup testing
- [ ] Backup retention policy defined

### ✅ Application Backups
- [ ] Code repository backed up (GitHub)
- [ ] Environment configuration documented
- [ ] Deployment process documented
- [ ] Recovery procedures tested

---

## Quick Reference Commands

```bash
# Application Management
sudo supervisorctl status poseweaver          # Check status
sudo supervisorctl restart poseweaver         # Restart app
sudo tail -f /var/log/poseweaver.log         # View logs

# Nginx Management
sudo nginx -t                                 # Test config
sudo systemctl restart nginx                  # Restart nginx
sudo systemctl status nginx                   # Check status

# SSL Certificate Management
sudo certbot certificates                     # Check certificates
sudo certbot renew                           # Renew certificates

# System Monitoring
htop                                          # System resources
df -h                                         # Disk usage
sudo ufw status                               # Firewall status

# Application Updates
/home/poseweaver/poseweaver/update.sh         # Update application
```

---

**🎉 Deployment Complete!**

Your PoseWeaver backend should now be running at:
- **API**: `https://your_domain.com`
- **WebSocket**: `wss://your_domain.com/socket.io/`
- **Health Check**: `https://your_domain.com/api/health`
