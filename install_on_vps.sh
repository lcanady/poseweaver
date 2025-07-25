#!/bin/bash

# PoseWeaver Complete DigitalOcean Droplet Installation Script
# This script installs and activates the entire PoseWeaver project
# Run as: sudo ./install_on_vps.sh

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
DOMAIN="poseweaver.com"
FRONTEND_URL="https://poseweaver.com"
SERVER_IP=$(curl -s ifconfig.me || echo "your_server_ip")

echo -e "${PURPLE}🚀 PoseWeaver Complete DigitalOcean Installation${NC}"
echo -e "${CYAN}Installing and activating the entire PoseWeaver project...${NC}"
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

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root (use sudo)"
    exit 1
fi

# Function to update system
update_system() {
    print_status "Updating system packages..."
    apt update && apt upgrade -y
    print_success "System packages updated"
}

# Function to install required packages
install_packages() {
    print_status "Installing required packages..."
    apt install -y python3 python3-pip python3-venv nginx supervisor git ufw curl htop certbot python3-certbot-nginx nodejs npm
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

# Function to setup Python environment for backend
setup_backend() {
    print_status "Setting up Python backend environment..."
    cd $APP_DIR/backend
    
    # Create virtual environment
    sudo -u $APP_USER python3 -m venv venv
    sudo -u $APP_USER ./venv/bin/pip install --upgrade pip
    sudo -u $APP_USER ./venv/bin/pip install -r requirements.txt
    
    print_success "Python backend environment configured"
}

# Function to create environment file
create_env_file() {
    print_status "Creating backend environment configuration..."
    cd $APP_DIR/backend
    
    if [ ! -f ".env" ]; then
        sudo -u $APP_USER cp .env.example .env
        
        # Update basic configuration
        sudo -u $APP_USER sed -i "s|FLASK_ENV=development|FLASK_ENV=production|g" .env
        sudo -u $APP_USER sed -i "s|FLASK_DEBUG=True|FLASK_DEBUG=False|g" .env
        sudo -u $APP_USER sed -i "s|FRONTEND_URL=.*|FRONTEND_URL=$FRONTEND_URL|g" .env
        sudo -u $APP_USER sed -i "s|PORT=.*|PORT=5001|g" .env
        
        print_success "Backend environment file created"
        print_info "⚠️  IMPORTANT: You need to edit /home/$APP_USER/poseweaver/backend/.env"
        print_info "Add your API keys: VENICE_API_KEY, MONGODB_URI, STRIPE keys"
    else
        print_success "Backend environment file already exists"
    fi
}

# Function to setup frontend environment
setup_frontend() {
    print_status "Setting up frontend environment..."
    cd $APP_DIR/frontend
    
    # Install dependencies
    sudo -u $APP_USER npm install
    
    # Create frontend environment file
    if [ ! -f ".env.local" ]; then
        sudo -u $APP_USER cat > .env.local << EOFFRONT
NEXT_PUBLIC_API_URL=http://$SERVER_IP
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_51Ro3ocPiG9G5Z3VQpKYXwpM0pQ5lGVXXvdhOxEf2HgFoPWQyd2k8V3ApHxj3dqBeBJ51hxvuxjEbNlucnSjigTA200EiKVrmt4
EOFFRONT
        print_success "Frontend environment file created"
    else
        print_success "Frontend environment file already exists"
    fi
    
    # Build frontend
    print_status "Building frontend..."
    sudo -u $APP_USER npm run build
    print_success "Frontend built successfully"
}

# Function to create supervisor configuration
create_supervisor_config() {
    print_status "Creating Supervisor configuration..."
    
    # Backend supervisor config
    cat > /etc/supervisor/conf.d/poseweaver-backend.conf << EOFBACKEND
[program:poseweaver-backend]
command=$APP_DIR/backend/venv/bin/python app.py
directory=$APP_DIR/backend
user=$APP_USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/poseweaver-backend.log
environment=PATH="$APP_DIR/backend/venv/bin"
EOFBACKEND

    # Frontend supervisor config
    cat > /etc/supervisor/conf.d/poseweaver-frontend.conf << EOFFRONTEND
[program:poseweaver-frontend]
command=npm start
directory=$APP_DIR/frontend
user=$APP_USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/poseweaver-frontend.log
environment=PATH="/usr/bin:/usr/local/bin",NODE_ENV="production",PORT="3000"
EOFFRONTEND

    print_success "Supervisor configurations created"
}

# Function to create nginx configuration
create_nginx_config() {
    print_status "Creating Nginx configuration..."
    
    cat > /etc/nginx/sites-available/poseweaver << EOFNGINX
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN $SERVER_IP _;

    # Frontend (Next.js)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support for Next.js dev
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Backend API
    location /api/ {
        # CORS headers
        add_header Access-Control-Allow-Origin "*" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Origin, X-Requested-With, Content-Type, Accept, Authorization" always;
        add_header Access-Control-Allow-Credentials "true" always;

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
        # CORS headers
        add_header Access-Control-Allow-Origin "*" always;
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
EOFNGINX

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
    ufw allow 3000  # Frontend
    ufw allow 5001  # Backend
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
    supervisorctl start poseweaver-backend
    supervisorctl start poseweaver-frontend
    systemctl restart nginx
    
    print_success "Services started"
}

# Function to create management scripts
create_management_scripts() {
    print_status "Creating management scripts..."
    
    # Update script
    cat > $APP_DIR/update.sh << 'EOFUPDATE'
#!/bin/bash
cd /home/poseweaver/poseweaver
sudo -u poseweaver git pull origin main

# Update backend
cd backend
sudo -u poseweaver ./venv/bin/pip install -r requirements.txt

# Update frontend
cd ../frontend
sudo -u poseweaver npm install
sudo -u poseweaver npm run build

# Restart services
sudo supervisorctl restart poseweaver-backend
sudo supervisorctl restart poseweaver-frontend

echo "✅ Application updated successfully!"
EOFUPDATE
    chmod +x $APP_DIR/update.sh
    chown $APP_USER:$APP_USER $APP_DIR/update.sh
    
    # Status script
    cat > $APP_DIR/status.sh << 'EOFSTATUS'
#!/bin/bash
echo "🔍 PoseWeaver Status Check"
echo "=========================="
echo ""
echo "📊 Application Status:"
sudo supervisorctl status poseweaver-backend poseweaver-frontend
echo ""
echo "🌐 Nginx Status:"
sudo systemctl status nginx --no-pager -l
echo ""
echo "🔥 Recent Backend Logs (last 10 lines):"
sudo tail -10 /var/log/poseweaver-backend.log
echo ""
echo "🔥 Recent Frontend Logs (last 10 lines):"
sudo tail -10 /var/log/poseweaver-frontend.log
echo ""
echo "💾 System Resources:"
free -h
df -h /
echo ""
echo "🌍 Network Tests:"
curl -s http://localhost:5001/api/health || echo "❌ Backend API not responding"
curl -s http://localhost:3000 > /dev/null && echo "✅ Frontend responding" || echo "❌ Frontend not responding"
EOFSTATUS
    chmod +x $APP_DIR/status.sh
    chown $APP_USER:$APP_USER $APP_DIR/status.sh
    
    # Logs script
    cat > $APP_DIR/logs.sh << 'EOFLOGS'
#!/bin/bash
echo "📋 PoseWeaver Logs (Ctrl+C to exit)"
echo "Choose which logs to view:"
echo "1) Backend logs"
echo "2) Frontend logs"
echo "3) Both (split view)"
read -p "Enter choice [1-3]: " choice

case $choice in
    1) sudo tail -f /var/log/poseweaver-backend.log ;;
    2) sudo tail -f /var/log/poseweaver-frontend.log ;;
    3) sudo tail -f /var/log/poseweaver-backend.log /var/log/poseweaver-frontend.log ;;
    *) echo "Invalid choice" ;;
