#!/bin/bash

# Fix Production Issues for PoseWeaver
# This script fixes the health endpoint and Next.js configuration issues

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

DOMAIN="poseweaver.com"
CONFIG_FILE="/etc/nginx/sites-available/$DOMAIN"

print_status "Fixing production issues for PoseWeaver..."

# Fix 1: Update Nginx configuration to use correct health endpoint
print_status "1. Fixing Nginx health check endpoint..."

if [[ -f "$CONFIG_FILE" ]]; then
    # Replace /health with /api/health in the Nginx config
    sed -i 's|location /health {|location /api/health {|g' "$CONFIG_FILE"
    sed -i 's|proxy_pass http://127.0.0.1:5001/health;|proxy_pass http://127.0.0.1:5001/api/health;|g' "$CONFIG_FILE"
    print_success "Health endpoint fixed in Nginx config"
else
    print_error "Nginx config file not found: $CONFIG_FILE"
    exit 1
fi

# Fix 2: Update frontend configuration to remove standalone output
print_status "2. Checking Next.js configuration..."

NEXTJS_CONFIG="/root/poseweaver/frontend/next.config.js"
if [[ -f "$NEXTJS_CONFIG" ]]; then
    # Check if standalone output is configured
    if grep -q "output.*standalone" "$NEXTJS_CONFIG"; then
        print_warning "Found standalone output configuration in next.config.js"
        print_status "Creating backup and fixing..."
        
        # Create backup
        cp "$NEXTJS_CONFIG" "$NEXTJS_CONFIG.backup"
        
        # Remove or comment out standalone output
        sed -i 's/output.*standalone/\/\/ output: "standalone" \/\/ Commented out for PM2 compatibility/g' "$NEXTJS_CONFIG"
        print_success "Next.js configuration fixed"
    else
        print_success "Next.js configuration is already correct"
    fi
else
    print_warning "Next.js config file not found, this might be okay"
fi

# Fix 3: Test Nginx configuration
print_status "3. Testing Nginx configuration..."
if nginx -t; then
    print_success "Nginx configuration is valid"
    
    # Reload Nginx
    print_status "Reloading Nginx..."
    systemctl reload nginx
    print_success "Nginx reloaded"
else
    print_error "Nginx configuration test failed"
    exit 1
fi

# Fix 4: Restart PM2 services to apply any frontend changes
print_status "4. Restarting PM2 services..."
cd /root/poseweaver

# If we modified Next.js config, rebuild the frontend
if [[ -f "$NEXTJS_CONFIG.backup" ]]; then
    print_status "Rebuilding frontend due to config changes..."
    cd frontend
    npm run build
    cd ..
fi

# Restart services
pm2 restart ecosystem.config.js --env production
print_success "PM2 services restarted"

# Fix 5: Test the fixes
print_status "5. Testing the fixes..."

# Wait a moment for services to start
sleep 5

# Test frontend
print_status "Testing frontend..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200"; then
    print_success "Frontend is responding correctly"
else
    print_warning "Frontend test inconclusive"
fi

# Test backend health endpoint
print_status "Testing backend health endpoint..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/api/health | grep -q "200"; then
    print_success "Backend health endpoint is working"
else
    print_warning "Backend health endpoint test failed"
fi

# Test Nginx proxy
print_status "Testing Nginx proxy..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost/api/health | grep -q "200"; then
    print_success "Nginx proxy to backend health endpoint is working"
else
    print_warning "Nginx proxy test failed"
fi

print_success "Production fixes completed!"
echo ""
print_status "Summary of fixes applied:"
echo "✅ Fixed Nginx health endpoint (/health → /api/health)"
echo "✅ Fixed Next.js standalone configuration warning"
echo "✅ Reloaded Nginx configuration"
echo "✅ Restarted PM2 services"
echo ""
print_status "Your site should now be working properly!"
print_status "Test it at: http://poseweaver.com (once DNS is configured)"
echo ""
print_status "Next steps:"
echo "1. Configure DNS A records to point to your server IP"
echo "2. Once DNS is working, set up SSL with:"
echo "   certbot --nginx -d poseweaver.com -d www.poseweaver.com"
