# PoseWeaver Backend VPS Deployment Guide

This guide walks you through deploying the PoseWeaver backend to a DigitalOcean VPS (Droplet) with full WebSocket support.

## Prerequisites

1. **DigitalOcean Account** with a VPS (Droplet)
2. **Domain name** (optional but recommended)
3. **MongoDB Atlas** or managed MongoDB instance
4. **Stripe Account** for payments
5. **Venice AI API Key**

## Step 1: VPS Setup

### 1.1 Create DigitalOcean Droplet

1. Log into DigitalOcean
2. Create a new Droplet:
   - **Image**: Ubuntu 22.04 LTS
   - **Size**: Basic plan, $12/month (2GB RAM, 1 vCPU) minimum
   - **Region**: Choose closest to your users
   - **Authentication**: SSH keys (recommended) or password
   - **Hostname**: poseweaver-backend

### 1.2 Initial Server Setup

SSH into your server:
```bash
ssh root@your_server_ip
```

Update system packages:
```bash
apt update && apt upgrade -y
```

Install required packages:
```bash
apt install -y python3 python3-pip python3-venv nginx supervisor git ufw
```

Create a non-root user:
```bash
adduser poseweaver
usermod -aG sudo poseweaver
su - poseweaver
```

## Step 2: Application Deployment

### 2.1 Clone Repository

```bash
cd /home/poseweaver
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name/backend
```

### 2.2 Python Environment Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

### 2.3 Environment Configuration

Create production environment file:
```bash
cp .env.example .env
nano .env
```

Configure your `.env` file:
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

## Step 3: Process Management with Supervisor

### 3.1 Create Supervisor Configuration

```bash
sudo nano /etc/supervisor/conf.d/poseweaver.conf
```

Add the following configuration:
```ini
[program:poseweaver]
command=/home/poseweaver/your-repo-name/backend/venv/bin/gunicorn --worker-class eventlet -w 1 --bind 127.0.0.1:5001 app:app
directory=/home/poseweaver/your-repo-name/backend
user=poseweaver
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/poseweaver.log
environment=PATH="/home/poseweaver/your-repo-name/backend/venv/bin"
```

### 3.2 Start the Application

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start poseweaver
sudo supervisorctl status poseweaver
```

## Step 4: Nginx Configuration

### 4.1 Create Nginx Site Configuration

```bash
sudo nano /etc/nginx/sites-available/poseweaver
```

Add the following configuration:
```nginx
server {
    listen 80;
    server_name your_domain.com www.your_domain.com;  # Replace with your domain or server IP

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # CORS headers for API
    add_header Access-Control-Allow-Origin "https://poseweaver.com" always;
    add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Origin, X-Requested-With, Content-Type, Accept, Authorization" always;
    add_header Access-Control-Allow-Credentials "true" always;

    # Handle preflight requests
    if ($request_method = 'OPTIONS') {
        add_header Access-Control-Allow-Origin "https://poseweaver.com";
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Origin, X-Requested-With, Content-Type, Accept, Authorization";
        add_header Access-Control-Allow-Credentials "true";
        add_header Content-Length 0;
        add_header Content-Type text/plain;
        return 204;
    }

    # Proxy to Flask application
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }

    # WebSocket specific location (Socket.IO)
    location /socket.io/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

### 4.2 Enable the Site

```bash
sudo ln -s /etc/nginx/sites-available/poseweaver /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Step 5: SSL Certificate (Optional but Recommended)

### 5.1 Install Certbot

```bash
sudo apt install certbot python3-certbot-nginx
```

### 5.2 Obtain SSL Certificate

```bash
sudo certbot --nginx -d your_domain.com -d www.your_domain.com
```

## Step 6: Firewall Configuration

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## Step 7: Update Frontend Configuration

Update your frontend environment to point to the new backend:

```bash
# In your frontend .env.local or environment variables
NEXT_PUBLIC_API_URL=https://your_domain.com
# or if no domain:
NEXT_PUBLIC_API_URL=http://your_server_ip
```

## Step 8: Testing

### 8.1 Test API Endpoints

```bash
curl https://your_domain.com/api/health
```

### 8.2 Test WebSocket Connection

The WebSocket should be accessible at:
```
wss://your_domain.com/socket.io/
```

## Step 9: Monitoring and Maintenance

### 9.1 View Application Logs

```bash
sudo tail -f /var/log/poseweaver.log
```

### 9.2 Restart Application

```bash
sudo supervisorctl restart poseweaver
```

### 9.3 Update Application

```bash
cd /home/poseweaver/your-repo-name
git pull origin main
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart poseweaver
```

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Check if supervisor is running: `sudo supervisorctl status poseweaver`
   - Check nginx configuration: `sudo nginx -t`
   - Check firewall: `sudo ufw status`

2. **CORS Errors**
   - Verify FRONTEND_URL in .env matches your frontend domain
   - Check nginx CORS headers configuration

3. **MongoDB Connection Issues**
   - Verify MONGODB_URI in .env
   - Check MongoDB Atlas IP whitelist (add 0.0.0.0/0 for testing)

4. **SSL Certificate Issues**
   - Renew certificate: `sudo certbot renew`
   - Check certificate status: `sudo certbot certificates`

## Security Considerations

1. **Environment Variables**: Never commit .env files to version control
2. **Firewall**: Only open necessary ports (22, 80, 443)
3. **Updates**: Regularly update system packages and dependencies
4. **Monitoring**: Set up monitoring for application health and security
5. **Backups**: Regular database backups
6. **SSL**: Always use HTTPS in production

## Performance Optimization

1. **Gunicorn Workers**: Adjust worker count based on CPU cores
2. **Nginx Caching**: Add caching for static assets
3. **Database**: Optimize MongoDB queries and indexes
4. **Monitoring**: Use tools like New Relic or DataDog for performance monitoring
