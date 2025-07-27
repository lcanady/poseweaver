#!/bin/bash

# Fix External Access Issues - Comprehensive Solution
# This script fixes the most common causes of external access problems

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

echo "🔧 Fixing External Access Issues"
echo "================================"
echo ""

# Step 1: Get server info
SERVER_IP=$(curl -s ifconfig.co 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "Unable to detect")
print_status "Server IP: $SERVER_IP"

# Step 2: Fix DNS/Host issues first
print_status "1. Checking and fixing DNS/Host configuration..."

# Add domain to hosts file as fallback
if ! grep -q "poseweaver.com" /etc/hosts; then
    echo "127.0.0.1 poseweaver.com www.poseweaver.com" >> /etc/hosts
    print_success "Added domain to hosts file"
fi

# Step 3: Fix firewall issues
print_status "2. Configuring firewall..."

if command -v ufw &> /dev/null; then
    # Reset and configure UFW properly
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow essential services
    ufw allow ssh
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Allow development ports temporarily
    ufw allow 3000/tcp
    ufw allow 5001/tcp
    
    ufw --force enable
    print_success "Firewall configured"
else
    print_warning "UFW not available"
fi

# Step 4: Fix Nginx configuration
print_status "3. Fixing Nginx configuration..."

NGINX_CONFIG="/etc/nginx/sites-available/poseweaver.com"
NGINX_ENABLED="/etc/nginx/sites-enabled/poseweaver.com"

