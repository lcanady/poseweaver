#!/bin/bash

# PoseWeaver Local to DigitalOcean Deployment Script
# This script deploys the entire PoseWeaver project from your MacBook to DigitalOcean
# Run from your project root: ./deploy_to_digitalocean.sh

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
VPS_IP=""
VPS_USER="root"
DOMAIN="poseweaver.com"
FRONTEND_URL="https://poseweaver.com"
APP_USER="poseweaver"
APP_DIR="/home/$APP_USER/poseweaver"
LOCAL_PROJECT_DIR="$(pwd)"

echo -e "${PURPLE}🚀 PoseWeaver Local to DigitalOcean Deployment${NC}"
echo -e "${CYAN}Deploying entire project from MacBook to DigitalOcean...${NC}"
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

# Function to gather deployment information
gather_deployment_info() {
    print_status "Gathering deployment information..."
    echo ""
    
    prompt_input "Enter your DigitalOcean VPS IP address" "VPS_IP"
    prompt_input "Enter VPS SSH user" "VPS_USER" "root"
    prompt_input "Enter your domain name (or leave empty for IP-only)" "DOMAIN" "poseweaver.com"
    prompt_input "Enter your frontend URL" "FRONTEND_URL" "https://poseweaver.com"
    
    echo ""
    print_info "Deployment Configuration:"
    print_info "VPS IP: $VPS_IP"
    print_info "SSH User: $VPS_USER"
    print_info "Domain: $DOMAIN"
    print_info "Frontend URL: $FRONTEND_URL"
    print_info "Local Project: $LOCAL_PROJECT_DIR"
    echo ""
    
    read -p "$(echo -e "${CYAN}Continue with deployment? (y/N): ${NC}")" confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_error "Deployment cancelled"
        exit 1
    fi
}

# Function to test VPS connection
test_vps_connection() {
    print_status "Testing VPS connection..."
    if ssh -o ConnectTimeout=10 -o BatchMode=yes $VPS_USER@$VPS_IP exit 2>/dev/null; then
        print_success "VPS connection successful"
    else
        print_error "Cannot connect to VPS. Trying with password authentication..."
        if ! ssh -o ConnectTimeout=10 $VPS_USER@$VPS_IP exit; then
            print_error "VPS connection failed. Please check:"
            print_error "1. VPS IP address is correct: $VPS_IP"
            print_error "2. SSH user is correct: $VPS_USER"
            print_error "3. VPS is running and accessible"
            print_error "4. SSH keys are set up or password authentication works"
            exit 1
        fi
        print_success "VPS connection successful with password"
    fi
}

