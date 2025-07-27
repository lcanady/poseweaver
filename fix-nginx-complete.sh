#!/bin/bash

# Complete Nginx Configuration Fix for PoseWeaver
# This script fixes all configuration issues and sets up proper Nginx config

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
NGINX_CONF="/etc/nginx/nginx.conf"

print_status "Fixing complete Nginx configuration for $DOMAIN..."

# Step 1: Add rate limiting zones to nginx.conf if not present
print_status "Adding rate limiting zones to nginx.conf..."
if ! grep -q "limit_req_zone" "$NGINX_CONF"; then
    # Find the http block and add rate limiting zones
    sed -i '/http {/a\\n    # Rate limiting zones for PoseWeaver\n    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;\n    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;\n' "$NGINX_CONF"
    print_success "Rate limiting zones added to nginx.conf"
else
    print_warning "Rate limiting zones already exist in nginx.conf"
fi

# Step 2: Create a clean, working Nginx configuration
print_status "Creating clean Nginx configuration..."

cat > "$CONFIG_FILE" << 'EOF'
# PoseWeaver Nginx Configuration
server {
    listen 80;
    server_name poseweaver.com www.poseweaver.com;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript;
    
    # Frontend (Next.js)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }
    
    # Backend API with rate limiting
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:5001/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5001/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static files with caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Block access to sensitive files
    location ~ /\. {
        deny all;
    }
    
    location ~ /(\.env|\.git|\.venv|logs/) {
        deny all;
    }
}
EOF

print_success "Clean Nginx configuration created"

# Step 3: Enable the site
print_status "Enabling the site..."
ln -sf "$CONFIG_FILE" "/etc/nginx/sites-enabled/$DOMAIN"

# Remove default site if it exists
if [[ -f /etc/nginx/sites-enabled/default ]]; then
    rm -f /etc/nginx/sites-enabled/default
    print_status "Removed default site"
fi

# Step 4: Test the configuration
print_status "Testing Nginx configuration..."
if nginx -t; then
    print_success "Nginx configuration is valid!"
    
    # Step 5: Start/reload Nginx
    print_status "Starting/reloading Nginx..."
    systemctl enable nginx
    systemctl start nginx 2>/dev/null || systemctl reload nginx
    print_success "Nginx is running"
    
    # Step 6: Show status
    print_success "Nginx setup completed successfully!"
    echo ""
    print_status "Current status:"
    systemctl status nginx --no-pager -l
    echo ""
    print_status "Your site should now be accessible at:"
    echo "http://poseweaver.com"
    echo "http://www.poseweaver.com"
    echo ""
    print_status "Next steps:"
    echo "1. Make sure your PM2 services are running:"
    echo "   pm2 start ecosystem.config.js --env production"
    echo ""
    echo "2. Test your site:"
    echo "   curl -I http://poseweaver.com"
    echo ""
    echo "3. Set up SSL certificates:"
    echo "   certbot --nginx -d poseweaver.com -d www.poseweaver.com"
    
else
    print_error "Nginx configuration test failed!"
    print_status "Checking configuration details..."
    nginx -t
    exit 1
fi
EOF
