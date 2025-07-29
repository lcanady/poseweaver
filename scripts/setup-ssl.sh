#!/bin/bash

# PoseWeaver SSL Certificate Setup Script
# This script sets up Let's Encrypt SSL certificates for production

set -e

DOMAIN="poseweaver.com"
EMAIL="admin@poseweaver.com"  # Change this to your email

echo "🔧 Setting up SSL certificates for $DOMAIN..."

# Create necessary directories
mkdir -p ./nginx/ssl
mkdir -p ./certbot/conf
mkdir -p ./certbot/www

# Check if running in development mode
if [[ "${NODE_ENV:-development}" == "development" ]]; then
    echo "⚠️  Development mode detected. SSL setup skipped."
    echo "   To enable HTTPS, set NODE_ENV=production and run this script."
    exit 0
fi

# Start nginx in HTTP-only mode for ACME challenge
echo "📦 Starting nginx for ACME challenge..."
docker-compose up -d nginx

# Wait for nginx to be ready
sleep 10

# Request SSL certificate
echo "🔐 Requesting SSL certificate from Let's Encrypt..."
docker run --rm \
    -v ./certbot/conf:/etc/letsencrypt \
    -v ./certbot/www:/var/www/certbot \
    certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN \
    -d www.$DOMAIN

# Enable HTTPS redirect in nginx config
echo "🔄 Enabling HTTPS redirect..."
sed -i 's/# location \/ {/location \/ {/' ./nginx/conf.d/poseweaver.conf
sed -i 's/#     return 301/    return 301/' ./nginx/conf.d/poseweaver.conf
sed -i 's/# }/}/' ./nginx/conf.d/poseweaver.conf

# Comment out development HTTP serving
sed -i 's/location \/ {/# location \/ {/' ./nginx/conf.d/poseweaver.conf
sed -i 's/        limit_req zone=general/    #     limit_req zone=general/' ./nginx/conf.d/poseweaver.conf
sed -i 's/        proxy_pass http:\/\/frontend;/    #     proxy_pass http:\/\/frontend;/' ./nginx/conf.d/poseweaver.conf
sed -i 's/        include \/etc\/nginx\/proxy_params;/    #     include \/etc\/nginx\/proxy_params;/' ./nginx/conf.d/poseweaver.conf
sed -i 's/    }/    # }/' ./nginx/conf.d/poseweaver.conf

# Restart nginx with SSL configuration
echo "🔄 Restarting nginx with SSL configuration..."
docker-compose restart nginx

# Set up certificate renewal
echo "⏰ Setting up certificate auto-renewal..."
(crontab -l 2>/dev/null; echo "0 12 * * * cd $(pwd) && docker run --rm -v ./certbot/conf:/etc/letsencrypt -v ./certbot/www:/var/www/certbot certbot/certbot renew --quiet && docker-compose restart nginx") | crontab -

echo "✅ SSL setup complete!"
echo "   Your site should now be available at https://$DOMAIN"
echo "   Certificates will auto-renew daily at 12:00 PM"
