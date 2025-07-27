#!/bin/bash

# Nginx and SSL Setup Script for PoseWeaver
# This script sets up Nginx reverse proxy and SSL certificates with Let's Encrypt

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Function to detect OS
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        print_error "Cannot detect OS. This script supports Ubuntu/Debian and CentOS/RHEL."
        exit 1
    fi
    
    print_status "Detected OS: $OS $VER"
}

# Function to install Nginx
install_nginx() {
    print_status "Installing Nginx..."
    
    if [[ $OS == *"Ubuntu"* ]] || [[ $OS == *"Debian"* ]]; then
        apt update
        apt install -y nginx
        systemctl enable nginx
    elif [[ $OS == *"CentOS"* ]] || [[ $OS == *"Red Hat"* ]] || [[ $OS == *"Rocky"* ]]; then
        yum update -y
        yum install -y nginx
        systemctl enable nginx
    else
        print_error "Unsupported OS for automatic installation"
        exit 1
    fi
    
    print_success "Nginx installed successfully"
}

# Function to install Certbot
install_certbot() {
    print_status "Installing Certbot for Let's Encrypt..."
    
    if [[ $OS == *"Ubuntu"* ]] || [[ $OS == *"Debian"* ]]; then
        apt install -y certbot python3-certbot-nginx
    elif [[ $OS == *"CentOS"* ]] || [[ $OS == *"Red Hat"* ]] || [[ $OS == *"Rocky"* ]]; then
        yum install -y certbot python3-certbot-nginx
    else
        print_error "Unsupported OS for automatic Certbot installation"
        exit 1
    fi
    
    print_success "Certbot installed successfully"
}

# Function to create Nginx configuration
create_nginx_config() {
    local domain=$1
    local config_file="/etc/nginx/sites-available/$domain"
    local config_link="/etc/nginx/sites-enabled/$domain"
    
    print_status "Creating Nginx configuration for $domain..."
    
    # Create sites-available and sites-enabled directories if they don't exist (for CentOS/RHEL)
    mkdir -p /etc/nginx/sites-available
    mkdir -p /etc/nginx/sites-enabled
    
    # Ensure nginx.conf includes sites-enabled
    if ! grep -q "include /etc/nginx/sites-enabled" /etc/nginx/nginx.conf; then
        sed -i '/include \/etc\/nginx\/conf\.d\/\*\.conf;/a\    include /etc/nginx/sites-enabled/*;' /etc/nginx/nginx.conf
    fi
    
    cat > $config_file << EOF
# PoseWeaver Nginx Configuration
server {
    listen 80;
    server_name $domain www.$domain;
    
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
    
    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone \$binary_remote_addr zone=login:10m rate=1r/s;
    
    # Frontend (Next.js)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
    }
    
    # Backend API
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:5001/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5001/health;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Static files with caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)\$ {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host \$host;
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
    
    # Enable the site
    ln -sf $config_file $config_link
    
    # Remove default site if it exists
    if [[ -f /etc/nginx/sites-enabled/default ]]; then
        rm -f /etc/nginx/sites-enabled/default
    fi
    
    print_success "Nginx configuration created for $domain"
}

# Function to test Nginx configuration
test_nginx_config() {
    print_status "Testing Nginx configuration..."
    
    if nginx -t; then
        print_success "Nginx configuration is valid"
    else
        print_error "Nginx configuration test failed"
        exit 1
    fi
}

# Function to obtain SSL certificate
obtain_ssl_cert() {
    local domain=$1
    local email=$2
    
    print_status "Obtaining SSL certificate for $domain..."
    
    # Stop nginx temporarily for standalone mode
    systemctl stop nginx
    
    # Obtain certificate
    if certbot certonly --standalone --non-interactive --agree-tos --email $email -d $domain -d www.$domain; then
        print_success "SSL certificate obtained successfully"
    else
        print_error "Failed to obtain SSL certificate"
        systemctl start nginx
        exit 1
    fi
    
    # Start nginx again
    systemctl start nginx
}

