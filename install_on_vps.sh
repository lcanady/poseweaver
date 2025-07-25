#!/bin/bash

# PoseWeaver VPS Complete Installation Script
# Run this script directly on your VPS to install everything
# Usage: curl -sSL https://raw.githubusercontent.com/lcanady/poseweaver/main/install_on_vps.sh | bash

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
APP_USER="poseweaver"
APP_DIR="/home/$APP_USER/poseweaver"
REPO_URL="https://github.com/lcanady/poseweaver.git"
DOMAIN=""
FRONTEND_URL="https://poseweaver.com"

echo -e "${PURPLE}🚀 PoseWeaver VPS Complete Installation${NC}"
echo -e "${CYAN}This script will install and configure everything on your VPS${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${YELLOW}📋 $1${NC}"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to print info
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to prompt for input
prompt_input() {
    local prompt="$1"
    local var_name="$2"
    local default_value="$3"
    
    if [ -n "$default_value" ]; then
        read -p "$(echo -e "${CYAN}$prompt [$default_value]: ${NC}")" input
        eval "$var_name=\"\${input:-$default_value}\""
    else
        read -p "$(echo -e "${CYAN}$prompt: ${NC}")" input
        eval "$var_name=\"$input\""
    fi
}

# Function to gather configuration
gather_config() {
    print_status "Gathering configuration..."
    echo ""
    
    prompt_input "Enter your domain name (e.g., api.poseweaver.com or leave empty for IP-only)" "DOMAIN"
    prompt_input "Enter your frontend URL" "FRONTEND_URL" "https://poseweaver.com"
    
    echo ""
    print_info "Configuration:"
    print_info "Domain: ${DOMAIN:-'Using IP address only'}"
    print_info "Frontend URL: $FRONTEND_URL"
    print_info "Repository: $REPO_URL"
    echo ""
}

# Check if running as root
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "Please run this script as root (use sudo)"
        exit 1
    fi
}

# Function to update system
update_system() {
    print_status "Updating system packages..."
    apt update && apt upgrade -y
    print_success "System packages updated"
}

# Function to install required packages
install_packages() {
    print_status "Installing required packages..."
    apt install -y python3 python3-pip python3-venv nginx supervisor git ufw curl htop
    print_success "Required packages installed"
}

# Function to create application user
create_user() {
    print_status "Creating application user..."
    if ! id "$APP_USER" &>/dev/null; then
        adduser --disabled-password --gecos "" $APP_USER
        usermod -aG sudo $APP_USER
        print_success "User $APP_USER created"
    else
        print_success "User $APP_USER already exists"
    fi
}

# Function to clone repository
clone_repository() {
    print_status "Setting up application directory..."
    sudo -u $APP_USER mkdir -p $APP_DIR
    cd $APP_DIR

    print_status "Cloning repository..."
    if [ ! -d ".git" ]; then
        sudo -u $APP_USER git clone $REPO_URL .
        print_success "Repository cloned"
    else
        sudo -u $APP_USER git pull origin main
        print_success "Repository updated"
    fi
}

# Function to setup Python environment
setup_python() {
    print_status "Setting up Python virtual environment..."
    cd $APP_DIR/backend
    
    sudo -u $APP_USER python3 -m venv venv
    sudo -u $APP_USER ./venv/bin/pip install --upgrade pip
    sudo -u $APP_USER ./venv/bin/pip install -r requirements.txt
    print_success "Python environment configured"
}

# Function to create environment file
create_env_file() {
    print_status "Creating environment configuration..."
    cd $APP_DIR/backend
    
    if [ ! -f ".env" ]; then
        sudo -u $APP_USER cp .env.example .env
        
        # Update basic configuration
        sudo -u $APP_USER sed -i "s|FLASK_ENV=development|FLASK_ENV=production|g" .env
        sudo -u $APP_USER sed -i "s|FLASK_DEBUG=True|FLASK_DEBUG=False|g" .env
        sudo -u $APP_USER sed -i "s|FRONTEND_URL=.*|FRONTEND_URL=$FRONTEND_URL|g" .env
        
        print_success "Environment file created"
        print_info "⚠️  IMPORTANT: You need to edit /home/$APP_USER/poseweaver/backend/.env"
        print_info "Add your API keys and database connection strings"
    else
        print_success "Environment file already exists"
    fi
}

