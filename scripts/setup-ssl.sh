#!/bin/bash

# SSL Setup Script for PoseWeaver
# This script helps you obtain SSL certificates using Certbot with Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 PoseWeaver SSL Certificate Setup${NC}"
echo "=================================================="

# Check if domain is provided
if [ -z "$1" ]; then
    echo -e "${RED}❌ Error: Domain name is required${NC}"
    echo "Usage: $0 <your-domain.com> [email@example.com]"
    echo "Example: $0 poseweaver.com admin@poseweaver.com"
    exit 1
fi

DOMAIN=$1
EMAIL=${2:-"admin@$DOMAIN"}

echo -e "${YELLOW}📋 Configuration:${NC}"
echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo ""

# Create necessary directories
echo -e "${BLUE}📁 Creating directories...${NC}"
mkdir -p ./certbot/conf
mkdir -p ./certbot/www

# Step 1: Start nginx without SSL first (for certificate validation)
echo -e "${BLUE}🚀 Step 1: Starting nginx for certificate validation...${NC}"

# Create temporary nginx config for certificate validation
cat > ./nginx/conf.d/temp-cert-validation.conf << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 200 'Certificate validation server running';
        add_header Content-Type text/plain;
    }
}
EOF

# Start only nginx and certbot for certificate generation
echo -e "${YELLOW}Starting nginx container for certificate validation...${NC}"
docker-compose -f docker-compose.ssl.yml up -d nginx

# Wait for nginx to be ready
echo -e "${YELLOW}Waiting for nginx to be ready...${NC}"
sleep 5

# Step 2: Obtain the certificate
echo -e "${BLUE}🔐 Step 2: Obtaining SSL certificate...${NC}"
docker-compose -f docker-compose.ssl.yml run --rm certbot \
    certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN \
    -d www.$DOMAIN

# Check if certificate was obtained successfully
if [ ! -f "./certbot/conf/live/$DOMAIN/fullchain.pem" ]; then
    echo -e "${RED}❌ Certificate generation failed!${NC}"
    echo "Please check the logs above and ensure:"
    echo "1. Your domain points to this server's IP address"
    echo "2. Port 80 is accessible from the internet"
    echo "3. No firewall is blocking the connection"
    exit 1
fi

echo -e "${GREEN}✅ Certificate obtained successfully!${NC}"

# Step 3: Update nginx configuration with your domain
echo -e "${BLUE}🔧 Step 3: Updating nginx configuration...${NC}"

# Replace placeholder domain in SSL config
sed -i.bak "s/your-domain.com/$DOMAIN/g" ./nginx/conf.d/poseweaver-ssl.conf

# Remove temporary validation config
rm -f ./nginx/conf.d/temp-cert-validation.conf

# Step 4: Restart with full SSL configuration
echo -e "${BLUE}🔄 Step 4: Restarting with SSL configuration...${NC}"
docker-compose -f docker-compose.ssl.yml down
docker-compose -f docker-compose.ssl.yml up -d

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 10

# Step 5: Test the setup
echo -e "${BLUE}🧪 Step 5: Testing SSL setup...${NC}"

# Test HTTP redirect
echo -e "${YELLOW}Testing HTTP to HTTPS redirect...${NC}"
HTTP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN/health || echo "000")
if [ "$HTTP_RESPONSE" = "301" ] || [ "$HTTP_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✅ HTTP redirect working${NC}"
else
    echo -e "${YELLOW}⚠️  HTTP redirect test returned: $HTTP_RESPONSE${NC}"
fi

# Test HTTPS
echo -e "${YELLOW}Testing HTTPS connection...${NC}"
HTTPS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" https://$DOMAIN/health || echo "000")
if [ "$HTTPS_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✅ HTTPS connection working${NC}"
else
    echo -e "${YELLOW}⚠️  HTTPS test returned: $HTTPS_RESPONSE${NC}"
fi

echo ""
echo -e "${GREEN}🎉 SSL Setup Complete!${NC}"
echo "=================================================="
echo -e "${BLUE}Your PoseWeaver application is now running with SSL:${NC}"
echo "• HTTP:  http://$DOMAIN (redirects to HTTPS)"
echo "• HTTPS: https://$DOMAIN"
echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo "1. Test your application at https://$DOMAIN"
echo "2. Certificate will auto-renew every 12 hours"
echo "3. Monitor logs with: docker-compose -f docker-compose.ssl.yml logs -f"
echo ""
echo -e "${BLUE}🔧 Useful Commands:${NC}"
echo "• View certificate info: docker-compose -f docker-compose.ssl.yml exec certbot certbot certificates"
echo "• Manual renewal: docker-compose -f docker-compose.ssl.yml exec certbot certbot renew"
echo "• Check nginx config: docker-compose -f docker-compose.ssl.yml exec nginx nginx -t"