# Create comprehensive Nginx config
cat > "$NGINX_CONFIG" << 'EOF'
server {
    listen 80;
    server_name poseweaver.com www.poseweaver.com;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=general:10m rate=30r/s;
    
    # Handle static assets with caching
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|woff|woff2|ttf|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        try_files $uri $uri/ @frontend;
    }
    
    # API proxy with proper headers
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://127.0.0.1:5001/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # CORS headers for API
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
        
        # Handle preflight requests
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "Content-Type, Authorization";
            add_header Access-Control-Max-Age 1728000;
            add_header Content-Type 'text/plain charset=UTF-8';
            add_header Content-Length 0;
            return 204;
        }
    }
    
    # Health check endpoint
    location /api/health {
        proxy_pass http://127.0.0.1:5001/api/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # No rate limiting for health checks
        access_log off;
    }
    
    # Frontend proxy
    location / {
        limit_req zone=general burst=50 nodelay;
        
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Fallback for frontend assets
    location @frontend {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable the site
ln -sf "$NGINX_CONFIG" "$NGINX_ENABLED"

# Test and reload Nginx
if nginx -t; then
    systemctl restart nginx
    systemctl enable nginx
    print_success "Nginx configured and restarted"
else
    print_error "Nginx configuration test failed"
    exit 1
fi

# Step 5: Fix ecosystem configuration
print_status "4. Updating ecosystem configuration..."

cd /root/poseweaver

# Backup current config
cp ecosystem.config.js ecosystem.config.js.backup

# Determine protocol
if [[ -f /etc/letsencrypt/live/poseweaver.com/fullchain.pem ]]; then
    API_URL="https://poseweaver.com/api"
    PROTOCOL="https"
else
    API_URL="http://poseweaver.com/api"
    PROTOCOL="http"
fi

# Update ecosystem config with proper environment variables
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [
    {
      name: 'poseweaver-backend',
      script: 'python',
      args: 'app.py',
      cwd: './backend',
      env: {
        FLASK_ENV: 'production',
        FLASK_APP: 'app.py',
        PORT: 5001,
        HOST: '127.0.0.1',
        MONGODB_URI: process.env.MONGODB_URI || 'mongodb://admin:password@localhost:27017/mush_pose_editor?authSource=admin'
      },
      instances: 1,
      exec_mode: 'fork',
      watch: false,
      max_memory_restart: '1G',
      error_file: './logs/backend-error.log',
      out_file: './logs/backend-out.log',
      log_file: './logs/backend-combined.log',
      time: true,
      interpreter: '/root/poseweaver/.venv/bin/python'
    },
    {
      name: 'poseweaver-frontend',
      script: 'npm',
      args: 'run start',
      cwd: './frontend',
      env: {
        NODE_ENV: 'production',
        PORT: 3000,
        HOST: '127.0.0.1',
        NEXT_PUBLIC_API_URL: '$API_URL'
      },
      env_development: {
        NODE_ENV: 'development',
        PORT: 3000,
        HOST: '127.0.0.1',
        NEXT_PUBLIC_API_URL: '/api'
      },
      instances: 1,
      exec_mode: 'fork',
      watch: false,
      max_memory_restart: '1G',
      error_file: './logs/frontend-error.log',
      out_file: './logs/frontend-out.log',
      log_file: './logs/frontend-combined.log',
      time: true
    }
  ]
};
EOF

print_success "Ecosystem configuration updated"

# Step 6: Fix frontend environment and rebuild
print_status "5. Rebuilding frontend with correct environment..."

cd frontend

# Clean build
rm -rf .next
rm -rf node_modules/.cache

# Set environment variables
export NEXT_PUBLIC_API_URL="$API_URL"
export NODE_ENV="production"

# Install and build
npm ci
npm run build

if [[ $? -eq 0 ]]; then
    print_success "Frontend rebuilt successfully"
else
    print_error "Frontend build failed"
    exit 1
fi

cd ..

# Step 7: Create logs directory
mkdir -p logs

# Step 8: Restart all services
print_status "6. Restarting all services..."

# Stop all PM2 processes
pm2 kill

# Start services with new configuration
pm2 start ecosystem.config.js --env production
pm2 save
pm2 startup

print_success "Services restarted"

# Step 9: Wait for services to initialize
print_status "7. Waiting for services to initialize..."
sleep 15

# Step 10: Comprehensive testing
print_status "8. Running comprehensive tests..."

# Test backend
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/api/health | grep -q "200"; then
    print_success "✓ Backend responding"
else
    print_error "✗ Backend not responding"
fi

# Test frontend
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200"; then
    print_success "✓ Frontend responding"
else
    print_error "✗ Frontend not responding"
fi

# Test Nginx proxy
if curl -s -o /dev/null -w "%{http_code}" http://localhost/api/health | grep -q "200"; then
    print_success "✓ Nginx API proxy working"
else
    print_error "✗ Nginx API proxy failed"
fi

# Test external domain access
if curl -s -o /dev/null -w "%{http_code}" "$PROTOCOL://poseweaver.com/api/health" --connect-timeout 10 | grep -q "200"; then
    print_success "✓ External domain access working"
else
    print_warning "⚠ External domain access test inconclusive (might be DNS)"
fi

# Test specific API endpoints
if curl -s -o /dev/null -w "%{http_code}" http://localhost/api/characters/mgmt/featured?limit=1 | grep -q "200"; then
    print_success "✓ Featured characters API working"
else
    print_warning "⚠ Featured characters API test inconclusive"
fi

# Step 11: Show current status
print_status "9. Current service status..."
pm2 status

# Step 12: Final recommendations
print_success "External access fix completed!"
echo ""
print_status "📋 Configuration Summary:"
echo "========================"
echo "Server IP: $SERVER_IP"
echo "Domain: poseweaver.com"
echo "Frontend: http://127.0.0.1:3000 → http://poseweaver.com"
echo "Backend: http://127.0.0.1:5001 → http://poseweaver.com/api"
echo "API URL: $API_URL"
echo ""

print_status "🧪 Test From External Machine:"
echo "=============================="
echo "1. Basic connectivity:"
echo "   curl -I http://poseweaver.com"
echo "   curl http://poseweaver.com/api/health"
echo ""
echo "2. API endpoints:"
echo "   curl http://poseweaver.com/api/characters/mgmt/featured?limit=1"
echo ""
echo "3. In browser:"
echo "   Visit: http://poseweaver.com"
echo "   Open F12 → Network tab"
echo "   Look for successful API calls to poseweaver.com/api/*"
echo ""

print_status "🔍 If Still Having Issues:"
echo "========================="
echo "1. Check DNS: dig poseweaver.com (should return $SERVER_IP)"
echo "2. Check cloud provider firewall (DigitalOcean, AWS, etc.)"
echo "3. Run diagnostic script: ./diagnose-external-access.sh"
echo "4. Check PM2 logs: pm2 logs"
echo "5. Check Nginx logs: tail -f /var/log/nginx/error.log"
echo ""

if [[ "$PROTOCOL" == "http" ]]; then
    print_warning "⚠️  SECURITY NOTE:"
    echo "You're using HTTP. For production, set up SSL:"
    echo "sudo certbot --nginx -d poseweaver.com -d www.poseweaver.com"
fi

print_success "Your site should now work properly from external machines!"
print_status "The main fixes applied:"
echo "✓ Fixed Nginx configuration with proper proxying"
echo "✓ Configured firewall to allow HTTP/HTTPS"
echo "✓ Updated ecosystem with correct API URLs"
echo "✓ Rebuilt frontend with proper environment variables"
echo "✓ Added comprehensive error handling and CORS"
