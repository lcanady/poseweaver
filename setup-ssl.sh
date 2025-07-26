#!/bin/bash

# PoseWeaver SSL Certificate Setup Script
# This script helps you obtain and configure SSL certificates for your PoseWeaver deployment

set -e

echo "🔒 PoseWeaver SSL Certificate Setup"
echo "=================================="

# Check if domain is provided
if [ -z "$1" ]; then
    echo "❌ Error: Please provide your domain name"
    echo "Usage: ./setup-ssl.sh your-domain.com"
    echo "Example: ./setup-ssl.sh poseweaver.example.com"
    exit 1
fi

DOMAIN=$1
EMAIL=${2:-"admin@$DOMAIN"}

echo "📋 Configuration:"
echo "   Domain: $DOMAIN"
echo "   Email: $EMAIL"
echo ""

# Create necessary directories
echo "📁 Creating SSL directories..."
mkdir -p ./certbot/conf
mkdir -p ./certbot/www

# Update nginx configuration with the domain
echo "🔧 Updating nginx configuration..."
sed "s/your-domain.com/$DOMAIN/g" nginx/conf.d/poseweaver.ssl.conf > nginx/conf.d/poseweaver.ssl.temp
mv nginx/conf.d/poseweaver.ssl.temp nginx/conf.d/poseweaver.ssl.conf

# Create initial nginx config for certificate challenge
echo "🌐 Creating initial nginx config for Let's Encrypt challenge..."
cat > nginx/conf.d/poseweaver.challenge.conf << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 200 "PoseWeaver SSL Setup - Certificate challenge server";
        add_header Content-Type text/plain;
    }
}
EOF

# Start nginx for certificate challenge
echo "🚀 Starting nginx for certificate challenge..."
docker-compose -f docker-compose.ssl.yml up -d nginx

# Wait for nginx to be ready
echo "⏳ Waiting for nginx to be ready..."
sleep 10

# Obtain SSL certificate
echo "🔐 Obtaining SSL certificate from Let's Encrypt..."
docker-compose -f docker-compose.ssl.yml run --rm certbot \
    certbot certonly --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN \
    -d www.$DOMAIN

# Check if certificate was obtained successfully
if [ ! -f "./certbot/conf/live/$DOMAIN/fullchain.pem" ]; then
    echo "❌ Failed to obtain SSL certificate"
    echo "Please check:"
    echo "1. Domain DNS points to this server"
    echo "2. Port 80 is accessible from the internet"
    echo "3. No firewall blocking HTTP traffic"
    exit 1
fi

echo "✅ SSL certificate obtained successfully!"

# Replace nginx config with SSL-enabled version
echo "🔄 Switching to SSL-enabled nginx configuration..."
rm nginx/conf.d/poseweaver.challenge.conf
cp nginx/conf.d/poseweaver.ssl.conf nginx/conf.d/poseweaver.conf

# Restart the full stack with SSL
echo "🔄 Restarting PoseWeaver with SSL enabled..."
docker-compose -f docker-compose.ssl.yml down
docker-compose -f docker-compose.ssl.yml up -d

echo ""
echo "🎉 SSL Setup Complete!"
echo "=================================="
echo "✅ Your PoseWeaver application is now available at:"
echo "   🌐 https://$DOMAIN"
echo "   🌐 https://www.$DOMAIN"
echo ""
echo "📋 Next Steps:"
echo "1. Test your SSL certificate: https://www.ssllabs.com/ssltest/"
echo "2. Set up automatic certificate renewal (already configured)"
echo "3. Update your DNS if needed"
echo ""
echo "🔄 Certificate Auto-Renewal:"
echo "   Certificates will automatically renew every 12 hours"
echo "   Check renewal status: docker-compose -f docker-compose.ssl.yml logs certbot"
echo ""
echo "🛠️  Management Commands:"
echo "   View logs: docker-compose -f docker-compose.ssl.yml logs"
echo "   Restart: docker-compose -f docker-compose.ssl.yml restart"
echo "   Stop: docker-compose -f docker-compose.ssl.yml down"
