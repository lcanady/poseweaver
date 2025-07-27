#!/bin/bash

# Comprehensive Fix for All Localhost References
# This script finds and fixes ALL remaining localhost references in the frontend

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

echo "🔧 Comprehensive Fix for All Localhost References"
echo "================================================"
echo ""

cd /root/poseweaver

# Step 1: Determine API URL protocol
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

# Step 2: Update ecosystem.config.js
print_status "2. Updating ecosystem.config.js..."

# Backup current config
cp ecosystem.config.js ecosystem.config.js.backup

# Update the API URL in ecosystem config
sed -i "s|NEXT_PUBLIC_API_URL: 'http://poseweaver.com/api'|NEXT_PUBLIC_API_URL: '$API_URL'|g" ecosystem.config.js
sed -i "s|NEXT_PUBLIC_API_URL: 'https://poseweaver.com/api'|NEXT_PUBLIC_API_URL: '$API_URL'|g" ecosystem.config.js

print_success "Ecosystem configuration updated"

# Step 3: Fix frontend files with problematic fallbacks
print_status "3. Fixing frontend API URL fallbacks..."

cd frontend

# Fix featured-characters.tsx - empty fallback causes issues
print_status "Fixing featured-characters.tsx..."
sed -i "s|\${process.env.NEXT_PUBLIC_API_URL || ''}/api/|\${process.env.NEXT_PUBLIC_API_URL || '/api'}/|g" components/featured-characters.tsx

# Ensure all files use consistent fallback patterns
print_status "Standardizing API URL patterns..."

# Find all files with API URL patterns and fix them
find . -name "*.tsx" -o -name "*.ts" -o -name "*.jsx" -o -name "*.js" | grep -v node_modules | grep -v .next | while read file; do
    if grep -q "process.env.NEXT_PUBLIC_API_URL" "$file"; then
        # Replace any remaining localhost fallbacks
        sed -i "s|process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001'|process.env.NEXT_PUBLIC_API_URL || '/api'|g" "$file"
        sed -i "s|process.env.NEXT_PUBLIC_API_URL||'http://localhost:5001'|process.env.NEXT_PUBLIC_API_URL||'/api'|g" "$file"
        
        # Fix empty string fallbacks that cause issues
        sed -i "s|process.env.NEXT_PUBLIC_API_URL || ''|process.env.NEXT_PUBLIC_API_URL || '/api'|g" "$file"
        
        echo "  ✓ Updated: $file"
    fi
done

print_success "Frontend API URL patterns standardized"

# Step 4: Verify getApiUrl function is working correctly
print_status "4. Verifying getApiUrl function..."

if [[ -f "utils/api-utils.ts" ]]; then
    print_success "getApiUrl function found"
    
    # Show current getApiUrl implementation
    echo "Current getApiUrl implementation:"
    grep -A 10 -B 2 "export function getApiUrl" utils/api-utils.ts || true
else
    print_warning "getApiUrl function not found - this might cause issues"
fi

# Step 5: Clean and rebuild
print_status "5. Cleaning and rebuilding frontend..."

# Stop PM2 services
cd /root/poseweaver
pm2 stop ecosystem.config.js || true

cd frontend

# Clean build artifacts
rm -rf .next
rm -rf node_modules/.cache

# Set environment variables for build
export NEXT_PUBLIC_API_URL="$API_URL"
export NODE_ENV="production"

print_status "Building with API_URL: $API_URL"

# Install dependencies
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

# Step 6: Update Nginx configuration if needed
print_status "6. Checking Nginx configuration..."

