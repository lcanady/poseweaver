#!/bin/bash

# Fix Firewall and Network Access Issues
# This script diagnoses and fixes connection refused issues

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

echo "🔍 Network Access Troubleshooting for PoseWeaver"
echo "=============================================="
echo ""

# Step 1: Check current server IP
print_status "1. Checking server IP address..."
SERVER_IP=$(curl -s ifconfig.co 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "Unable to detect")
echo "Server IP: $SERVER_IP"
echo ""

# Step 2: Check what ports are listening
print_status "2. Checking listening ports..."
echo "Ports currently listening:"
netstat -tlnp | grep -E ":(80|443|3000|5001|22) " || echo "No standard web ports found listening"
echo ""

# Step 3: Check firewall status
print_status "3. Checking firewall configuration..."

# Check UFW (Ubuntu Firewall)
if command -v ufw &> /dev/null; then
    print_status "UFW Status:"
    ufw status verbose
    echo ""
    
    # Fix UFW if needed
    if ufw status | grep -q "Status: inactive"; then
        print_warning "UFW is inactive. Configuring firewall rules..."
        
        # Enable UFW with proper rules
        ufw --force reset
        ufw default deny incoming
        ufw default allow outgoing
        
        # Allow essential services
        ufw allow ssh
        ufw allow 22/tcp
        ufw allow 80/tcp
        ufw allow 443/tcp
        
        # Allow development ports (can be removed later)
        ufw allow 3000/tcp
        ufw allow 5001/tcp
        
        ufw --force enable
        print_success "UFW configured and enabled"
    else
        print_status "UFW is active. Checking rules..."
        
        # Ensure HTTP and HTTPS are allowed
        if ! ufw status | grep -q "80/tcp"; then
            ufw allow 80/tcp
            print_success "Added HTTP (port 80) rule"
        fi
        
        if ! ufw status | grep -q "443/tcp"; then
            ufw allow 443/tcp
            print_success "Added HTTPS (port 443) rule"
        fi
        
        # Reload UFW
        ufw reload
    fi
fi

# Check iptables
print_status "Current iptables rules:"
iptables -L -n | head -20
echo ""

# Step 4: Check if Nginx is binding to all interfaces
print_status "4. Checking Nginx binding..."
if systemctl is-active --quiet nginx; then
    print_success "Nginx is running"
    
    # Check if nginx is listening on all interfaces
    if netstat -tlnp | grep nginx | grep -q "0.0.0.0:80"; then
        print_success "Nginx is listening on all interfaces (0.0.0.0:80)"
    else
        print_warning "Nginx might not be listening on all interfaces"
        netstat -tlnp | grep nginx
    fi
else
    print_error "Nginx is not running"
    print_status "Starting Nginx..."
    systemctl start nginx
    systemctl enable nginx
fi

# Step 5: Test local connections
print_status "5. Testing local connections..."

# Test Nginx locally
if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200\|301\|302"; then
    print_success "Nginx responds locally"
else
    print_error "Nginx not responding locally"
fi

# Test from server IP
if [[ "$SERVER_IP" != "Unable to detect" ]]; then
    print_status "Testing connection to server IP..."
    if curl -s -o /dev/null -w "%{http_code}" http://$SERVER_IP --connect-timeout 5 | grep -q "200\|301\|302"; then
        print_success "Server responds on public IP"
    else
        print_error "Server not responding on public IP"
    fi
fi

# Step 6: Check cloud provider firewall (DigitalOcean)
print_status "6. Cloud provider considerations..."
echo "If you're using DigitalOcean, AWS, or other cloud providers:"
echo "- Check the cloud provider's firewall/security groups"
echo "- Ensure ports 80 and 443 are allowed in the cloud console"
echo "- DigitalOcean: Networking → Firewalls"
echo "- AWS: Security Groups"
echo ""

# Step 7: Advanced network diagnostics
print_status "7. Network interface information..."
ip addr show | grep -E "(inet |UP|DOWN)" | head -10
echo ""

# Step 8: Check for any blocking services
print_status "8. Checking for conflicting services..."
if systemctl is-active --quiet apache2; then
    print_warning "Apache2 is running - this might conflict with Nginx"
    echo "Consider stopping Apache2: systemctl stop apache2"
fi

# Step 9: Test specific ports
print_status "9. Testing port accessibility..."

# Function to test port
test_port() {
    local port=$1
    local service=$2
    
    if nc -z localhost $port 2>/dev/null; then
        print_success "Port $port ($service) is accessible locally"
    else
        print_error "Port $port ($service) is not accessible locally"
    fi
}

test_port 80 "HTTP"
test_port 443 "HTTPS"
test_port 3000 "Frontend"
test_port 5001 "Backend"

echo ""

# Step 10: Provide fix recommendations
print_status "🔧 Fix Recommendations:"
echo ""

if ! systemctl is-active --quiet nginx; then
    echo "❌ Start Nginx:"
    echo "   systemctl start nginx"
    echo "   systemctl enable nginx"
    echo ""
fi

if command -v ufw &> /dev/null && ufw status | grep -q "Status: inactive"; then
    echo "❌ Configure firewall:"
    echo "   ufw allow ssh"
    echo "   ufw allow 80/tcp"
    echo "   ufw allow 443/tcp"
    echo "   ufw --force enable"
    echo ""
fi

echo "❌ If still not working, check your cloud provider:"
echo "   - DigitalOcean: Networking → Firewalls"
echo "   - AWS: EC2 → Security Groups"
echo "   - Ensure ports 80 and 443 are allowed"
echo ""

echo "❌ Test external connectivity:"
echo "   From another machine: curl -I http://$SERVER_IP"
echo "   Online tool: https://www.whatsmyip.org/port-scanner/"
echo ""

# Step 11: Create a simple test page
print_status "Creating simple test page..."
cat > /var/www/html/test.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>PoseWeaver Server Test</title>
</head>
<body>
    <h1>PoseWeaver Server is Working!</h1>
    <p>If you can see this page, your server is accessible from the internet.</p>
    <p>Timestamp: $(date)</p>
</body>
</html>
EOF

# Replace the timestamp
sed -i "s/\$(date)/$(date)/" /var/www/html/test.html

print_success "Test page created at /var/www/html/test.html"
echo ""

print_status "🌐 Final Test URLs:"
echo "Local test: curl http://localhost/test.html"
echo "External test: http://$SERVER_IP/test.html"
echo "Domain test (once DNS works): http://poseweaver.com/test.html"
echo ""

print_success "Network troubleshooting completed!"
print_status "If you're still having issues, the problem is likely:"
print_status "1. Cloud provider firewall settings"
print_status "2. DNS not pointing to your server"
print_status "3. ISP blocking (rare)"
