#!/bin/bash

# Comprehensive External Access Diagnostics
# This script diagnoses why external machines see placeholder content while local works

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

echo "🔍 Comprehensive External Access Diagnostics"
echo "============================================"
echo ""

# Step 1: Get server information
print_status "1. Server Information"
echo "===================="
SERVER_IP=$(curl -s ifconfig.co 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "Unable to detect")
echo "Server IP: $SERVER_IP"
echo "Hostname: $(hostname)"
echo "Date: $(date)"
echo ""

# Step 2: Check DNS resolution
print_status "2. DNS Resolution Check"
echo "======================"
if command -v dig &> /dev/null; then
    echo "DNS A record for poseweaver.com:"
    dig +short poseweaver.com A || echo "DNS lookup failed"
    echo ""
    echo "DNS A record for www.poseweaver.com:"
    dig +short www.poseweaver.com A || echo "DNS lookup failed"
else
    echo "dig not available, using nslookup:"
    nslookup poseweaver.com || echo "DNS lookup failed"
fi
echo ""

# Step 3: Check what's actually listening
print_status "3. Port Listening Status"
echo "======================="
echo "Ports currently listening:"
netstat -tlnp | grep -E ":(80|443|3000|5001) " | while read line; do
    echo "  $line"
done
echo ""

# Step 4: Check PM2 status
print_status "4. PM2 Service Status"
echo "===================="
cd /root/poseweaver
pm2 status
echo ""

# Step 5: Check Nginx status and configuration
print_status "5. Nginx Configuration Check"
echo "============================"
if systemctl is-active --quiet nginx; then
    print_success "Nginx is running"
    
    # Check Nginx configuration
    echo "Nginx configuration test:"
    nginx -t
    echo ""
    
    # Show relevant Nginx config
    NGINX_CONFIG="/etc/nginx/sites-available/poseweaver.com"
    if [[ -f "$NGINX_CONFIG" ]]; then
        echo "Current Nginx configuration (key parts):"
        grep -A 20 -B 5 "location" "$NGINX_CONFIG" | head -50
    else
        print_error "Nginx config file not found: $NGINX_CONFIG"
    fi
else
    print_error "Nginx is not running"
fi
echo ""

# Step 6: Test local connectivity
print_status "6. Local Connectivity Tests"
echo "==========================="

# Test backend directly
print_status "Testing backend (localhost:5001)..."
BACKEND_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" http://localhost:5001/api/health 2>/dev/null || echo "FAILED")
if [[ "$BACKEND_RESPONSE" == *"HTTP_CODE:200"* ]]; then
    print_success "✓ Backend responding locally"
    echo "Response: ${BACKEND_RESPONSE%HTTP_CODE:*}"
else
    print_error "✗ Backend not responding locally"
    echo "Response: $BACKEND_RESPONSE"
fi

# Test frontend directly
print_status "Testing frontend (localhost:3000)..."
FRONTEND_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" -I http://localhost:3000 2>/dev/null || echo "FAILED")
if [[ "$FRONTEND_RESPONSE" == *"HTTP_CODE:200"* ]]; then
    print_success "✓ Frontend responding locally"
else
    print_error "✗ Frontend not responding locally"
    echo "Response: $FRONTEND_RESPONSE"
fi

# Test Nginx proxy
print_status "Testing Nginx proxy (localhost:80)..."
NGINX_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" -I http://localhost 2>/dev/null || echo "FAILED")
if [[ "$NGINX_RESPONSE" == *"HTTP_CODE:200"* ]]; then
    print_success "✓ Nginx proxy responding locally"
else
    print_error "✗ Nginx proxy not responding locally"
    echo "Response: $NGINX_RESPONSE"
fi

# Test API through Nginx
print_status "Testing API through Nginx (localhost/api/health)..."
API_NGINX_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" http://localhost/api/health 2>/dev/null || echo "FAILED")
if [[ "$API_NGINX_RESPONSE" == *"HTTP_CODE:200"* ]]; then
    print_success "✓ API through Nginx responding locally"
    echo "Response: ${API_NGINX_RESPONSE%HTTP_CODE:*}"