# Function to update Nginx config for SSL
update_nginx_ssl_config() {
    local domain=$1
    local config_file="/etc/nginx/sites-available/$domain"
    
    print_status "Updating Nginx configuration for SSL..."
    
    cat > $config_file << EOF
# PoseWeaver Nginx Configuration with SSL
server {
    listen 80;
    server_name $domain www.$domain;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $domain www.$domain;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/$domain/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$domain/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/$domain/chain.pem;
    
    # SSL Security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
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
    
    # Rate limiting
    limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone \$binary_remote_addr zone=login:10m rate=1r/s;
    
    # Frontend (Next.js)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
    }
    
    # Backend API
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:5001/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:5001/health;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Static files with caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)\$ {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host \$host;
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
    
    print_success "Nginx SSL configuration updated"
}

# Function to setup auto-renewal
setup_auto_renewal() {
    print_status "Setting up SSL certificate auto-renewal..."
    
    # Create renewal hook script
    cat > /etc/letsencrypt/renewal-hooks/deploy/nginx-reload.sh << 'EOF'
#!/bin/bash
systemctl reload nginx
EOF
    
    chmod +x /etc/letsencrypt/renewal-hooks/deploy/nginx-reload.sh
    
    # Test renewal
    if certbot renew --dry-run; then
        print_success "SSL auto-renewal setup successfully"
    else
        print_warning "SSL auto-renewal test failed, but certificates were still obtained"
    fi
}

# Function to configure firewall
configure_firewall() {
    print_status "Configuring firewall..."
    
    if command -v ufw &> /dev/null; then
        # Ubuntu/Debian with UFW
        ufw --force enable
        ufw allow ssh
        ufw allow 'Nginx Full'
        ufw --force reload
        print_success "UFW firewall configured"
    elif command -v firewall-cmd &> /dev/null; then
        # CentOS/RHEL with firewalld
        systemctl enable firewalld
        systemctl start firewalld
        firewall-cmd --permanent --add-service=ssh
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --reload
        print_success "Firewalld configured"
    else
        print_warning "No supported firewall found. Please configure manually."
    fi
}

# Function to start and enable services
start_services() {
    print_status "Starting and enabling services..."
    
    systemctl enable nginx
    systemctl start nginx
    systemctl reload nginx
    
    print_success "Services started and enabled"
}

# Function to show final status
show_status() {
    local domain=$1
    
    print_success "Setup completed successfully!"
    echo ""
    print_status "Configuration Summary:"
    echo "Domain: $domain"
    echo "SSL Certificate: ✅ Enabled"
    echo "Auto-renewal: ✅ Configured"
    echo "Firewall: ✅ Configured"
    echo ""
    print_status "Your site should now be accessible at:"
    echo "https://$domain"
    echo "https://www.$domain"
    echo ""
    print_status "Useful commands:"
    echo "Check Nginx status: systemctl status nginx"
    echo "Check SSL certificates: certbot certificates"
    echo "Test Nginx config: nginx -t"
    echo "Reload Nginx: systemctl reload nginx"
    echo "View Nginx logs: journalctl -u nginx -f"
    echo ""
    print_status "Make sure your PM2 services are running:"
    echo "pm2 status"
    echo "pm2 start ecosystem.config.js --env production"
}

# Main setup function
main() {
    local domain=$1
    local email=$2
    
    if [[ -z "$domain" ]] || [[ -z "$email" ]]; then
        print_error "Usage: $0 <domain> <email>"
        echo "Example: $0 example.com admin@example.com"
        exit 1
    fi
    
    print_status "Starting Nginx and SSL setup for $domain"
    echo "========================================"
    
    check_root
    detect_os
    install_nginx
    install_certbot
    create_nginx_config "$domain"
    test_nginx_config
    start_services
    obtain_ssl_cert "$domain" "$email"
    update_nginx_ssl_config "$domain"
    test_nginx_config
    setup_auto_renewal
    configure_firewall
    start_services
    show_status "$domain"
}

# Run main function with arguments
main "$@"