esac
EOFLOGS
    chmod +x $APP_DIR/logs.sh
    chown $APP_USER:$APP_USER $APP_DIR/logs.sh
    
    # Restart script
    cat > $APP_DIR/restart.sh << 'EOFRESTART'
#!/bin/bash
echo "🔄 Restarting PoseWeaver services..."
sudo supervisorctl restart poseweaver-backend
sudo supervisorctl restart poseweaver-frontend
sudo systemctl restart nginx
echo "✅ All services restarted!"
EOFRESTART
    chmod +x $APP_DIR/restart.sh
    chown $APP_USER:$APP_USER $APP_DIR/restart.sh
    
    print_success "Management scripts created"
}

# Function to run tests
run_tests() {
    print_status "Running installation tests..."
    
    # Wait for services to start
    sleep 10
    
    # Test backend
    if supervisorctl status poseweaver-backend | grep -q "RUNNING"; then
        print_success "✅ Backend is running"
    else
        print_error "❌ Backend is not running"
    fi
    
    # Test frontend
    if supervisorctl status poseweaver-frontend | grep -q "RUNNING"; then
        print_success "✅ Frontend is running"
    else
        print_error "❌ Frontend is not running"
    fi
    
    # Test nginx
    if systemctl is-active --quiet nginx; then
        print_success "✅ Nginx is running"
    else
        print_error "❌ Nginx is not running"
    fi
    
    # Test API endpoint
    if curl -f -s http://localhost:5001/api/health > /dev/null; then
        print_success "✅ Backend API health check passed"
    else
        print_error "❌ Backend API health check failed"
    fi
    
    # Test frontend
    if curl -f -s http://localhost:3000 > /dev/null; then
        print_success "✅ Frontend health check passed"
    else
        print_error "❌ Frontend health check failed"
    fi
    
    print_success "Installation tests completed"
}