# Function to create supervisor configuration
create_supervisor_config() {
    print_status "Creating Supervisor configuration..."
    cat > /etc/supervisor/conf.d/poseweaver.conf << EOF
[program:poseweaver]
command=$APP_DIR/backend/venv/bin/python app.py
directory=$APP_DIR/backend
user=$APP_USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/poseweaver.log
environment=PATH="$APP_DIR/backend/venv/bin"
EOF
    print_success "Supervisor configuration created"
}

# Function to create nginx configuration
create_nginx_config() {
    print_status "Creating Nginx configuration..."
    
    # Determine server name
    if [ -n "$DOMAIN" ]; then
        SERVER_NAME="$DOMAIN www.$DOMAIN"
    else
        SERVER_NAME="_"
    fi
    
    cat > /etc/nginx/sites-available/poseweaver << EOF
server {
    listen 80;
    server_name $SERVER_NAME;

    # Proxy to Flask application
    location / {
        # CORS headers for API
        add_header Access-Control-Allow-Origin "$FRONTEND_URL" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Origin, X-Requested-With, Content-Type, Accept, Authorization" always;
        add_header Access-Control-Allow-Credentials "true" always;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;

        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }

    # WebSocket specific location (Socket.IO)
    location /socket.io/ {
        # CORS headers for WebSocket
        add_header Access-Control-Allow-Origin "$FRONTEND_URL" always;
        add_header Access-Control-Allow-Credentials "true" always;

        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
    }
}
EOF

    # Enable the site
    ln -sf /etc/nginx/sites-available/poseweaver /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    print_success "Nginx configuration created"
}

# Function to configure firewall
configure_firewall() {
    print_status "Configuring firewall..."
    ufw --force enable
    ufw allow OpenSSH
    ufw allow 'Nginx Full'
    print_success "Firewall configured"
}

# Function to start services
start_services() {
    print_status "Starting services..."
    
    # Test nginx configuration
    nginx -t
    
    # Start services
    supervisorctl reread
    supervisorctl update
    supervisorctl start poseweaver
    systemctl restart nginx
    
    print_success "Services started"
}

# Function to create management scripts
create_management_scripts() {
    print_status "Creating management scripts..."
    
    # Update script
    cat > $APP_DIR/update.sh << 'EOF'
#!/bin/bash
cd /home/poseweaver/poseweaver
sudo -u poseweaver git pull origin main
cd backend
sudo -u poseweaver ./venv/bin/pip install -r requirements.txt
sudo supervisorctl restart poseweaver
echo "✅ Application updated successfully!"
EOF
    chmod +x $APP_DIR/update.sh
    chown $APP_USER:$APP_USER $APP_DIR/update.sh
    
    # Status script
    cat > $APP_DIR/status.sh << 'EOF'
#!/bin/bash
echo "🔍 PoseWeaver Status Check"
echo "=========================="
echo ""
echo "📊 Application Status:"
sudo supervisorctl status poseweaver
echo ""
echo "🌐 Nginx Status:"
sudo systemctl status nginx --no-pager -l
echo ""
echo "🔥 Recent Logs (last 10 lines):"
sudo tail -10 /var/log/poseweaver.log
echo ""
echo "💾 System Resources:"
free -h
df -h /
echo ""
echo "🌍 Network Test:"
curl -s http://localhost:5001/api/health || echo "❌ API not responding"
EOF
    chmod +x $APP_DIR/status.sh
    chown $APP_USER:$APP_USER $APP_DIR/status.sh
    
    # Logs script
    cat > $APP_DIR/logs.sh << 'EOF'
#!/bin/bash
echo "📋 Following PoseWeaver logs (Ctrl+C to exit)..."
sudo tail -f /var/log/poseweaver.log
EOF
    chmod +x $APP_DIR/logs.sh
    chown $APP_USER:$APP_USER $APP_DIR/logs.sh
    
    print_success "Management scripts created"
}

