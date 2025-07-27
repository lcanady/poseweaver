#!/bin/bash

# Fix API URL Configuration for External Access
# This script updates the frontend to use the correct API URL for external users

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

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    print_error "This script must be run as root (use sudo)"
    exit 1
fi

echo "🔧 Fixing API URL Configuration for External Access"
echo "================================================="
echo ""

# Step 1: Update ecosystem.config.js with correct API URL
print_status "1. Updating ecosystem.config.js..."

cd /root/poseweaver

# Backup current config
cp ecosystem.config.js ecosystem.config.js.backup

# Update the API URL in ecosystem config
sed -i "s|NEXT_PUBLIC_API_URL: 'http://localhost:5001'|NEXT_PUBLIC_API_URL: 'https://poseweaver.com/api'|g" ecosystem.config.js

print_success "Ecosystem configuration updated"

# Step 2: Check if SSL is set up, if not use HTTP
print_status "2. Checking SSL status..."

if [[ -f /etc/letsencrypt/live/poseweaver.com/fullchain.pem ]]; then
    print_success "SSL certificates found - using HTTPS"
    API_URL="https://poseweaver.com/api"
else
    print_warning "No SSL certificates found - using HTTP for now"
    sed -i "s|NEXT_PUBLIC_API_URL: 'https://poseweaver.com/api'|NEXT_PUBLIC_API_URL: 'http://poseweaver.com/api'|g" ecosystem.config.js
    API_URL="http://poseweaver.com/api"
fi

echo "API URL set to: $API_URL"

# Step 3: Rebuild frontend with new environment variables
print_status "3. Rebuilding frontend with new API URL..."

cd frontend

# Set the environment variable for build
export NEXT_PUBLIC_API_URL="$API_URL"

# Clean and rebuild
rm -rf .next
npm run build

if [[ $? -eq 0 ]]; then
    print_success "Frontend rebuilt successfully"
else
    print_error "Frontend build failed"
    exit 1
fi

cd ..

# Step 4: Restart PM2 services
print_status "4. Restarting PM2 services..."

pm2 restart ecosystem.config.js --env production
pm2 save

print_success "PM2 services restarted"

# Step 5: Test the configuration
print_status "5. Testing the new configuration..."

# Wait for services to start
sleep 5

# Test frontend
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200"; then
    print_success "Frontend is responding"
else
    print_warning "Frontend test inconclusive"
fi

# Test backend API
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/api/health | grep -q "200"; then
    print_success "Backend API is responding"
else
    print_warning "Backend API test failed"
fi

# Test through Nginx
if curl -s -o /dev/null -w "%{http_code}" http://localhost/api/health | grep -q "200"; then
    print_success "Nginx proxy is working"
else
    print_warning "Nginx proxy test failed"
fi

# Step 6: Show current configuration
print_status "6. Current configuration summary..."

echo ""
echo "📋 Configuration Summary:"
echo "========================"
echo "Frontend API URL: $API_URL"
echo "Frontend Port: 3000"
echo "Backend Port: 5001"
echo "Nginx Proxy: /api/* → http://127.0.0.1:5001/"
echo ""

# Step 7: Provide testing instructions
print_success "Configuration update completed!"
echo ""
print_status "🧪 Testing Instructions:"
echo ""
echo "1. Test from your local machine:"
echo "   curl -I http://poseweaver.com"
echo "   curl -I http://poseweaver.com/api/health"
echo ""
echo "2. Test in browser:"
echo "   Visit: http://poseweaver.com"
echo "   Open browser dev tools (F12) → Network tab"
echo "   Look for API calls to poseweaver.com/api/* (not localhost)"
echo ""
echo "3. If you have SSL certificates, update to HTTPS:"
echo "   The frontend will use: https://poseweaver.com/api"
echo ""

print_status "🔧 Next Steps:"
echo "1. Test your site from a different machine/network"
echo "2. Set up SSL certificates if not already done:"
echo "   certbot --nginx -d poseweaver.com -d www.poseweaver.com"
echo "3. After SSL setup, run this script again to use HTTPS URLs"
echo ""

print_status "📊 Monitor your services:"
echo "pm2 status"
echo "pm2 logs"
echo "pm2 monit"