# Function to display summary
display_summary() {
    echo ""
    echo -e "${PURPLE}🎉 PoseWeaver Installation Complete!${NC}"
    echo -e "${GREEN}======================================${NC}"
    echo ""
    echo -e "${CYAN}🌐 Your application is available at:${NC}"
    echo -e "  Frontend: http://$SERVER_IP (Full App)"
    echo -e "  Backend API: http://$SERVER_IP/api/"
    echo -e "  WebSocket: ws://$SERVER_IP/socket.io/"
    if [ "$DOMAIN" != "poseweaver.com" ]; then
        echo -e "  Domain: http://$DOMAIN (when DNS is configured)"
    fi
    echo ""
    echo -e "${CYAN}📁 Important Files:${NC}"
    echo -e "  Backend Environment: /home/$APP_USER/poseweaver/backend/.env"
    echo -e "  Frontend Environment: /home/$APP_USER/poseweaver/frontend/.env.local"
    echo -e "  Backend Logs: /var/log/poseweaver-backend.log"
    echo -e "  Frontend Logs: /var/log/poseweaver-frontend.log"
    echo -e "  Nginx Config: /etc/nginx/sites-available/poseweaver"
    echo ""
    echo -e "${CYAN}🔧 Management Commands:${NC}"
    echo -e "  Status: $APP_DIR/status.sh"
    echo -e "  Update: $APP_DIR/update.sh"
    echo -e "  Logs: $APP_DIR/logs.sh"
    echo -e "  Restart: $APP_DIR/restart.sh"
    echo -e "  Manual restart: supervisorctl restart poseweaver-backend poseweaver-frontend"
    echo ""
    echo -e "${YELLOW}⚠️  NEXT STEPS:${NC}"
    echo -e "  1. Edit backend environment: nano /home/$APP_USER/poseweaver/backend/.env"
    echo -e "  2. Add your API keys (Venice AI, MongoDB, Stripe)"
    echo -e "  3. Restart services: $APP_DIR/restart.sh"
    echo -e "  4. Test full app: curl http://$SERVER_IP"
    echo -e "  5. Test API: curl http://$SERVER_IP/api/health"
    if [ "$DOMAIN" != "your_domain.com" ]; then
        echo -e "  6. Set up SSL: certbot --nginx -d $DOMAIN"
        echo -e "  7. Point DNS to this server: $SERVER_IP"
    fi
    echo ""
    echo -e "${CYAN}🔍 Quick Tests:${NC}"
    echo -e "  curl http://$SERVER_IP/api/health"
    echo -e "  curl http://$SERVER_IP"
    echo ""
    echo -e "${GREEN}🚀 Your complete PoseWeaver application is ready!${NC}"
    echo -e "${GREEN}Both frontend and backend are running and configured.${NC}"
}

# Main installation flow
main() {
    echo -e "${PURPLE}Starting complete PoseWeaver installation...${NC}"
    echo ""
    
    update_system
    install_packages
    create_user
    clone_repository
    setup_backend
    create_env_file
    setup_frontend
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
