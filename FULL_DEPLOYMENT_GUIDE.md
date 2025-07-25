# PoseWeaver Full Project Deployment Guide

This guide walks you through deploying the entire PoseWeaver project (backend + frontend) using the unified deployment script.

## 🚀 Quick Start

```bash
# Run the deployment script from your project root
./deploy_full_project.sh
```

The script will guide you through the entire process interactively.

## 📋 Prerequisites

### Before Running the Script

1. **DigitalOcean VPS** (Ubuntu 22.04, 2GB RAM minimum)
2. **SSH access** to your VPS with key-based authentication
3. **Domain name** (optional but recommended)
4. **Vercel account** and CLI installed
5. **Git repository** pushed to GitHub

### Required Information

Have these ready when running the script:

- **VPS IP address**
- **Domain name** (e.g., `api.poseweaver.com`)
- **SSH username** (usually `root`)

### Environment Variables

You'll need these for the backend `.env` file:

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

## 🔄 What the Script Does

### 1. Prerequisites Check
- ✅ Verifies Git, SSH, and Vercel CLI are installed
- ✅ Checks you're in a Git repository
- ✅ Installs missing dependencies

### 2. Information Gathering
- 📝 Prompts for VPS IP, domain, and SSH user
- 🔍 Tests VPS connection
- ✅ Validates all inputs

### 3. Repository Preparation
- 📦 Commits any uncommitted changes
- 🚀 Pushes latest code to GitHub
- 🔄 Ensures remote repository is up-to-date

### 4. Backend Deployment
- 🖥️ Downloads and runs VPS deployment script
- ⚙️ Configures Nginx, Supervisor, and Python environment
- 🔧 Sets up WebSocket support with Flask-SocketIO
- 📋 Prompts for environment variable configuration

### 5. Frontend Deployment
- 🌐 Deploys to Vercel with production settings
- 🔗 Configures API URL to point to your VPS
- ✅ Handles environment variable injection

### 6. Testing & Validation
- 🧪 Tests backend API health endpoint
- 🔍 Validates CORS configuration
- 🌐 Verifies WebSocket endpoint availability

## 📱 Usage Examples

### Basic Deployment
```bash
./deploy_full_project.sh
```

### With Custom Configuration
The script will prompt you for:
```
Enter your VPS IP address: 164.90.XXX.XXX
Enter your domain name: api.poseweaver.com
Enter VPS SSH user [root]: root
```

## 🔧 Manual Steps Required

### 1. Environment Configuration
When prompted, SSH into your VPS and configure:
```bash
ssh root@your_vps_ip
nano /home/poseweaver/poseweaver/backend/.env
```

Add all your production environment variables.

### 2. SSL Certificate (Optional)
```bash
ssh root@your_vps_ip
certbot --nginx -d your_domain.com
```

### 3. DNS Configuration
Point your domain to your VPS IP:
```
A record: api.poseweaver.com → your_vps_ip
```

## 🎯 Post-Deployment

### Verify Everything Works

1. **Backend API**: `curl http://your_domain.com/api/health`
2. **Frontend**: Visit `https://poseweaver.com`
3. **WebSocket**: Check browser console for connection success

### Useful Commands

```bash
# Check backend status
ssh root@your_vps_ip 'supervisorctl status poseweaver'

# View backend logs
ssh root@your_vps_ip 'tail -f /var/log/poseweaver.log'

# Restart backend
ssh root@your_vps_ip 'supervisorctl restart poseweaver'

# Update backend
ssh root@your_vps_ip '/home/poseweaver/poseweaver/update.sh'

# Redeploy frontend
cd frontend && vercel --prod
```

## 🐛 Troubleshooting

### Common Issues

#### 1. VPS Connection Failed
```bash
# Test SSH connection
ssh -v root@your_vps_ip

# Check SSH keys
ssh-add -l
```

#### 2. Backend Not Starting
```bash
# Check logs
ssh root@your_vps_ip 'tail -50 /var/log/poseweaver.log'

# Check environment variables
ssh root@your_vps_ip 'cat /home/poseweaver/poseweaver/backend/.env'
```

#### 3. WebSocket Connection Failed
- Verify Nginx configuration includes WebSocket support
- Check that Flask-SocketIO is running (not just Flask)
- Ensure CORS headers allow your frontend domain

#### 4. Frontend API Calls Failing
- Check `NEXT_PUBLIC_API_URL` in Vercel environment variables
- Verify CORS configuration on backend
- Test API endpoints directly with curl

### Debug Mode

To run with more verbose output:
```bash
bash -x ./deploy_full_project.sh
```

## 🔄 Updates and Maintenance

### Update Backend Code
```bash
# On your local machine
git add .
git commit -m "Backend updates"
git push origin main

# On VPS (or use the update script)
ssh root@your_vps_ip '/home/poseweaver/poseweaver/update.sh'
```

### Update Frontend Code
```bash
# On your local machine
cd frontend
vercel --prod
```

### Full Redeployment
```bash
# Run the deployment script again
./deploy_full_project.sh
```

## 📊 Monitoring

### Health Checks
- **Backend**: `http://your_domain.com/api/health`
- **Frontend**: Browser console for errors
- **WebSocket**: Browser network tab for connection status

### Log Monitoring
```bash
# Real-time backend logs
ssh root@your_vps_ip 'tail -f /var/log/poseweaver.log'

# Nginx logs
ssh root@your_vps_ip 'tail -f /var/log/nginx/error.log'
```

## 🔒 Security Considerations

1. **Environment Variables**: Never commit `.env` files
2. **SSH Keys**: Use key-based authentication only
3. **Firewall**: Only open necessary ports (22, 80, 443)
4. **SSL**: Always use HTTPS in production
5. **Updates**: Keep system packages updated

## 🎉 Success Indicators

After successful deployment, you should see:

✅ Backend API responding at your domain  
✅ Frontend deployed to Vercel  
✅ WebSocket connections working  
✅ CORS configured properly  
✅ SSL certificate installed (if configured)  

Your PoseWeaver application is now fully deployed and ready for users!
