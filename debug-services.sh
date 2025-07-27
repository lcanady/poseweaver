#!/bin/bash

# Debug script to check PM2 services and network connectivity
# This helps troubleshoot reverse proxy issues

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo "🔍 PoseWeaver Service Debug Report"
echo "=================================="
echo ""

# Check PM2 status
print_status "1. Checking PM2 services..."
if command -v pm2 &> /dev/null; then
    pm2 status
    echo ""
    
    # Check if services are running
    if pm2 list | grep -q "poseweaver-frontend.*online"; then
        print_success "Frontend service is running"
    else
        print_error "Frontend service is NOT running"
    fi
    
    if pm2 list | grep -q "poseweaver-backend.*online"; then
        print_success "Backend service is running"
    else
        print_error "Backend service is NOT running"
    fi
else
    print_error "PM2 is not installed or not in PATH"
fi

echo ""

# Check if ports are listening
print_status "2. Checking port connectivity..."

# Check port 3000 (frontend)
if netstat -tln | grep -q ":3000 "; then
    print_success "Port 3000 is listening (Frontend)"
else
    print_error "Port 3000 is NOT listening (Frontend)"
fi

# Check port 5001 (backend)
if netstat -tln | grep -q ":5001 "; then
    print_success "Port 5001 is listening (Backend)"
else
    print_error "Port 5001 is NOT listening (Backend)"
fi

# Check port 80 (nginx)
if netstat -tln | grep -q ":80 "; then
    print_success "Port 80 is listening (Nginx)"
else
    print_error "Port 80 is NOT listening (Nginx)"
fi

echo ""

# Test local connectivity
print_status "3. Testing local service connectivity..."

# Test frontend
print_status "Testing frontend (port 3000)..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200\|301\|302"; then
    print_success "Frontend is responding"
else
    print_error "Frontend is NOT responding"
    print_status "Trying to connect to frontend..."
    curl -I http://localhost:3000 2>&1 || echo "Connection failed"
fi

# Test backend
print_status "Testing backend (port 5001)..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/health 2>/dev/null | grep -q "200"; then
    print_success "Backend health check passed"
else
    print_error "Backend health check failed"
    print_status "Trying to connect to backend..."
    curl -I http://localhost:5001 2>&1 || echo "Connection failed"
fi

echo ""

# Check Nginx status and config
print_status "4. Checking Nginx..."
if systemctl is-active --quiet nginx; then
    print_success "Nginx is running"
    
    # Test nginx config
    if nginx -t &>/dev/null; then
        print_success "Nginx configuration is valid"
    else
        print_error "Nginx configuration has errors"
        nginx -t
    fi
else
    print_error "Nginx is NOT running"
    print_status "Nginx status:"
    systemctl status nginx --no-pager -l
fi

echo ""

# Check logs for errors
print_status "5. Recent PM2 logs (last 20 lines)..."
if command -v pm2 &> /dev/null; then
    echo "--- Frontend logs ---"
    pm2 logs poseweaver-frontend --lines 10 --nostream 2>/dev/null || echo "No frontend logs available"
    echo ""
    echo "--- Backend logs ---"
    pm2 logs poseweaver-backend --lines 10 --nostream 2>/dev/null || echo "No backend logs available"
else
    print_warning "PM2 not available for log checking"
fi

echo ""

# Check disk space
print_status "6. System resources..."
echo "Disk usage:"
df -h / | tail -1
echo ""
echo "Memory usage:"
free -h
echo ""

# Recommendations
print_status "🔧 Troubleshooting Recommendations:"
echo ""

if ! pm2 list | grep -q "poseweaver-frontend.*online"; then
    echo "❌ Frontend not running:"
    echo "   cd /root/poseweaver && pm2 start ecosystem.config.js --env production"
    echo "   or: cd /root/poseweaver && pm2 restart poseweaver-frontend"
fi

if ! pm2 list | grep -q "poseweaver-backend.*online"; then
    echo "❌ Backend not running:"
    echo "   cd /root/poseweaver && pm2 start ecosystem.config.js --env production"
    echo "   or: cd /root/poseweaver && pm2 restart poseweaver-backend"
fi

if ! netstat -tln | grep -q ":3000 "; then
    echo "❌ Frontend port 3000 not listening:"
    echo "   Check if Next.js is built: cd /root/poseweaver/frontend && npm run build"
    echo "   Check PM2 logs: pm2 logs poseweaver-frontend"
fi

if ! systemctl is-active --quiet nginx; then
    echo "❌ Nginx not running:"
    echo "   sudo systemctl start nginx"
    echo "   sudo systemctl enable nginx"
fi

echo ""
print_status "Quick fix commands:"
echo "1. Restart all services: cd /root/poseweaver && pm2 restart ecosystem.config.js"
echo "2. View live logs: pm2 logs"
echo "3. Check detailed status: pm2 monit"
echo "4. Restart nginx: sudo systemctl restart nginx"