else
    print_error "✗ API through Nginx not responding locally"
    echo "Response: $API_NGINX_RESPONSE"
fi
echo ""

# Step 7: Test external connectivity
print_status "7. External Connectivity Tests"
echo "=============================="

if [[ "$SERVER_IP" != "Unable to detect" ]]; then
    # Test direct IP access
    print_status "Testing direct IP access ($SERVER_IP)..."
    IP_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" -I http://$SERVER_IP --connect-timeout 10 2>/dev/null || echo "FAILED")
    if [[ "$IP_RESPONSE" == *"HTTP_CODE:200"* ]]; then
        print_success "✓ Server accessible via IP"
    else
        print_error "✗ Server not accessible via IP"
        echo "Response: $IP_RESPONSE"
    fi
    
    # Test API via IP
    print_status "Testing API via IP ($SERVER_IP/api/health)..."
    IP_API_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" http://$SERVER_IP/api/health --connect-timeout 10 2>/dev/null || echo "FAILED")
    if [[ "$IP_API_RESPONSE" == *"HTTP_CODE:200"* ]]; then
        print_success "✓ API accessible via IP"
        echo "Response: ${IP_API_RESPONSE%HTTP_CODE:*}"
    else
        print_error "✗ API not accessible via IP"
        echo "Response: $IP_API_RESPONSE"
    fi
fi

# Test domain access
print_status "Testing domain access (poseweaver.com)..."
DOMAIN_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" -I http://poseweaver.com --connect-timeout 10 2>/dev/null || echo "FAILED")
if [[ "$DOMAIN_RESPONSE" == *"HTTP_CODE:200"* ]]; then
    print_success "✓ Domain accessible"
else
    print_error "✗ Domain not accessible"
    echo "Response: $DOMAIN_RESPONSE"
fi

# Test API via domain
print_status "Testing API via domain (poseweaver.com/api/health)..."
DOMAIN_API_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" http://poseweaver.com/api/health --connect-timeout 10 2>/dev/null || echo "FAILED")
if [[ "$DOMAIN_API_RESPONSE" == *"HTTP_CODE:200"* ]]; then
    print_success "✓ API accessible via domain"
    echo "Response: ${DOMAIN_API_RESPONSE%HTTP_CODE:*}"
else
    print_error "✗ API not accessible via domain"
    echo "Response: $DOMAIN_API_RESPONSE"
fi
echo ""

# Step 8: Test specific API endpoints that might be failing
print_status "8. Specific API Endpoint Tests"
echo "=============================="

# Test featured characters endpoint
print_status "Testing featured characters endpoint..."
FEATURED_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" http://localhost/api/characters/mgmt/featured?limit=1 2>/dev/null || echo "FAILED")
if [[ "$FEATURED_RESPONSE" == *"HTTP_CODE:200"* ]]; then
    print_success "✓ Featured characters endpoint working"
    echo "Response preview: ${FEATURED_RESPONSE%HTTP_CODE:*}" | head -c 200
    echo "..."
else
    print_error "✗ Featured characters endpoint failed"
    echo "Response: $FEATURED_RESPONSE"
fi

