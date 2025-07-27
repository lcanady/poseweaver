#!/bin/bash

# Fix Nginx API Proxy Configuration
# This script fixes the API proxy to preserve the /api path

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
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

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    print_error "This script must be run as root (use sudo)"
    exit 1
fi

echo "🔧 Fixing Nginx API Proxy Configuration"
echo "======================================="

NGINX_CONFIG="/etc/nginx/sites-available/poseweaver.com"

# Backup current config
cp "$NGINX_CONFIG" "$NGINX_CONFIG.backup"
print_status "Backed up current Nginx config"

# Fix the API proxy line
print_status "Fixing API proxy configuration..."

# Replace the problematic line
sed -i 's|proxy_pass http://127.0.0.1:5001/;|proxy_pass http://127.0.0.1:5001;|g' "$NGINX_CONFIG"

print_success "Fixed API proxy configuration"

# Test the configuration
print_status "Testing Nginx configuration..."
if nginx -t; then
    print_success "Nginx configuration is valid"
    
    # Reload Nginx
    print_status "Reloading Nginx..."
    systemctl reload nginx
    print_success "Nginx reloaded successfully"
else
    print_error "Nginx configuration test failed"
    print_status "Restoring backup..."
    cp "$NGINX_CONFIG.backup" "$NGINX_CONFIG"
    exit 1
fi

# Test the fix
print_status "Testing API endpoint..."
sleep 2

if curl -s -o /dev/null -w "%{http_code}" http://localhost/api/health | grep -q "200"; then
    print_success "✓ API health endpoint working through Nginx"
else
    print_error "✗ API health endpoint still not working"
fi

if curl -s -o /dev/null -w "%{http_code}" http://localhost/api/characters/mgmt/featured?limit=1 | grep -q "200"; then
    print_success "✓ Featured characters endpoint working through Nginx"
else
    print_error "✗ Featured characters endpoint still not working"
fi

print_success "Nginx API proxy fix completed!"
echo ""
print_status "What was fixed:"
echo "Before: /api/ → http://127.0.0.1:5001/ (strips /api)"
echo "After:  /api/ → http://127.0.0.1:5001  (preserves /api)"
echo ""
print_status "Your frontend should now be able to load images and data properly!"
