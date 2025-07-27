#!/bin/bash

# Fix the Nginx configuration error on the server
# This script fixes the gzip_proxied directive issue

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

DOMAIN="poseweaver.com"
CONFIG_FILE="/etc/nginx/sites-available/$DOMAIN"

print_status "Fixing Nginx configuration for $DOMAIN..."

# Check if config file exists
if [[ ! -f "$CONFIG_FILE" ]]; then
    print_error "Nginx configuration file not found: $CONFIG_FILE"
    exit 1
fi

# Fix the gzip_proxied directive
print_status "Fixing gzip_proxied directive..."
sed -i 's/gzip_proxied expired no-cache no-store private must-revalidate auth;/gzip_proxied expired no-cache no-store private auth;/g' "$CONFIG_FILE"

print_success "Configuration fixed"

# Test the configuration
print_status "Testing Nginx configuration..."
if nginx -t; then
    print_success "Nginx configuration is now valid!"
    
    # Reload Nginx
    print_status "Reloading Nginx..."
    systemctl reload nginx
    print_success "Nginx reloaded successfully"
    
    print_status "You can now continue with the SSL setup by running:"
    echo "sudo ./setup-nginx-ssl.sh poseweaver.com your-email@example.com"
else
    print_error "Configuration is still invalid. Please check manually."
    exit 1
fi