# Test user profile endpoint (if applicable)
print_status "Testing user profile endpoint..."
PROFILE_RESPONSE=$(curl -s -w "HTTP_CODE:%{http_code}" http://localhost/api/users/profile 2>/dev/null || echo "FAILED")
if [[ "$PROFILE_RESPONSE" == *"HTTP_CODE:401"* ]]; then
    print_success "✓ User profile endpoint responding (401 expected without auth)"
elif [[ "$PROFILE_RESPONSE" == *"HTTP_CODE:200"* ]]; then
    print_success "✓ User profile endpoint responding"
else
    print_error "✗ User profile endpoint failed"
    echo "Response: $PROFILE_RESPONSE"
fi
echo ""

# Step 9: Check environment variables in running processes
print_status "9. Environment Variable Check"
echo "============================"

# Check frontend environment
print_status "Frontend environment variables:"
pm2 show poseweaver-frontend | grep -A 10 -B 2 "env:" || echo "Could not retrieve frontend env"

# Check backend environment
print_status "Backend environment variables:"
pm2 show poseweaver-backend | grep -A 10 -B 2 "env:" || echo "Could not retrieve backend env"
echo ""

# Step 10: Check recent logs for errors
print_status "10. Recent Log Analysis"
echo "======================"

print_status "Recent frontend logs:"
pm2 logs poseweaver-frontend --lines 10 --nostream || echo "Could not retrieve frontend logs"

print_status "Recent backend logs:"
pm2 logs poseweaver-backend --lines 10 --nostream || echo "Could not retrieve backend logs"

print_status "Recent Nginx error logs:"
tail -n 10 /var/log/nginx/error.log 2>/dev/null || echo "Could not retrieve Nginx error logs"
echo ""

# Step 11: Check firewall status
print_status "11. Firewall Status"
echo "=================="
if command -v ufw &> /dev/null; then
    ufw status verbose
else
    echo "UFW not available"
fi
echo ""

# Step 12: Network interface check
print_status "12. Network Interface Check"
echo "==========================="
echo "Network interfaces:"
ip addr show | grep -E "(inet |UP|DOWN)" | head -10
echo ""

# Step 13: Generate diagnostic summary
print_status "13. Diagnostic Summary & Recommendations"
echo "========================================"

echo ""
print_status "🔍 DIAGNOSTIC RESULTS:"
echo ""

# Analyze results and provide recommendations
if [[ "$BACKEND_RESPONSE" == *"HTTP_CODE:200"* ]] && [[ "$FRONTEND_RESPONSE" == *"HTTP_CODE:200"* ]]; then
    if [[ "$DOMAIN_API_RESPONSE" != *"HTTP_CODE:200"* ]]; then
        print_error "❌ ISSUE FOUND: Services work locally but not externally"
        echo ""
        echo "🔧 LIKELY CAUSES:"
        echo "1. DNS not pointing to your server IP ($SERVER_IP)"
        echo "2. Firewall blocking external access"
        echo "3. Cloud provider security groups blocking ports"
        echo "4. Nginx not binding to external interfaces"
        echo ""
        echo "🚀 IMMEDIATE FIXES TO TRY:"
        echo "1. Check DNS: dig poseweaver.com (should return $SERVER_IP)"
        echo "2. Check firewall: ufw status"
        echo "3. Check cloud provider firewall settings"
        echo "4. Restart Nginx: systemctl restart nginx"
    else
        print_success "✅ External access working - issue might be specific to certain endpoints"
    fi
else
    print_error "❌ ISSUE FOUND: Services not working locally"
    echo ""
    echo "🔧 IMMEDIATE FIXES:"
    echo "1. Restart PM2 services: pm2 restart all"
    echo "2. Check PM2 logs: pm2 logs"
    echo "3. Rebuild frontend: cd frontend && npm run build"
fi

echo ""
print_status "📋 NEXT STEPS:"
echo "1. Fix any issues identified above"
echo "2. Test from external machine: curl -I http://poseweaver.com"
echo "3. Test API from external machine: curl http://poseweaver.com/api/health"
echo "4. Check browser console on external machine for JavaScript errors"
echo ""

print_status "🌐 EXTERNAL TESTING COMMANDS:"
echo "From another machine, run these commands:"
echo "curl -I http://poseweaver.com"
echo "curl http://poseweaver.com/api/health"
echo "curl http://poseweaver.com/api/characters/mgmt/featured?limit=1"
echo ""

print_success "Diagnostic completed! Review the results above to identify the issue."