# Function to run tests
run_tests() {
    print_status "Running installation tests..."
    
    # Wait for application to start
    sleep 5
    
    # Test application status
    if supervisorctl status poseweaver | grep -q "RUNNING"; then
        print_success "✅ Application is running"
    else
        print_error "❌ Application is not running"
        print_info "Check logs: tail -f /var/log/poseweaver.log"
    fi
    
    # Test nginx
    if systemctl is-active --quiet nginx; then
        print_success "✅ Nginx is running"
    else
        print_error "❌ Nginx is not running"
    fi
    
    # Test API endpoint
    if curl -f -s http://localhost:5001/api/health > /dev/null; then
        print_success "✅ API health check passed"
    else
        print_error "❌ API health check failed"
        print_info "The application may still be starting up or needs environment configuration"
    fi
    
    print_success "Installation tests completed"
}

# Function to display summary
display_summary() {
    local server_ip=$(curl -s ifconfig.me || echo "your_server_ip")
    local api_url
    
    if [ -n "$DOMAIN" ]; then
        api_url="http://$DOMAIN"
    else
        api_url="http://$server_ip"
    fi
    
    echo ""
    echo -e "${PURPLE}🎉 Installation Complete!${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""
    echo -e "${CYAN}🌐 Your API is available at:${NC}"
    echo -e "  URL: $api_url"
    echo -e "  Health Check: $api_url/api/health"
    echo -e "  WebSocket: ws://${DOMAIN:-$server_ip}/socket.io/"
    echo ""
    echo -e "${CYAN}📁 Important Files:${NC}"
    echo -e "  Environment: /home/$APP_USER/poseweaver/backend/.env"
    echo -e "  Logs: /var/log/poseweaver.log"
    echo -e "  Nginx Config: /etc/nginx/sites-available/poseweaver"
    echo ""
    echo -e "${CYAN}🔧 Management Commands:${NC}"
    echo -e "  Status: $APP_DIR/status.sh"
    echo -e "  Update: $APP_DIR/update.sh"
    echo -e "  Logs: $APP_DIR/logs.sh"
    echo -e "  Restart: sudo supervisorctl restart poseweaver"
    echo ""
    echo -e "${YELLOW}⚠️  NEXT STEPS:${NC}"
    echo -e "  1. Edit environment file: nano /home/$APP_USER/poseweaver/backend/.env"
    echo -e "  2. Add your API keys (Venice AI, MongoDB, Stripe)"
    echo -e "  3. Restart application: sudo supervisorctl restart poseweaver"
    if [ -n "$DOMAIN" ]; then
        echo -e "  4. Set up SSL: certbot --nginx -d $DOMAIN"
        echo -e "  5. Point your domain DNS to this server IP: $server_ip"
    fi
    echo ""
    echo -e "${CYAN}🔍 Verify Installation:${NC}"
    echo -e "  curl $api_url/api/health"
    echo ""
    echo -e "${GREEN}🚀 Your PoseWeaver backend is ready!${NC}"
}

# Main installation flow
main() {
    echo -e "${PURPLE}Starting PoseWeaver installation...${NC}"
    echo ""
    
    check_root
    gather_config
    update_system
    install_packages
    create_user
    clone_repository
    setup_python
    create_env_file
    create_supervisor_config
    create_nginx_config
    configure_firewall
    start_services
    create_management_scripts
    run_tests
    display_summary
}

# Handle script interruption
trap 'print_error "Installation interrupted. You may need to clean up manually."; exit 1' INT TERM

# Run main function
main "$@"