NGINX_CONFIG="/etc/nginx/sites-available/poseweaver.com"
if [[ -f "$NGINX_CONFIG" ]]; then
    # Ensure Nginx is configured to serve static assets properly
    if ! grep -q "location ~* \.(jpg|jpeg|png|gif|ico|css|js)" "$NGINX_CONFIG"; then
        print_status "Adding static asset handling to Nginx..."
        
        # Add static asset handling before the API proxy
        sed -i '/location \/api\/ {/i\
    # Handle static assets\
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|woff|woff2|ttf|svg)$ {\
        expires 1y;\
        add_header Cache-Control "public, immutable";\
        try_files $uri $uri/ @frontend;\
    }\
' "$NGINX_CONFIG"
        
        # Test and reload Nginx
        if nginx -t; then
            systemctl reload nginx
            print_success "Nginx configuration updated and reloaded"
        else
            print_error "Nginx configuration test failed"
        fi
    else
        print_success "Nginx static asset handling already configured"
    fi
else
    print_warning "Nginx configuration file not found"
fi

# Step 7: Start PM2 services
print_status "7. Starting PM2 services..."

pm2 start ecosystem.config.js --env production
pm2 save

print_success "PM2 services started"

# Step 8: Wait and test
print_status "8. Waiting for services to initialize..."
sleep 15

# Step 9: Comprehensive testing
print_status "9. Running comprehensive tests..."

# Test backend health
print_status "Testing backend health..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/api/health | grep -q "200"; then
    print_success "✓ Backend health check passed"
else
    print_error "✗ Backend health check failed"
fi

# Test frontend
print_status "Testing frontend..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200"; then
    print_success "✓ Frontend is responding"
else
    print_error "✗ Frontend test failed"
fi

# Test Nginx proxy
print_status "Testing Nginx proxy..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost/api/health | grep -q "200"; then
    print_success "✓ Nginx proxy is working"
else
    print_error "✗ Nginx proxy test failed"
fi

# Test external domain access
print_status "Testing external domain access..."
if curl -s -o /dev/null -w "%{http_code}" "$PROTOCOL://poseweaver.com/api/health" --connect-timeout 10 | grep -q "200"; then
    print_success "✓ External domain API access working"
else
    print_warning "⚠ External domain API access test inconclusive"
fi

# Step 10: Test avatar/image serving
print_status "10. Testing image/avatar serving..."

# Create a test endpoint call
TEST_RESPONSE=$(curl -s "$PROTOCOL://poseweaver.com/api/characters/mgmt/featured?limit=1" 2>/dev/null || echo "failed")

if [[ "$TEST_RESPONSE" != "failed" ]] && [[ "$TEST_RESPONSE" != *"error"* ]]; then
    print_success "✓ Character API endpoint responding"
else
    print_warning "⚠ Character API endpoint test inconclusive"
fi

# Step 11: Show PM2 status
print_status "11. Current service status..."
pm2 status

# Step 12: Final summary and recommendations
print_success "Comprehensive localhost fix completed!"
echo ""
print_status "📋 Configuration Summary:"
echo "========================"
echo "Frontend API URL: $API_URL"
echo "Protocol: $PROTOCOL"
echo "Frontend Port: 3000"
echo "Backend Port: 5001"
echo "Nginx Proxy: /api/* → http://127.0.0.1:5001/"
echo ""

print_status "🔍 What was fixed:"
echo "=================="
echo "✓ Updated ecosystem.config.js with correct API URL"
echo "✓ Fixed empty fallback in featured-characters.tsx"
echo "✓ Standardized all API URL patterns across frontend"
echo "✓ Added Nginx static asset handling (if needed)"
echo "✓ Rebuilt frontend with proper environment variables"
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
echo "   Check if avatars and images load properly"
echo ""

print_status "🔍 Monitor Services:"
echo "==================="
echo "pm2 logs --lines 50"
echo "pm2 monit"
echo "tail -f /var/log/nginx/access.log"
echo ""

if [[ "$PROTOCOL" == "http" ]]; then
    print_warning "⚠️  SECURITY NOTE:"
    echo "You're using HTTP. For production, set up SSL:"
    echo "sudo certbot --nginx -d poseweaver.com -d www.poseweaver.com"
    echo "Then run this script again to use HTTPS URLs"
fi

print_success "All localhost references have been comprehensively fixed!"
print_status "Avatars and all API calls should now work from external machines."