# Function to prepare local project
prepare_local_project() {
    print_status "Preparing local project for deployment..."
    
    # Ensure we're in the project root
    if [ ! -f "package.json" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
        print_error "Please run this script from the PoseWeaver project root directory"
        exit 1
    fi
    
    # Create deployment package
    print_status "Creating deployment package..."
    
    # Create temporary deployment directory
    DEPLOY_DIR="/tmp/poseweaver-deploy-$(date +%s)"
    mkdir -p $DEPLOY_DIR
    
    # Copy project files (excluding node_modules, .git, etc.)
    rsync -av --exclude='node_modules' \
              --exclude='.git' \
              --exclude='.next' \
              --exclude='__pycache__' \
              --exclude='*.pyc' \
              --exclude='.env' \
              --exclude='.env.local' \
              --exclude='venv' \
              --exclude='dist' \
              --exclude='build' \
              ./ $DEPLOY_DIR/
    
    print_success "Deployment package created at $DEPLOY_DIR"
}

# Function to upload project to VPS
upload_project() {
    print_status "Uploading project to VPS..."
    
    # Create remote directory structure
    ssh $VPS_USER@$VPS_IP "mkdir -p /tmp/poseweaver-upload"
    
    # Upload project files
    rsync -avz --progress $DEPLOY_DIR/ $VPS_USER@$VPS_IP:/tmp/poseweaver-upload/
    
    print_success "Project uploaded to VPS"
}

# Function to create remote installation script
create_remote_installer() {
    print_status "Creating remote installation script..."
    
    # Create the installation script on the VPS
    ssh $VPS_USER@$VPS_IP << EOFREMOTE
cat > /tmp/install_poseweaver.sh << 'EOFINSTALL'
#!/bin/bash

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() { echo -e "\${YELLOW}📋 \$1\${NC}"; }
print_success() { echo -e "\${GREEN}✅ \$1\${NC}"; }
print_error() { echo -e "\${RED}❌ \$1\${NC}"; }

# Configuration
APP_USER="$APP_USER"
APP_DIR="$APP_DIR"
VPS_IP="$VPS_IP"
DOMAIN="$DOMAIN"
FRONTEND_URL="$FRONTEND_URL"

echo "🚀 Installing PoseWeaver on DigitalOcean VPS..."

# Update system
print_status "Updating system..."
apt update && apt upgrade -y

# Install required packages
print_status "Installing packages..."
apt install -y python3 python3-pip python3-venv nginx supervisor git ufw curl htop certbot python3-certbot-nginx

# Install Node.js 18
print_status "Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Create application user
print_status "Creating application user..."
if ! id "\$APP_USER" &>/dev/null; then
    adduser --disabled-password --gecos "" \$APP_USER
    usermod -aG sudo \$APP_USER
fi

# Setup application directory
print_status "Setting up application..."
sudo -u \$APP_USER mkdir -p \$APP_DIR
cp -r /tmp/poseweaver-upload/* \$APP_DIR/
chown -R \$APP_USER:\$APP_USER \$APP_DIR

# Setup backend
print_status "Setting up backend..."
cd \$APP_DIR/backend
sudo -u \$APP_USER python3 -m venv venv
sudo -u \$APP_USER ./venv/bin/pip install --upgrade pip
sudo -u \$APP_USER ./venv/bin/pip install -r requirements.txt

# Create backend environment
if [ ! -f ".env" ]; then
    sudo -u \$APP_USER cp .env.example .env
    sudo -u \$APP_USER sed -i "s|FLASK_ENV=development|FLASK_ENV=production|g" .env
    sudo -u \$APP_USER sed -i "s|FLASK_DEBUG=True|FLASK_DEBUG=False|g" .env
    sudo -u \$APP_USER sed -i "s|FRONTEND_URL=.*|FRONTEND_URL=\$FRONTEND_URL|g" .env
    sudo -u \$APP_USER sed -i "s|PORT=.*|PORT=5001|g" .env
fi

# Setup frontend
print_status "Setting up frontend..."
cd \$APP_DIR/frontend
sudo -u \$APP_USER npm install

# Create frontend environment
sudo -u \$APP_USER cat > .env.local << EOFFRONT
NEXT_PUBLIC_API_URL=http://\$VPS_IP
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key_here
EOFFRONT

# Build frontend
print_status "Building frontend..."
sudo -u \$APP_USER npm run build

# Create supervisor configs
print_status "Creating service configurations..."

# Backend supervisor config
cat > /etc/supervisor/conf.d/poseweaver-backend.conf << EOFBACKEND
[program:poseweaver-backend]
command=\$APP_DIR/backend/venv/bin/python app.py
directory=\$APP_DIR/backend
user=\$APP_USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/poseweaver-backend.log
environment=PATH="\$APP_DIR/backend/venv/bin"
EOFBACKEND

# Frontend supervisor config
cat > /etc/supervisor/conf.d/poseweaver-frontend.conf << EOFFRONTEND
[program:poseweaver-frontend]
command=npm start
directory=\$APP_DIR/frontend
user=\$APP_USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/poseweaver-frontend.log
environment=PATH="/usr/bin:/usr/local/bin",NODE_ENV="production",PORT="3000"
EOFFRONTEND

# Create nginx config
print_status "Configuring Nginx..."
cat > /etc/nginx/sites-available/poseweaver << EOFNGINX
server {
    listen 80;
    server_name \$DOMAIN www.\$DOMAIN \$VPS_IP _;

    # Frontend (Next.js)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\$scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade \\\$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Backend API
    location /api/ {
        add_header Access-Control-Allow-Origin "*" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Origin, X-Requested-With, Content-Type, Accept, Authorization" always;
        add_header Access-Control-Allow-Credentials "true" always;

        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\$scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade \\\$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }

    # WebSocket
    location /socket.io/ {
        add_header Access-Control-Allow-Origin "*" always;
        add_header Access-Control-Allow-Credentials "true" always;

        proxy_pass http://127.0.0.1:5001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \\\$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \\\$host;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\$scheme;
        proxy_read_timeout 86400;
    }
}
EOFNGINX

# Enable nginx site
ln -sf /etc/nginx/sites-available/poseweaver /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Configure firewall
print_status "Configuring firewall..."
ufw --force enable
ufw allow OpenSSH
ufw allow 'Nginx Full'

# Start services
print_status "Starting services..."
nginx -t
supervisorctl reread
supervisorctl update
supervisorctl start poseweaver-backend
supervisorctl start poseweaver-frontend
systemctl restart nginx

# Create management scripts
mkdir -p \$APP_DIR/scripts

cat > \$APP_DIR/scripts/status.sh << 'EOFSTATUS'
#!/bin/bash
echo "🔍 PoseWeaver Status"
echo "==================="
echo ""
echo "📊 Services:"
sudo supervisorctl status poseweaver-backend poseweaver-frontend
echo ""
echo "🌐 Nginx:"
sudo systemctl status nginx --no-pager -l | head -5
echo ""
echo "🔥 Recent Logs:"
echo "Backend:"
sudo tail -5 /var/log/poseweaver-backend.log
echo "Frontend:"
sudo tail -5 /var/log/poseweaver-frontend.log
echo ""
echo "🌍 Health Checks:"
curl -s http://localhost:5001/api/health || echo "❌ Backend API not responding"
curl -s http://localhost:3000 > /dev/null && echo "✅ Frontend responding" || echo "❌ Frontend not responding"
EOFSTATUS

cat > \$APP_DIR/scripts/restart.sh << 'EOFRESTART'
#!/bin/bash
echo "🔄 Restarting PoseWeaver..."
sudo supervisorctl restart poseweaver-backend poseweaver-frontend
sudo systemctl restart nginx
echo "✅ Services restarted!"
EOFRESTART

chmod +x \$APP_DIR/scripts/*.sh
chown -R \$APP_USER:\$APP_USER \$APP_DIR/scripts

print_success "Installation completed!"
echo ""
echo "🌐 Your app: http://\$VPS_IP"
echo "📋 Status: \$APP_DIR/scripts/status.sh"
echo "🔄 Restart: \$APP_DIR/scripts/restart.sh"
echo ""
echo "⚠️  Next steps:"
echo "1. Edit: nano \$APP_DIR/backend/.env"
echo "2. Add API keys (OpenRouter AI, MongoDB, Stripe)"
echo "3. Restart: \$APP_DIR/scripts/restart.sh"

EOFINSTALL

chmod +x /tmp/install_poseweaver.sh
EOFREMOTE

    print_success "Remote installation script created"
}

# Function to run remote installation
run_remote_installation() {
    print_status "Running installation on VPS..."
    
    ssh $VPS_USER@$VPS_IP "sudo /tmp/install_poseweaver.sh"
    
    print_success "Remote installation completed"
}

# Function to test deployment
test_deployment() {
    print_status "Testing deployment..."
    
    # Wait for services to start
    sleep 10
    
    # Test API
    if curl -f -s http://$VPS_IP/api/health > /dev/null; then
        print_success "✅ Backend API is responding"
    else
        print_error "❌ Backend API test failed"
    fi
    
    # Test frontend
    if curl -f -s http://$VPS_IP > /dev/null; then
        print_success "✅ Frontend is responding"
    else
        print_error "❌ Frontend test failed"
    fi
}

# Function to cleanup
cleanup() {
    print_status "Cleaning up temporary files..."
    rm -rf $DEPLOY_DIR
    ssh $VPS_USER@$VPS_IP "rm -rf /tmp/poseweaver-upload /tmp/install_poseweaver.sh"
    print_success "Cleanup completed"
}

# Function to display deployment summary
display_summary() {
    echo ""
    echo -e "${PURPLE}🎉 Deployment Complete!${NC}"
    echo -e "${GREEN}========================${NC}"
    echo ""
    echo -e "${CYAN}🌐 Your PoseWeaver app is live at:${NC}"
    echo -e "  Frontend: http://$VPS_IP"
    echo -e "  Backend API: http://$VPS_IP/api/"
    echo -e "  WebSocket: ws://$VPS_IP/socket.io/"
    echo ""
    echo -e "${CYAN}🔧 Management Commands (run on VPS):${NC}"
    echo -e "  Status: $APP_DIR/scripts/status.sh"
    echo -e "  Restart: $APP_DIR/scripts/restart.sh"
    echo ""
    echo -e "${YELLOW}⚠️  Next Steps:${NC}"
    echo -e "  1. SSH to VPS: ssh $VPS_USER@$VPS_IP"
    echo -e "  2. Edit environment: nano $APP_DIR/backend/.env"
    echo -e "  3. Add your API keys (OpenRouter AI, MongoDB, Stripe)"
    echo -e "  4. Restart services: $APP_DIR/scripts/restart.sh"
    echo ""
    echo -e "${CYAN}🔍 Quick Tests:${NC}"
    echo -e "  curl http://$VPS_IP/api/health"
    echo -e "  curl http://$VPS_IP"
    echo ""
    echo -e "${GREEN}🚀 Your complete PoseWeaver application is deployed!${NC}"
}

# Main deployment flow
main() {
    echo -e "${PURPLE}Starting deployment from MacBook to DigitalOcean...${NC}"
    echo ""
    
    gather_deployment_info
    test_vps_connection
    prepare_local_project
    upload_project
    create_remote_installer
    run_remote_installation
    test_deployment
    cleanup
    display_summary
}

# Handle script interruption
trap 'print_error "Deployment interrupted. You may need to clean up manually."; cleanup; exit 1' INT TERM

# Run main function
main "$@"
