#!/bin/bash

# PoseWeaver Backend VPS Deployment Script
# This script automates the deployment process on a fresh Ubuntu 22.04 VPS

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_USER="poseweaver"
APP_DIR="/home/$APP_USER/poseweaver"
REPO_URL="https://github.com/lcanady/poseweaver.git"  # Update this to your actual repository URL
DOMAIN="your_domain.com"  # Update this

echo -e "${GREEN}🚀 Starting PoseWeaver Backend Deployment${NC}"

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

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root (use sudo)"
    exit 1
fi

print_status "Updating system packages..."
apt update && apt upgrade -y
print_success "System packages updated"

print_status "Installing required packages..."
apt install -y python3 python3-pip python3-venv nginx supervisor git ufw curl
print_success "Required packages installed"

print_status "Creating application user..."
if ! id "$APP_USER" &>/dev/null; then
    adduser --disabled-password --gecos "" $APP_USER
    usermod -aG sudo $APP_USER
    print_success "User $APP_USER created"
else
    print_success "User $APP_USER already exists"
fi

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

cd backend

print_status "Setting up Python virtual environment..."
sudo -u $APP_USER python3 -m venv venv
sudo -u $APP_USER ./venv/bin/pip install --upgrade pip
sudo -u $APP_USER ./venv/bin/pip install -r requirements.txt
sudo -u $APP_USER ./venv/bin/pip install gunicorn eventlet
print_success "Python environment configured"

print_status "Creating environment configuration..."
if [ ! -f ".env" ]; then
    sudo -u $APP_USER cp .env.example .env
    print_status "Please edit /home/$APP_USER/poseweaver/backend/.env with your configuration"
    print_status "Required variables: OPENROUTER_API_KEY, MONGODB_URI, SECRET_KEY, JWT_SECRET_KEY, STRIPE_SECRET_KEY"
else
    print_success "Environment file already exists"
fi

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

print_status "Creating Nginx configuration..."
cat > /etc/nginx/sites-available/poseweaver << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    # Proxy to Flask application
    location / {
        # CORS headers for API
        add_header Access-Control-Allow-Origin "https://poseweaver.com" always;
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
        add_header Access-Control-Allow-Origin "https://poseweaver.com" always;
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

print_status "Testing Nginx configuration..."
nginx -t
print_success "Nginx configuration is valid"

print_status "Starting services..."
supervisorctl reread
supervisorctl update
supervisorctl start poseweaver
systemctl restart nginx
print_success "Services started"

print_status "Configuring firewall..."
ufw --force enable
ufw allow OpenSSH
ufw allow 'Nginx Full'
print_success "Firewall configured"

print_status "Creating update script..."
cat > $APP_DIR/update.sh << EOF
#!/bin/bash
cd $APP_DIR
sudo -u $APP_USER git pull origin main
cd backend
sudo -u $APP_USER ./venv/bin/pip install -r requirements.txt
sudo supervisorctl restart poseweaver
echo "Application updated successfully!"
EOF
chmod +x $APP_DIR/update.sh
chown $APP_USER:$APP_USER $APP_DIR/update.sh
print_success "Update script created at $APP_DIR/update.sh"

print_success "🎉 Deployment completed!"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo "1. Edit the environment file: nano $APP_DIR/backend/.env"
echo "2. Add your API keys and database connection string"
echo "3. Restart the application: supervisorctl restart poseweaver"
echo "4. Test the API: curl http://localhost/api/health"
echo "5. Set up SSL certificate: certbot --nginx -d $DOMAIN"
echo ""
echo -e "${YELLOW}📋 Useful Commands:${NC}"
echo "- Check application status: supervisorctl status poseweaver"
echo "- View application logs: tail -f /var/log/poseweaver.log"
echo "- Update application: $APP_DIR/update.sh"
echo "- Restart application: supervisorctl restart poseweaver"
echo ""
echo -e "${GREEN}✅ Your backend will be available at: http://$DOMAIN${NC}"
echo -e "${GREEN}✅ WebSocket endpoint: ws://$DOMAIN/socket.io/${NC}"
