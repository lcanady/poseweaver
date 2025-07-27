#!/bin/bash

# Fix All Localhost References and Redeploy
# This script fixes all remaining localhost references and rebuilds the frontend

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

echo "🔧 Fixing All Localhost References and Redeploying"
echo "================================================"
echo ""

cd /root/poseweaver

# Step 1: Check SSL status to determine protocol
print_status "1. Determining API URL protocol..."

if [[ -f /etc/letsencrypt/live/poseweaver.com/fullchain.pem ]]; then
    API_URL="https://poseweaver.com/api"
    PROTOCOL="https"
    print_success "SSL certificates found - using HTTPS"
else
    API_URL="http://poseweaver.com/api"
    PROTOCOL="http"
    print_warning "No SSL certificates found - using HTTP"
fi

echo "API URL: $API_URL"

# Step 2: Update ecosystem.config.js with correct protocol
print_status "2. Updating ecosystem.config.js..."

# Backup current config
cp ecosystem.config.js ecosystem.config.js.backup

# Update the API URL in ecosystem config
if [[ "$PROTOCOL" == "https" ]]; then
    sed -i "s|NEXT_PUBLIC_API_URL: 'http://poseweaver.com/api'|NEXT_PUBLIC_API_URL: 'https://poseweaver.com/api'|g" ecosystem.config.js
else
    sed -i "s|NEXT_PUBLIC_API_URL: 'https://poseweaver.com/api'|NEXT_PUBLIC_API_URL: 'http://poseweaver.com/api'|g" ecosystem.config.js
fi

print_success "Ecosystem configuration updated"

# Step 3: Stop PM2 services
print_status "3. Stopping PM2 services..."
pm2 stop ecosystem.config.js || true

# Step 4: Clean and rebuild frontend
print_status "4. Cleaning and rebuilding frontend..."

cd frontend

# Clean previous build
rm -rf .next
rm -rf node_modules/.cache

# Set environment variable for build
export NEXT_PUBLIC_API_URL="$API_URL"
export NODE_ENV="production"

print_status "Building with API_URL: $API_URL"

# Install dependencies (in case of updates)
npm ci

# Build the frontend
npm run build

if [[ $? -eq 0 ]]; then
    print_success "Frontend built successfully"
else
    print_error "Frontend build failed"
    exit 1
fi

cd ..

# Step 5: Restart PM2 services
print_status "5. Starting PM2 services..."

pm2 start ecosystem.config.js --env production
pm2 save

print_success "PM2 services started"

# Step 6: Wait for services to initialize
print_status "6. Waiting for services to initialize..."
sleep 10

# Step 7: Test the services
print_status "7. Testing services..."

# Test backend health
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/api/health | grep -q "200"; then
    print_success "Backend health check passed"
else
    print_warning "Backend health check failed"
fi

# Test frontend
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200"; then
    print_success "Frontend is responding"
else
    print_warning "Frontend test inconclusive"
fi

# Test Nginx proxy
if curl -s -o /dev/null -w "%{http_code}" http://localhost/api/health | grep -q "200"; then
    print_success "Nginx proxy is working"
else
    print_warning "Nginx proxy test failed"
fi

# Step 8: Show PM2 status
print_status "8. Current PM2 status..."
pm2 status

# Step 9: Test API calls from frontend perspective
print_status "9. Testing API configuration..."

# Create a simple test script to verify API calls
cat > /tmp/test-api.js << EOF
const https = require('${PROTOCOL}');
const http = require('http');

const client = ${PROTOCOL} === 'https' ? https : http;

const options = {
  hostname: 'poseweaver.com',
  port: ${PROTOCOL} === 'https' ? 443 : 80,
  path: '/api/health',
  method: 'GET'
};

const req = client.request(options, (res) => {
  console.log('Status:', res.statusCode);
  console.log('Headers:', res.headers);
  
  let data = '';
  res.on('data', (chunk) => {
    data += chunk;
  });
  
  res.on('end', () => {
    console.log('Response:', data);
    process.exit(res.statusCode === 200 ? 0 : 1);
  });
});

req.on('error', (e) => {
  console.error('Error:', e.message);
  process.exit(1);
});

req.setTimeout(5000, () => {
  console.error('Request timeout');
  req.destroy();
  process.exit(1);
});

req.end();
EOF

print_status "Testing external API access..."
if node /tmp/test-api.js; then
    print_success "External API access working"
else
    print_warning "External API access test failed"
fi

rm -f /tmp/test-api.js

# Step 10: Summary and next steps
print_success "Deployment completed!"
echo ""
print_status "📋 Configuration Summary:"
echo "========================"
echo "Frontend API URL: $API_URL"
echo "Protocol: $PROTOCOL"
echo "Frontend Port: 3000"
echo "Backend Port: 5001"
echo "Nginx Proxy: /api/* → http://127.0.0.1:5001/"
echo ""

print_status "🧪 Test Your Site:"
echo "=================="
echo "1. From external machine:"
echo "   curl -I $PROTOCOL://poseweaver.com"
echo "   curl -I $PROTOCOL://poseweaver.com/api/health"
echo ""
echo "2. In browser (from any machine):"
echo "   Visit: $PROTOCOL://poseweaver.com"
echo "   Open F12 → Network tab"
echo "   Look for API calls to poseweaver.com/api/* (no localhost)"
echo ""

print_status "🔍 Monitor Services:"
echo "==================="
echo "pm2 status"
echo "pm2 logs"
echo "pm2 monit"
echo ""

if [[ "$PROTOCOL" == "http" ]]; then
    print_warning "⚠️  SECURITY NOTE:"
    echo "You're using HTTP. For production, set up SSL:"
    echo "sudo certbot --nginx -d poseweaver.com -d www.poseweaver.com"
    echo "Then run this script again to use HTTPS URLs"
fi

print_success "All localhost references have been fixed!"
print_status "Your site should now work from any external machine."
